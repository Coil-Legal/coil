"""When Twilio refuses, say what Twilio said.

A bare "error:400" is not something a person at the keyboard can act on: a fictional
555 number, the firm's own number as the destination, and an unfunded account all
look identical. Twilio explains itself in the response body; these tests hold us to
passing that explanation through to the screen instead of swallowing it.

Both real cases here were found on the live QA instance: Twilio 21211 (the seeded
555-0100 contact) and 21266 (sending to the account's own From number).

Run: .venv/bin/python -m pytest tests/test_provider_errors.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_provider_errors.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_provider_errors")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_provider_errors")

from tests.helpers import login  # noqa: E402

TWILIO = {"TWILIO_ACCOUNT_SID": "ACtest", "TWILIO_AUTH_TOKEN": "tok", "TWILIO_FROM_NUMBER": "+15550001111"}


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


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
    cfg = {"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
           "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": ""}
    cfg.update(TWILIO)
    return create_app(cfg)


@pytest.fixture(scope="module")
def client(app):
    c = app.test_client()
    c._csrf = login(c)
    return c


def post(c, path, data, **kw):
    """Every write goes through the real CSRF gate, like a browser."""
    return c.post(path, data=dict(data, _csrf=c._csrf), follow_redirects=True, **kw)


def _contact_with_phone(app, phone):
    from app.extensions import db
    from app.models import Contact
    with app.app_context():
        c = Contact.query.filter(Contact.phone.isnot(None), Contact.phone != "").first()
        if c is None:
            c = Contact(first_name="QA", last_name="Phone")
            db.session.add(c)
        c.phone = phone
        db.session.commit()
        return c.id


def test_a_fictional_number_is_explained_not_numbered(app, client, monkeypatch):
    """Twilio 21211. The seeded 555-0100 contact produced exactly this on the QA box."""
    cid = _contact_with_phone(app, "555-0100")
    body = {"code": 21211, "message": "The 'To' number 555-0100 is not a valid phone number.",
            "more_info": "https://www.twilio.com/docs/errors/21211", "status": 400}
    monkeypatch.setattr("app.services.sms.requests.post",
                        lambda *a, **k: FakeResponse(400, body))
    r = post(client, "/messages/send", {"contact_id": cid, "body": "hello"})
    assert r.status_code == 200
    page = r.data.decode()
    assert "not a valid phone number" in page, "the person must be told the number is the problem"
    assert "error:400" not in page, "a bare HTTP code is not an explanation"


def test_sending_to_our_own_number_is_explained(app, client, monkeypatch):
    """Twilio 21266. Easy to hit while testing, impossible to diagnose from 'error:400'."""
    cid = _contact_with_phone(app, "+15550001111")
    body = {"code": 21266, "message": "'To' and 'From' number cannot be the same.", "status": 400}
    monkeypatch.setattr("app.services.sms.requests.post",
                        lambda *a, **k: FakeResponse(400, body))
    r = post(client, "/messages/send", {"contact_id": cid, "body": "hello"})
    assert "cannot be the same" in r.data.decode()


def test_the_message_is_still_stored_when_twilio_refuses(app, client, monkeypatch):
    """A refused send is a record too: the attempt happened and the file should show it."""
    cid = _contact_with_phone(app, "555-0100")
    body = {"code": 21211, "message": "The 'To' number is not a valid phone number.", "status": 400}
    monkeypatch.setattr("app.services.sms.requests.post",
                        lambda *a, **k: FakeResponse(400, body))
    post(client, "/messages/send", {"contact_id": cid, "body": "stored anyway"})
    from app.models import Message
    with app.app_context():
        m = Message.query.filter_by(contact_id=cid, body="stored anyway").first()
        assert m is not None, "the attempt must survive as a record"
        assert m.status == "error:21211"
        assert len(m.status) <= 30, "Message.status is a 30 character column"


def test_a_refusal_with_no_json_still_says_something(app, client, monkeypatch):
    """A proxy or an outage can return HTML. Say what we know rather than crashing."""
    cid = _contact_with_phone(app, "555-0100")
    monkeypatch.setattr("app.services.sms.requests.post",
                        lambda *a, **k: FakeResponse(502, None))
    r = post(client, "/messages/send", {"contact_id": cid, "body": "gateway"})
    assert r.status_code == 200
    assert "HTTP 502" in r.data.decode()


def test_success_is_unchanged(app, client, monkeypatch):
    cid = _contact_with_phone(app, "+15125550143")
    monkeypatch.setattr("app.services.sms.requests.post",
                        lambda *a, **k: FakeResponse(201, {"sid": "SM123", "status": "queued"}))
    r = post(client, "/messages/send", {"contact_id": cid, "body": "all good"})
    assert r.status_code == 200
    assert "would not send" not in r.data.decode()
    from app.models import Message
    with app.app_context():
        m = Message.query.filter_by(contact_id=cid, body="all good").first()
        assert m.provider_id == "SM123" and m.status == "queued"


def test_a_refused_test_call_explains_itself(app, client, monkeypatch):
    """The voice test call had the same bare-code problem as SMS."""
    body = {"code": 21215, "message": "Account not authorized to call +1809 numbers.", "status": 400}
    monkeypatch.setattr("app.blueprints.voice.requests.post",
                        lambda *a, **k: FakeResponse(400, body))
    r = post(client, "/voice/reminders/test", {"to": "8095551234"})
    assert "not authorized" in r.data.decode()
