"""An SMTP failure (bad credentials, a relay down) must not become a 500.

Found by the QA loop on testfirm: Save and send on an engagement letter returned
HTTP 500 because the firm's configured SMTP credentials were rejected and
smtplib's SMTPAuthenticationError propagated straight out of send_email,
unhandled, through send_engagement, through the route. Every other caller of
send_email (invoices, statements, trust requests, signature requests, portal
links) had the same exposure; only messages.py had wrapped its own call in a
try/except. The fix belongs in send_email itself, not in each of the ~20 callers.

Run: .venv/bin/python -m pytest tests/test_mail_smtp_failure.py -q
"""
import os
import smtplib
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_mail_smtp_failure.db")
DB_URI = f"sqlite:///{DB_PATH}"
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_mail_smtp_failure")

from tests.helpers import login  # noqa: E402


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = dict(os.environ, DATABASE_URL=DB_URI, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    a = create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "PDF_DIR": PDF_DIR, "TESTING": True,
                    "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "",
                    "SMTP_HOST": "smtp.example.test", "SMTP_PORT": 587,
                    "SMTP_USER": "firm@example.test", "SMTP_PASS": "wrong",
                    "MAIL_FROM": "firm@example.test"})
    yield a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def staff(client):
    tok = login(client)
    return client, tok


class _BoomSMTP:
    """Stands in for smtplib.SMTP: connects fine, then rejects login like a real relay would."""

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def starttls(self):
        pass

    def login(self, user, pw):
        raise smtplib.SMTPAuthenticationError(535, b"5.7.8 Username and Password not accepted")


def test_send_email_reports_failure_instead_of_raising(app, monkeypatch):
    monkeypatch.setattr(smtplib, "SMTP", _BoomSMTP)
    from app.services.mail import send_email
    with app.test_request_context():
        ok = send_email("client@example.test", "Subject", "<p>Body</p>")
    assert ok is False


def test_engagement_save_and_send_survives_a_bad_relay(app, staff, monkeypatch):
    """The exact QA repro: compose a letter, click Save and send, relay rejects the login."""
    monkeypatch.setattr(smtplib, "SMTP", _BoomSMTP)
    client, tok = staff
    from app.models import Matter, Engagement, EngagementEvent
    from app.extensions import db
    with app.app_context():
        m = Matter.query.filter(Matter.client.has(email="maria@example.com")).first() or Matter.query.first()
        mid = m.id

    table_html = ("<p>Intro</p><table><tr><th>Item</th><th>Amount</th></tr>"
                  "<tr><td>Retainer</td><td>$2,000</td></tr></table><p>Thanks.</p>")
    r = client.post("/engagements/new", data={"_csrf": tok, "matter_id": mid, "action": "send",
                                              "scope": "Test scope", "body_html": table_html},
                    follow_redirects=True)
    assert r.status_code == 200, "an SMTP auth failure is not a 500"
    body = r.data.decode()
    assert "could not be delivered" in body

    with app.app_context():
        e = Engagement.query.filter_by(matter_id=mid).order_by(Engagement.id.desc()).first()
        assert e.status == "sent"
        assert e.sent_to
        ev = EngagementEvent.query.filter_by(engagement_id=e.id, event="sent").first()
        assert "delivery failed" in ev.detail
