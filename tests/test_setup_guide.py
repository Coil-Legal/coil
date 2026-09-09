"""The setup wizard: every step skippable, nothing lost, and the firm's own credentials
actually take effect afterwards.

The point of the wizard is that a firm on an instance somebody else runs can switch on
payments, texting and email filing without a shell. So the tests check that what is
entered is what the service later reads, not just that the form saved.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_setup_guide.db")
DB_URI = f"sqlite:///{DB_PATH}"

from tests.helpers import login  # noqa: E402


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = dict(os.environ, DATABASE_URL=DB_URI)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True})


@pytest.fixture(autouse=True)
def clean_env(app, monkeypatch):
    for k in ("SMTP_HOST", "SMTP_USER", "SMTP_PASS", "MAIL_FROM", "STRIPE_SECRET_KEY",
              "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER", "IMAP_HOST"):
        monkeypatch.delenv(k, raising=False)
        monkeypatch.setitem(app.config, k, "")


@pytest.fixture
def client(app):
    c = app.test_client()
    login(c)
    return c


def test_the_guide_lists_every_step(client):
    body = client.get("/setup-guide").get_data(as_text=True)
    for title in ("Sending email", "Case law research", "Getting paid online",
                  "Filing email to matters", "Texting clients"):
        assert title in body


def test_every_step_page_renders(client):
    for key in ("smtp", "courtlistener", "stripe", "imap", "twilio"):
        r = client.get(f"/setup-guide/{key}")
        assert r.status_code == 200, key
        body = r.get_data(as_text=True)
        assert "Do you need it?" in body, f"{key} should say whether it is needed"
        assert "Skip for now" in body, f"{key} must be skippable"


def test_skipping_is_recorded_and_moves_on(client, app):
    from app.models import Firm
    tok = login(client)
    r = client.post("/setup-guide/twilio", data={"action": "skip", "_csrf": tok})
    assert r.status_code == 302
    with app.app_context():
        assert json.loads(Firm.get().setup_json)["twilio"] == "skipped"


def test_a_skipped_step_can_still_be_done_later(client, app):
    from app.integrations import setting
    tok = login(client)
    client.post("/setup-guide/twilio", data={"action": "skip", "_csrf": tok})
    client.post("/setup-guide/twilio", data={
        "TWILIO_ACCOUNT_SID": "AC123", "TWILIO_AUTH_TOKEN": "tok", "TWILIO_FROM_NUMBER": "+15125550100",
        "action": "save", "_csrf": tok})
    with app.app_context():
        assert setting("TWILIO_ACCOUNT_SID") == "AC123"


def test_what_the_firm_enters_is_what_the_service_uses(client, app):
    """The whole point: a hosted firm has no .env, so this has to reach the code that sends."""
    from app.services import sms
    tok = login(client)
    client.post("/setup-guide/twilio", data={
        "TWILIO_ACCOUNT_SID": "AC999", "TWILIO_AUTH_TOKEN": "secret", "TWILIO_FROM_NUMBER": "+15125550111",
        "action": "save", "_csrf": tok})
    with app.app_context():
        assert sms.configured() is True


def test_a_blank_box_keeps_what_was_saved(client, app):
    """A half-filled form must not wipe a working setting."""
    from app.integrations import setting
    tok = login(client)
    client.post("/setup-guide/smtp", data={
        "SMTP_HOST": "smtp.example.test", "SMTP_USER": "a@b.test", "SMTP_PASS": "pw",
        "MAIL_FROM": "a@b.test", "SMTP_PORT": "587", "action": "save", "_csrf": tok})
    client.post("/setup-guide/smtp", data={"SMTP_HOST": "", "action": "save", "_csrf": tok})
    with app.app_context():
        assert setting("SMTP_HOST") == "smtp.example.test"


def test_typing_none_clears_a_value(client, app):
    from app.integrations import setting
    tok = login(client)
    client.post("/setup-guide/imap", data={"IMAP_HOST": "imap.example.test", "action": "save", "_csrf": tok})
    client.post("/setup-guide/imap", data={"IMAP_HOST": "none", "action": "save", "_csrf": tok})
    with app.app_context():
        assert setting("IMAP_HOST") == ""


def test_the_environment_still_wins(client, app, monkeypatch):
    """An operator who pinned a value made a decision the wizard must not undo."""
    from app.integrations import setting
    tok = login(client)
    client.post("/setup-guide/smtp", data={"SMTP_HOST": "firm.example.test", "action": "save", "_csrf": tok})
    monkeypatch.setenv("SMTP_HOST", "operator.example.test")
    with app.app_context():
        assert setting("SMTP_HOST") == "operator.example.test"


def test_only_allowlisted_settings_can_be_written(app):
    """This blob is filled from a web form. SECRET_KEY must never be settable that way."""
    from app.integrations import save_firm_values, firm_values
    with app.app_context():
        save_firm_values({"SECRET_KEY": "hijacked", "DATABASE_URL": "sqlite:///evil.db",
                          "SMTP_USER": "fine@example.test"})
        v = firm_values()
        assert "SECRET_KEY" not in v and "DATABASE_URL" not in v
        assert v["SMTP_USER"] == "fine@example.test"


def test_logged_out_visitors_cannot_reach_the_wizard(app):
    c = app.test_client()
    assert c.get("/setup-guide").status_code in (302, 401)
    assert c.post("/setup-guide/stripe", data={"action": "skip"}).status_code in (302, 400, 401)


# --------------------------------------------- a summary is not thrown away by accident
def test_saving_a_deposition_with_an_empty_box_keeps_the_summary(app):
    """form.get(k, default) only falls back when the key is ABSENT, and the textarea is
    always submitted. An empty box therefore wiped a summary that cost a model call and
    that an attorney may have spent time editing, with no warning and no undo."""
    from app.extensions import db
    from app.models import DepositionSummary, Matter
    from tests.helpers import login
    c = app.test_client()
    tok = login(c)
    with app.app_context():
        m = Matter.query.first()
        dep = DepositionSummary(matter_id=m.id, deponent="A Witness", summary_text="Worth keeping.")
        db.session.add(dep); db.session.commit()
        dep_id = dep.id

    r = c.post(f"/discovery/depositions/{dep_id}/save",
               data={"summary_text": "", "deponent": "A Witness", "_csrf": tok})
    assert r.status_code == 302
    with app.app_context():
        assert db.session.get(DepositionSummary, dep_id).summary_text == "Worth keeping."


def test_clearing_a_deposition_summary_on_purpose_works(app):
    from app.extensions import db
    from app.models import DepositionSummary, Matter
    from tests.helpers import login
    c = app.test_client()
    tok = login(c)
    with app.app_context():
        m = Matter.query.first()
        dep = DepositionSummary(matter_id=m.id, deponent="B Witness", summary_text="Remove me.")
        db.session.add(dep); db.session.commit()
        dep_id = dep.id

    c.post(f"/discovery/depositions/{dep_id}/save",
           data={"summary_text": "", "clear_summary": "1", "deponent": "B Witness", "_csrf": tok})
    with app.app_context():
        assert db.session.get(DepositionSummary, dep_id).summary_text == ""
