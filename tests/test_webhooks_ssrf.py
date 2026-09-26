"""Outgoing webhooks must not let the server be used to probe its own network (Coil QA #55).

Grok added a webhook pointed at `http://127.0.0.1:8000/health` and hit Test: it was accepted
at save time and `webhooks_out._attempt()`'s `requests.post()` reached it with no address
check, which is server-side request forgery against loopback, container ports, the cloud
metadata address and any other container on the same Docker network. Both the save-time
check in `settings.webhook_new()` and the delivery-time check in `webhooks_out.attempt_delivery()`
must refuse a URL that resolves to a private, loopback, link-local, reserved, multicast or
unspecified address, unless `COIL_WEBHOOKS_ALLOW_PRIVATE` is set. A redirect to one of those
addresses must not be followed either.

Run: .venv/bin/python -m pytest tests/test_webhooks_ssrf.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_webhooks_ssrf.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_webhooks_ssrf")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_webhooks_ssrf")

from tests.helpers import login  # noqa: E402


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
                       "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": ""})


@pytest.fixture(scope="module")
def client(app):
    c = app.test_client()
    c._csrf = login(c)
    return c


def add_webhook(client, url, event="task.completed"):
    return client.post("/settings/webhooks/new", data={"_csrf": client._csrf, "url": url, "events": event})


# ---------------------------------------------------------------- unsafe_url_reason itself

def test_loopback_by_ip_is_unsafe():
    from app.blueprints.webhooks_out import unsafe_url_reason
    assert unsafe_url_reason("http://127.0.0.1:8000/health") is not None


def test_localhost_by_name_is_unsafe():
    from app.blueprints.webhooks_out import unsafe_url_reason
    assert unsafe_url_reason("http://localhost/hook") is not None


def test_link_local_metadata_address_is_unsafe():
    from app.blueprints.webhooks_out import unsafe_url_reason
    assert unsafe_url_reason("http://169.254.169.254/latest/meta-data/") is not None


def test_rfc1918_address_is_unsafe():
    from app.blueprints.webhooks_out import unsafe_url_reason
    assert unsafe_url_reason("http://10.0.0.5/hook") is not None
    assert unsafe_url_reason("http://192.168.1.5/hook") is not None


def test_public_address_is_safe():
    from app.blueprints.webhooks_out import unsafe_url_reason
    assert unsafe_url_reason("http://93.184.216.34/hook") is None


def test_allow_private_switch_lifts_the_refusal():
    from app.blueprints.webhooks_out import unsafe_url_reason
    assert unsafe_url_reason("http://127.0.0.1:8000/health", allow_private=True) is None


# ---------------------------------------------------------------- save time (settings.webhook_new)

def test_save_refuses_loopback_url(client):
    r = add_webhook(client, "http://127.0.0.1:8000/health")
    assert r.status_code == 302
    from app.models import Webhook
    with client.application.app_context():
        assert Webhook.query.filter_by(url="http://127.0.0.1:8000/health").count() == 0


def test_save_refuses_metadata_url(client):
    add_webhook(client, "http://169.254.169.254/latest/meta-data/")
    from app.models import Webhook
    with client.application.app_context():
        assert Webhook.query.filter_by(url="http://169.254.169.254/latest/meta-data/").count() == 0


def test_save_accepts_a_public_url(client):
    r = add_webhook(client, "https://example.com/hook")
    assert r.status_code == 302
    from app.models import Webhook
    with client.application.app_context():
        assert Webhook.query.filter_by(url="https://example.com/hook").count() == 1


# ---------------------------------------------------------------- delivery time (attempt_delivery)

def test_attempt_delivery_refuses_a_loopback_hook(app):
    from app.models import Webhook, WebhookDelivery
    from app.extensions import db
    from app.blueprints.webhooks_out import attempt_delivery
    with app.app_context():
        h = Webhook(url="http://127.0.0.1:8000/health", events="task.completed", is_active=True)
        db.session.add(h)
        db.session.flush()
        d = WebhookDelivery(webhook_id=h.id, event="ping", payload_json="{}", status="pending", attempts=0)
        db.session.add(d)
        db.session.flush()
        ok = attempt_delivery(d, h)
        assert ok is False
        assert d.response_code is None, "no request should have been made at all"
        assert "Refused" in d.last_error
        db.session.rollback()


def test_attempt_delivery_does_not_follow_a_redirect_to_a_private_address(app, monkeypatch):
    from app.models import Webhook, WebhookDelivery
    from app.extensions import db
    from app.blueprints import webhooks_out
    from app.blueprints.webhooks_out import attempt_delivery

    class FakeResponse:
        status_code = 307
        headers = {"Location": "http://127.0.0.1:8000/health"}

    calls = {}

    def fake_post(url, data=None, headers=None, timeout=None, allow_redirects=None):
        calls["allow_redirects"] = allow_redirects
        return FakeResponse()

    monkeypatch.setattr(webhooks_out.requests, "post", fake_post)
    with app.app_context():
        h = Webhook(url="https://example.com/redirector", events="task.completed", is_active=True)
        db.session.add(h)
        db.session.flush()
        d = WebhookDelivery(webhook_id=h.id, event="ping", payload_json="{}", status="pending", attempts=0)
        db.session.add(d)
        db.session.flush()
        ok = attempt_delivery(d, h)
        assert ok is False
        assert calls["allow_redirects"] is False
        assert "redirected to" in d.last_error
        assert "127.0.0.1" in d.last_error
        db.session.rollback()
