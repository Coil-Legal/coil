"""Granular scopes and the two confidentiality modes.

The redaction tests are the important ones. This feature exists so a firm can point an
AI agent at Coil, which means client data leaves the building. If redacted mode ever
leaks a client name or the substance of a matter, a firm that chose it on our word has a
Rule 1.6 problem. So these assert on the actual seeded values, not on flags.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_api_scopes.db")
DB_URI = f"sqlite:///{DB_PATH}"


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


def _token(app, scopes, confidentiality="full"):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token, reset_rate_limits
    reset_rate_limits()
    with app.app_context():
        u = User.query.filter_by(email="owner@example.com").first()
        _, raw = create_token(u, "test", scopes, confidentiality)
        db.session.commit()
    return {"Authorization": f"Bearer {raw}"}


def _seeded(app):
    """The real client name and time narrative in the seeded database."""
    from app.models import Contact, TimeEntry
    with app.app_context():
        c = Contact.query.filter_by(is_client=True).first()
        t = TimeEntry.query.filter(TimeEntry.description != "").first()
        return c.display_name, (t.description if t else None)


# ------------------------------------------------------------------ scopes
def test_a_scope_only_opens_its_own_resource(app):
    c = app.test_client()
    h = _token(app, ["matters:read"])
    assert c.get("/api/v1/matters", headers=h).status_code == 200
    for blocked in ("/api/v1/contacts", "/api/v1/invoices", "/api/v1/tasks", "/api/v1/time"):
        r = c.get(blocked, headers=h)
        assert r.status_code == 403, f"{blocked} should be closed to a matters-only token"
        assert "scope" in r.json["error"]


def test_read_does_not_imply_write(app):
    c = app.test_client()
    h = _token(app, ["time:read"])
    assert c.get("/api/v1/time", headers=h).status_code == 200
    r = c.post("/api/v1/time", headers=h, json={"matter_id": 1, "minutes": 6, "description": "x"})
    assert r.status_code == 403


def test_legacy_tokens_keep_working(app):
    """Tokens issued before granular scopes are running on installs we cannot reach."""
    c = app.test_client()
    ro = _token(app, "read")
    assert c.get("/api/v1/matters", headers=ro).status_code == 200
    assert c.get("/api/v1/contacts", headers=ro).status_code == 200
    assert c.post("/api/v1/time", headers=ro, json={"matter_id": 1, "minutes": 6}).status_code == 403
    rw = _token(app, "read,write")
    assert c.get("/api/v1/matters", headers=rw).status_code == 200


def test_me_reports_the_scopes_an_agent_may_use(app):
    c = app.test_client()
    h = _token(app, ["matters:read", "time:write"])
    body = c.get("/api/v1/me", headers=h).json
    assert set(body["token"]["scopes"]) == {"matters:read", "time:write"}


# --------------------------------------------------------- confidentiality
def test_redacted_mode_withholds_the_client_name(app):
    client_name, _ = _seeded(app)
    c = app.test_client()
    h = _token(app, ["matters:read", "contacts:read"], "redacted")

    body = c.get("/api/v1/matters", headers=h).get_data(as_text=True)
    assert client_name not in body, "a client name reached a redacted token"

    body = c.get("/api/v1/contacts", headers=h).get_data(as_text=True)
    assert client_name not in body, "a contact name reached a redacted token"


def test_redacted_mode_withholds_the_substance_of_the_work(app):
    _, narrative = _seeded(app)
    if not narrative:
        pytest.skip("no seeded time narrative")
    c = app.test_client()
    h = _token(app, ["time:read"], "redacted")
    body = c.get("/api/v1/time", headers=h).get_data(as_text=True)
    assert narrative not in body, "a time narrative reached a redacted token"
    assert "[redacted]" in body, "the field should say it was withheld, not look empty"


def test_redacted_mode_keeps_what_makes_it_useful(app):
    """Structure has to survive or the mode is pointless: an agent still needs to answer
    billing questions and act on a matter number."""
    c = app.test_client()
    h = _token(app, ["matters:read", "time:read", "invoices:read"], "redacted")
    m = c.get("/api/v1/matters", headers=h).json["matters"][0]
    assert m["number"] and m["id"] and m["status"]
    t = c.get("/api/v1/time", headers=h).json["time_entries"]
    if t:
        assert t[0]["minutes"] is not None and t[0]["date"]
    inv = c.get("/api/v1/invoices", headers=h).json["invoices"]
    if inv:
        assert inv[0]["total_cents"] is not None


def test_full_mode_returns_the_real_thing(app):
    client_name, _ = _seeded(app)
    c = app.test_client()
    h = _token(app, ["matters:read"], "full")
    assert client_name in c.get("/api/v1/matters", headers=h).get_data(as_text=True)


def test_me_tells_the_agent_which_mode_it_is_in(app):
    c = app.test_client()
    for mode in ("redacted", "full"):
        body = c.get("/api/v1/me", headers=_token(app, ["matters:read"], mode)).json
        assert body["token"]["confidentiality"] == mode
        assert body["token"]["note"]


def test_new_tokens_are_redacted_unless_asked_otherwise(app):
    from app.blueprints.api import create_token
    from app.extensions import db
    from app.models import User
    with app.app_context():
        u = User.query.filter_by(email="owner@example.com").first()
        t, _ = create_token(u, "default", "read")
        db.session.commit()
        assert t.confidentiality == "redacted"


def test_an_unknown_mode_falls_back_to_redacted(app):
    from app.blueprints.api import create_token
    from app.extensions import db
    from app.models import User
    with app.app_context():
        u = User.query.filter_by(email="owner@example.com").first()
        t, _ = create_token(u, "junk", "read", "anything-goes")
        db.session.commit()
        assert t.confidentiality == "redacted"


# --------------------------------------------------- widened API surface
def test_documents_never_return_file_contents(app):
    """A document is the most concentrated client confidence in the system. The API
    returns metadata so an agent can see what exists, and never the bytes or the text."""
    c = app.test_client()
    h = _token(app, ["documents:read"], "full")
    r = c.get("/api/v1/documents", headers=h)
    assert r.status_code == 200
    for d in r.json["documents"]:
        assert "extracted_text" not in d
        assert "path" not in d, "the filesystem path must never leave the server"


def test_notes_and_calendar_writes_need_their_own_scope(app):
    c = app.test_client()
    h = _token(app, ["notes:read", "calendar:read"], "full")
    assert c.post("/api/v1/notes", headers=h, json={"matter_id": 1, "body": "x"}).status_code == 403
    assert c.post("/api/v1/calendar", headers=h,
                  json={"title": "x", "starts_at": "2026-09-08T10:00:00"}).status_code == 403


def test_a_note_can_be_added_and_is_attributed(app):
    from app.models import Note, User
    c = app.test_client()
    h = _token(app, ["notes:read", "notes:write"], "full")
    r = c.post("/api/v1/notes", headers=h, json={"matter_id": 1, "body": "Called the client back."})
    assert r.status_code == 201, r.get_data(as_text=True)
    with app.app_context():
        n = Note.query.get(r.json["note"]["id"])
        owner = User.query.filter_by(email="owner@example.com").first()
        assert n.body == "Called the client back."
        assert n.user_id == owner.id, "a note must be attributed to the token's owner"


def test_a_note_on_a_matter_that_does_not_exist_is_refused(app):
    c = app.test_client()
    h = _token(app, ["notes:write"], "full")
    assert c.post("/api/v1/notes", headers=h, json={"matter_id": 99999, "body": "x"}).status_code == 404


def test_calendar_rejects_a_bad_timestamp_rather_than_guessing(app):
    c = app.test_client()
    h = _token(app, ["calendar:write"], "full")
    r = c.post("/api/v1/calendar", headers=h, json={"title": "Call", "starts_at": "next tuesday"})
    assert r.status_code == 400
    assert "ISO 8601" in r.json["error"]
