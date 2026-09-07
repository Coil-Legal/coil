"""In-app feedback: what it sends, what it refuses, and what it never leaks.

The point of the last one: this posts a firm's data to a third party (us). If it ever
starts carrying matter or client content, that is a confidentiality problem for every
firm running Coil, so the payload is asserted field by field.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_feedback.db")
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
    return create_app({
        "SQLALCHEMY_DATABASE_URI": DB_URI,
        "TESTING": True,
        "COIL_VERSION": "v9.9.9",
        "COIL_COMMIT": "cafebabe1234",
        "COIL_CHANNEL": "stable",
        "BASE_URL": "https://coil.testfirm.com",
    })


@pytest.fixture
def client(app):
    c = app.test_client()
    login(c)
    return c


def _capture(monkeypatch):
    """Intercept the outbound call and hand back whatever was going to be sent."""
    sent = {}
    import app.blueprints.feedback as fb

    def fake(payload):
        sent.update(payload)
        return True, ""

    monkeypatch.setattr(fb, "send_feedback", fake)
    return sent


def test_the_button_is_on_every_page(client):
    r = client.get("/")
    assert b"Send feedback" in r.data


def test_form_submits_and_carries_the_account_and_build(client, app, monkeypatch):
    sent = _capture(monkeypatch)
    tok = login(client)
    r = client.post("/feedback", data={
        "kind": "bug", "message": "Trust export drops the last row.",
        "from": "/accounting/trust", "_csrf": tok,
    })
    # Sends them back to the page they were on when they hit the button.
    assert r.status_code == 302, r.data[:200]
    assert r.headers["Location"] == "/accounting/trust"
    assert sent["message"] == "Trust export drops the last row."
    assert sent["kind"] == "bug"
    assert sent["page"] == "/accounting/trust"
    assert sent["version"] == "v9.9.9"
    assert sent["commit"] == "cafebabe1234"
    assert sent["channel"] == "stable"
    assert sent["base_url"] == "https://coil.testfirm.com"
    # tied to the account and the firm, which is the whole ask
    assert sent["email"]
    assert sent["name"]
    assert sent["firm"]


def test_payload_carries_nothing_but_the_declared_fields(client, app, monkeypatch):
    """The page promises an exact list. If a field is added, this test must be the thing
    that notices, not a firm reading their own matter names in our inbox."""
    sent = _capture(monkeypatch)
    tok = login(client)
    client.post("/feedback", data={"kind": "missing", "message": "hi", "_csrf": tok})
    assert set(sent) == {
        "firm", "name", "email", "kind", "message", "page",
        "version", "commit", "channel", "base_url", "hosting",
    }


def test_an_empty_message_is_refused_and_nothing_is_sent(client, app, monkeypatch):
    sent = _capture(monkeypatch)
    tok = login(client)
    r = client.post("/feedback", data={"kind": "bug", "message": "   ", "_csrf": tok})
    assert r.status_code == 200
    assert sent == {}


def test_an_unknown_kind_falls_back_rather_than_being_stored_raw(client, app, monkeypatch):
    sent = _capture(monkeypatch)
    tok = login(client)
    client.post("/feedback", data={"kind": "<script>", "message": "x", "_csrf": tok})
    assert sent["kind"] == "bug"


def test_logged_out_visitors_cannot_reach_it(app):
    c = app.test_client()
    r = c.get("/feedback")
    assert r.status_code in (302, 401), "feedback must sit behind the login"


def test_a_failure_to_reach_coil_legal_tells_the_user_where_else_to_send_it(client, monkeypatch):
    import app.blueprints.feedback as fb
    monkeypatch.setattr(fb, "send_feedback", lambda p: (False, "Could not reach coil.legal from this server."))
    tok = login(client)
    r = client.post("/feedback", data={"kind": "bug", "message": "x", "_csrf": tok})
    assert b"Could not reach coil.legal" in r.data


def test_it_can_be_turned_off_entirely(app):
    from app import create_app
    off = create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True, "FEEDBACK_ENABLED": "0"})
    c = off.test_client()
    login(c)
    assert b"Send feedback" not in c.get("/").data
    r = c.get("/feedback", follow_redirects=False)
    assert r.status_code == 302, "the route must refuse when the feature is off"


def test_the_request_identifies_itself_as_coil(app, monkeypatch):
    """Without a User-Agent, urllib sends Python-urllib/x.y, which the WAF in front of
    coil.legal blocks: every send came back 403 until this was set."""
    import app.blueprints.feedback as fb
    seen = {}

    class FakeResp:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def fake_urlopen(req, timeout=None):
        seen["agent"] = req.get_header("User-agent")
        seen["url"] = req.full_url
        return FakeResp()

    monkeypatch.setattr(fb.urllib.request, "urlopen", fake_urlopen)
    with app.app_context():
        ok, _ = fb.send_feedback({"message": "x"})
    assert ok
    assert seen["agent"].startswith("Coil/"), seen["agent"]
    assert "coil.legal" in seen["agent"]
