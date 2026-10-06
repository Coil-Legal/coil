"""Issue #137 (QA2): a second logout on an already-closed session sends the browser to
`/login?next=/logout`. Signing in from that page then followed `next` straight to `/logout`
with a GET, and `/logout` only accepts POST, so the real result was a bare 405 page instead
of the dashboard, even though the sign-in itself worked.

Own SQLite file, own UPLOAD_DIR and PDF_DIR. Never touches data/practice.db.
Run: .venv/bin/python -m pytest tests/test_login_next_safe.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_login_next_safe.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_login_next_safe")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_login_next_safe")

from tests.helpers import _tok, login  # noqa: E402


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


def test_second_logout_sends_login_to_dashboard_not_back_to_logout(app):
    """Reproduces case 6025: a second POST /logout on an already-closed session (same
    browser, so its CSRF token is still the one logout() left in place) falls through to
    login_required's redirect, /login?next=/logout. Signing in from there must land on the
    dashboard, not loop back into a GET on the POST-only /logout route."""
    c = app.test_client()
    tok = login(c)

    r = c.post("/logout", data={"_csrf": tok})
    assert r.status_code == 302
    assert r.headers["Location"] == "/login"

    r = c.post("/logout", data={"_csrf": tok})
    assert r.status_code == 302
    assert r.headers["Location"] == "/login?next=/logout"

    r = c.get("/login?next=/logout")
    tok2 = _tok(r.data)
    r = c.post("/login?next=/logout", data={"email": "owner@example.com", "password": "password123", "_csrf": tok2})
    assert r.status_code == 302
    assert r.headers["Location"] != "/logout"

    r = c.get(r.headers["Location"])
    assert r.status_code == 200


def test_login_next_still_honors_a_real_get_route(app):
    c = app.test_client()
    r = c.get("/login?next=/settings")
    tok = _tok(r.data)
    r = c.post("/login?next=/settings", data={"email": "owner@example.com", "password": "password123", "_csrf": tok})
    assert r.status_code == 302
    assert r.headers["Location"] == "/settings"
