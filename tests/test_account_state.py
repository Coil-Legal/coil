"""Hosted account lifecycle (C08): active, suspended, closed.

A suspended firm signs in, reads everything and can export, but nothing it does changes a
record; its clients see a polite "temporarily unavailable" page instead of a pay or sign
form; providers are told to retry. A closed firm gets sign in, sign out and the owner's
export page, and nothing else. The owner's /settings/export must stay reachable in every
state, because a paused or closed firm must always be able to take its data.

/settings/export is built separately. When this build does not have it, the test app gets
a stub route at that path so the guard is exercised on the real path.

Run: .venv/bin/python -m pytest tests/test_account_state.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_account_state.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_account_state")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_account_state")

from tests.helpers import login, _tok  # noqa: E402

PAUSED = "This account is paused. You can view and export your data. Contact hello@coil.legal to reactivate."


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
    a = create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
                    "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": "",
                    "COIL_READY_CACHE_SECONDS": 0})
    if "/settings/export" not in {r.rule for r in a.url_map.iter_rules()}:
        from app.helpers import owner_required

        @owner_required
        def _stub_export():
            from flask import request
            return f"export stub {request.method}", 200
        a.add_url_rule("/settings/export", "stub_settings_export", _stub_export, methods=["GET", "POST"])
    with a.app_context():
        from app.extensions import db
        from app.models import User
        if not User.query.filter_by(email="attorney.state@example.com").first():
            u = User(email="attorney.state@example.com", name="State Attorney", role="attorney")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
    return a


@pytest.fixture(autouse=True)
def state(app):
    def set_state(value, retain=""):
        app.config["COIL_ACCOUNT_STATE"] = value
        app.config["COIL_ACCOUNT_CLOSED_RETAIN_UNTIL"] = retain
    yield set_state
    set_state("active")


@pytest.fixture
def owner(app):
    c = app.test_client()
    c._csrf = login(c)
    return c


@pytest.fixture
def tokens(app):
    """Public tokens of one seeded invoice and engagement, for the client-facing pages."""
    from app.models import Invoice, Engagement
    with app.app_context():
        inv = Invoice.query.filter(Invoice.public_token != None).first()  # noqa: E711
        eng = Engagement.query.filter(Engagement.token != None).first() if hasattr(Engagement, "token") else None  # noqa: E711
        return {"invoice": inv.public_token if inv else "missing",
                "engagement": getattr(eng, "token", None) or "missing"}


def _contact_count(app):
    from app.models import Contact
    with app.app_context():
        return Contact.query.count()


# --- active ---------------------------------------------------------------------------
def test_active_is_unchanged(app, owner, state):
    state("active")
    r = owner.get("/")
    assert r.status_code == 200
    assert b"account-banner" not in r.data
    before = _contact_count(app)
    r = owner.post("/contacts/new", data={"_csrf": owner._csrf, "kind": "person", "first_name": "QA",
                                          "last_name": "State Active"})
    assert r.status_code in (200, 302)
    assert _contact_count(app) == before + 1


def test_unknown_value_is_treated_as_suspended(app, owner, state):
    state("suspendd")
    r = owner.post("/contacts/new", data={"_csrf": owner._csrf, "first_name": "QA", "last_name": "Typo"})
    assert r.status_code == 423


# --- suspended ------------------------------------------------------------------------
def test_suspended_reads_work_and_show_the_banner(app, owner, state):
    state("suspended")
    for path in ("/", "/contacts", "/matters", "/invoices"):
        r = owner.get(path)
        assert r.status_code == 200, path
        assert PAUSED.encode() in r.data, path


def test_suspended_refuses_every_write_with_423(app, owner, state):
    state("suspended")
    before = _contact_count(app)
    r = owner.post("/contacts/new", data={"_csrf": owner._csrf, "first_name": "QA", "last_name": "Paused"})
    assert r.status_code == 423
    assert PAUSED.encode() in r.data
    assert _contact_count(app) == before
    for method in ("put", "patch", "delete"):
        r = getattr(owner, method)("/contacts/1", headers={"X-CSRF-Token": owner._csrf})
        assert r.status_code == 423, method


def test_suspended_still_allows_sign_in_sign_out_and_own_password(app, state):
    state("suspended")
    c = app.test_client()
    tok = login(c)              # login POST works
    from app.models import User
    with app.app_context():
        me = User.query.filter_by(email="owner@example.com").first().id
        other = User.query.filter_by(email="attorney.state@example.com").first().id
    r = c.get(f"/settings/users/{me}/edit")
    tok = _tok(r.data) or tok
    r = c.post(f"/settings/users/{me}/edit", data={"_csrf": tok, "name": "Demo Owner", "email": "owner@example.com",
                                                   "role": "owner", "password": ""})
    assert r.status_code in (200, 302), "own account page must stay usable to rotate a password"
    assert b"<h1>This account is paused</h1>" not in r.data
    r = c.post(f"/settings/users/{other}/edit", data={"_csrf": tok, "name": "Changed"})
    assert r.status_code == 423, "editing someone else is a write like any other"
    r = c.post("/logout", data={"_csrf": tok})
    assert r.status_code in (200, 302)


def test_suspended_export_page_reachable_for_owner(app, owner, state):
    state("suspended")
    assert owner.get("/settings/export").status_code == 200
    assert owner.post("/settings/export", data={"_csrf": owner._csrf}).status_code == 200


def test_suspended_client_pages_are_temporarily_unavailable(app, state, tokens):
    state("suspended")
    c = app.test_client()
    for path in (f"/p/{tokens['invoice']}", f"/pay/{tokens['invoice']}?method=card", f"/sign/{tokens['engagement']}",
                 "/sign/doc/abc", "/portal/login", "/intake/form", "/pay/card/abc"):
        r = c.get(path)
        assert r.status_code == 503, path
        assert b"Temporarily unavailable" in r.data, path
        assert b"account-banner" not in r.data, path
        assert r.headers.get("Retry-After")
    r = c.post("/intake/submit", data={"name": "QA Lead"})
    assert r.status_code == 503
    r = c.post(f"/sign/{tokens['engagement']}", data={"signer_name": "QA", "agree": "1"})
    assert r.status_code == 503


def test_suspended_webhooks_get_503_so_providers_retry(app, state):
    state("suspended")
    c = app.test_client()
    for path in ("/webhooks/stripe", "/webhooks/twilio", "/webhooks/twilio/status"):
        r = c.post(path, data=b"{}", content_type="application/json")
        assert r.status_code == 503, path
        assert r.headers.get("Retry-After")


def test_suspended_tracking_pixel_records_nothing(app, state, tokens):
    state("suspended")
    r = app.test_client().get(f"/track/invoice/{tokens['invoice']}.gif")
    assert r.status_code == 204


def test_suspended_api_reads_pass_writes_get_json_423(app, state):
    state("suspended")
    c = app.test_client()
    r = c.get("/api/v1/matters")
    assert r.status_code != 423      # reaches the API, which asks for a token
    r = c.post("/api/v1/matters", json={"name": "QA"})
    assert r.status_code == 423
    assert r.get_json()["error"] == "account_suspended"


def test_health_endpoints_work_in_every_state(app, state):
    for value in ("suspended", "closed"):
        state(value)
        c = app.test_client()
        assert c.get("/health").status_code == 200
        assert c.get("/health/ready").status_code in (200, 503)
        assert c.get("/health/ready").get_json()["status"] in ("ready", "degraded")
        assert c.get("/static/app.css").status_code == 200


# --- closed ---------------------------------------------------------------------------
def test_closed_shows_closed_page_everywhere_else(app, owner, state):
    state("closed", "2027-01-09")
    for path in ("/", "/contacts", "/matters", "/invoices", "/exports", "/settings"):
        r = owner.get(path)
        assert r.status_code == 423, path
        assert b"This account is closed. The owner can still sign in and download all firm data until January 9, 2027." in r.data
    r = owner.post("/contacts/new", data={"_csrf": owner._csrf, "first_name": "QA"})
    assert r.status_code == 423


def test_closed_without_retention_date_omits_it(app, owner, state):
    state("closed")
    r = owner.get("/")
    assert b"download all firm data." in r.data
    assert b" until " not in r.data.split(b"download all firm data")[1][:20]


def test_closed_allows_login_logout_and_owner_export(app, state):
    state("closed", "2027-01-09")
    c = app.test_client()
    assert c.get("/login").status_code == 200
    tok = login(c)
    assert c.get("/settings/export").status_code == 200
    assert c.post("/settings/export", data={"_csrf": tok}).status_code == 200
    r = c.post("/logout", data={"_csrf": tok})
    assert r.status_code in (200, 302)


def test_closed_export_stays_owner_only(app, state):
    state("closed")
    c = app.test_client()
    login(c, email="attorney.state@example.com")
    assert c.get("/settings/export").status_code == 403


def test_closed_logged_out_visitor_gets_closed_page_with_sign_in(app, state):
    state("closed")
    r = app.test_client().get("/")
    assert r.status_code == 423
    assert b'href="/login"' in r.data


def test_closed_client_pages_webhooks_and_api(app, state, tokens):
    state("closed")
    c = app.test_client()
    r = c.get(f"/p/{tokens['invoice']}")
    assert r.status_code == 410
    assert b"No longer available" in r.data
    assert c.post("/webhooks/stripe", data=b"{}").status_code == 503
    assert c.get("/api/v1/matters").status_code == 423
    assert c.get("/calendar").status_code == 423


def test_closed_state_is_case_insensitive(app, owner, state):
    state(" Closed ")
    assert owner.get("/").status_code == 423


# --- cron -----------------------------------------------------------------------------
@pytest.mark.parametrize("value", ["suspended", "closed"])
def test_cron_jobs_skip_but_backup_does_not(value):
    from app.account_state import cli_skip_reason, PAUSED_CLI_SKIPS
    config = {"COIL_ACCOUNT_STATE": value}
    for cmd in ("agenda", "reminders", "interest", "emailin", "sequences", "webhooks", "monthly_invoicing",
                "case_audit", "payment_plans", "voice_reminders"):
        assert cmd in PAUSED_CLI_SKIPS
        assert "skipped" in cli_skip_reason(cmd, config)
    assert cli_skip_reason("backup", config) is None
    assert cli_skip_reason("export_firm", config) is None, "an export must run while paused or closed"
    assert cli_skip_reason("agenda", {"COIL_ACCOUNT_STATE": "active"}) is None


def test_suspended_cli_run_sends_nothing_and_records_a_heartbeat(tmp_path):
    db = tmp_path / "practice.db"
    beats = tmp_path / "beats.json"
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", COIL_ACCOUNT_STATE="suspended",
               COIL_HEARTBEAT_FILE=str(beats), SMTP_HOST="")
    subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], check=True, cwd=ROOT, env=env,
                   capture_output=True)
    r = subprocess.run([sys.executable, "-m", "app.cli", "reminders"], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert "reminders: skipped, the account is suspended" in r.stdout
    assert "invoice," not in r.stdout     # the normal "reminders: N invoice, ..." line never printed
    import json
    entry = json.loads(beats.read_text())["jobs"]["reminders"]
    assert entry["last_success"] and "skipped" in entry["last_note"]
