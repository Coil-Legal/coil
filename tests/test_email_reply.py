"""Answering a filed client email, by email, from inside the matter.

Mail filing pulls a client's email into the matter. Until this existed, the only way
to answer it was the attorney's own mail client, which put the answer somewhere Coil
could not see. A file holding one side of a conversation is worse than no file, and
it is the side the attorney gets asked about later.

Found by the QA loop on the live instance: "Email reply from Coil: not testable on
that thread (Send a text / Reply in portal only; no email composer)."

Run: .venv/bin/python -m pytest tests/test_email_reply.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_email_reply.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_email_reply")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_email_reply")

from tests.helpers import login  # noqa: E402

INBOUND_ID = "<qa-inbound-9f21@example.test>"


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(PDF_DIR, ignore_errors=True)
    env = dict(os.environ, DATABASE_URL=DB_URI, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="", SMTP_HOST="")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
                       "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "",
                       "SMTP_HOST": "", "MAIL_FROM": "firm@example.test"})


@pytest.fixture(scope="module")
def client(app):
    c = app.test_client()
    c._csrf = login(c)
    return c


def post(c, path, data):
    return c.post(path, data=dict(data, _csrf=c._csrf), follow_redirects=True)


@pytest.fixture(scope="module")
def contact_with_inbound(app):
    """A client who emailed us, filed to a matter, exactly as app.cli emailin leaves it."""
    from app.extensions import db
    from app.models import Contact, Matter, Message
    with app.app_context():
        c = Contact.query.filter(Contact.email.isnot(None), Contact.email != "").first()
        assert c is not None, "seed data should have a contact with an email"
        m = Matter.query.filter_by(client_id=c.id).first()
        db.session.add(Message(
            contact_id=c.id, matter_id=m.id if m else None, direction="in", channel="email",
            to_addr="firm@example.test", from_addr=c.email, subject="Question about my deposition",
            body="Do I need to bring anything on Thursday?", message_id=INBOUND_ID, status="filed"))
        db.session.commit()
        return c.id, (m.id if m else None), c.email


def test_the_thread_offers_an_email_reply(client, contact_with_inbound):
    cid, _, email = contact_with_inbound
    page = client.get(f"/messages/{cid}").data.decode()
    assert "Reply by email" in page, "a filed email must be answerable by email"
    assert '/messages/email-send' in page
    assert email in page, "the attorney should see where it is going"


def test_the_subject_is_prefilled_as_a_reply(client, contact_with_inbound):
    cid, _, _ = contact_with_inbound
    page = client.get(f"/messages/{cid}").data.decode()
    assert "Re: Question about my deposition" in page, "do not make them retype the subject"


def test_sending_records_the_reply_on_the_thread(app, client, contact_with_inbound):
    cid, mid, email = contact_with_inbound
    r = post(client, "/messages/email-send",
             {"contact_id": cid, "matter_id": mid or "", "subject": "Re: Question about my deposition",
              "body": "Bring photo ID and the letter we sent. Nothing else."})
    assert r.status_code == 200
    from app.models import Message
    with app.app_context():
        m = Message.query.filter_by(contact_id=cid, channel="email", direction="out").first()
        assert m is not None, "the answer must live in the file, not only in the mail server"
        assert m.to_addr == email
        assert m.subject == "Re: Question about my deposition"
        assert "photo ID" in m.body
        assert m.matter_id == mid, "it belongs to the matter it answers"


def test_the_reply_threads_onto_the_client_last_email(app, client, contact_with_inbound, monkeypatch):
    """Without In-Reply-To the client gets a loose email they have to reconcile by hand."""
    cid, mid, _ = contact_with_inbound
    seen = {}

    def fake_send(to, subject, html, text=None, attachments=None, reply_to=None, headers=None):
        seen.update(to=to, subject=subject, headers=headers or {}, text=text)
        return True

    monkeypatch.setattr("app.blueprints.messages.send_email", fake_send)
    post(client, "/messages/email-send", {"contact_id": cid, "matter_id": mid or "", "subject": "",
                                          "body": "Threading check."})
    assert seen["headers"].get("In-Reply-To") == INBOUND_ID
    assert seen["headers"].get("References") == INBOUND_ID
    assert seen["subject"].lower().startswith("re:"), "an empty subject becomes a reply subject"


def test_an_empty_body_is_refused(app, client, contact_with_inbound):
    cid, _, _ = contact_with_inbound
    from app.models import Message
    with app.app_context():
        before = Message.query.filter_by(channel="email", direction="out").count()
    r = post(client, "/messages/email-send", {"contact_id": cid, "body": "   "})
    assert "Type a message first" in r.data.decode()
    with app.app_context():
        assert Message.query.filter_by(channel="email", direction="out").count() == before


def test_a_contact_with_no_email_cannot_be_emailed(app, client):
    from app.extensions import db
    from app.models import Contact
    with app.app_context():
        c = Contact(first_name="QA", last_name="NoEmail", email="")
        db.session.add(c)
        db.session.commit()
        cid = c.id
    page = client.get(f"/messages/{cid}").data.decode()
    assert "No email address on file" in page
    r = post(client, "/messages/email-send", {"contact_id": cid, "body": "hello"})
    assert "has no email address on file" in r.data.decode()


def test_a_relay_failure_keeps_the_words_and_says_so(app, client, contact_with_inbound, monkeypatch):
    """SMTP dying must not silently swallow what the attorney wrote."""
    cid, mid, _ = contact_with_inbound

    def boom(*a, **k):
        raise OSError("relay refused")

    monkeypatch.setattr("app.blueprints.messages.send_email", boom)
    r = post(client, "/messages/email-send",
             {"contact_id": cid, "matter_id": mid or "", "subject": "Held", "body": "Words worth keeping."})
    assert r.status_code == 200, "a relay problem is not a 500"
    assert "not sent" in r.data.decode().lower()
    from app.models import Message
    with app.app_context():
        m = Message.query.filter_by(subject="Held", channel="email", direction="out").first()
        assert m is not None and m.status == "not_sent"
        assert "Words worth keeping" in m.body
