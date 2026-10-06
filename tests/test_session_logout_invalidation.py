"""Issue #101 (QA2): a copied session cookie stayed valid after the owning browser logged out.

Flask's session is a signed, client-side cookie with no server-side store, so logout could
only tell the logging-out browser to drop its own cookie. Any other copy of that same signed
value (XSS, a shared machine, a synced browser profile) kept working until it expired on its
own. Fixed by stamping a session version into the cookie at login and bumping the user's
version on logout, so every outstanding copy stops matching.

Own SQLite file, own UPLOAD_DIR and PDF_DIR. Never touches data/practice.db.
Run: .venv/bin/python -m pytest tests/test_session_logout_invalidation.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_session_logout_invalidation.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_session_logout_invalidation")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_session_logout_invalidation")

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


def test_copied_session_cookie_dies_on_logout(app):
    client_a = app.test_client()
    tok = login(client_a)

    client_b = app.test_client()
    copied = client_a.get_cookie("session")
    assert copied is not None
    client_b.set_cookie("session", copied.value)

    # Both clients are authenticated with the same copied cookie value.
    assert client_b.get("/settings/users").status_code == 200

    r = client_a.post("/logout", data={"_csrf": tok})
    assert r.status_code == 302

    # The second client's copy of the old cookie must now be refused.
    r = client_b.get("/settings/users")
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_logout_writes_an_audit_entry(app):
    """Issue #127 (QA2): logout bumped session_version (the #101 fix above) but wrote no
    audit row, so /settings/audit never showed when a session ended, only when it began."""
    client_a = app.test_client()
    tok = login(client_a)
    r = client_a.post("/logout", data={"_csrf": tok})
    assert r.status_code == 302

    client_c = app.test_client()
    login(client_c)
    page = client_c.get("/settings/audit").get_data(as_text=True)
    assert "logout" in page
    assert 'value="logout"' in page  # the action-filter dropdown now offers it
