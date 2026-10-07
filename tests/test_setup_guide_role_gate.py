"""Regression for issue #165: paralegal and readonly could open /setup-guide and its step
pages, including /setup-guide/courtlistener, which prefills the firm's real CourtListener
token in plain text. /settings/integrations already refuses both roles; this wizard reads
and writes the same firm-wide credentials and must be refused the same way.

Root cause: ALWAYS_ALLOW's before_request check matched "/setup" (the pre-login firm
wizard) against any path starting with those five characters, with no separator boundary,
so "/setup-guide" skipped the role gate entirely. Fixed in app/permissions.py: the
boundary check that already protected PREFIX_PERMS now applies to ALWAYS_ALLOW too, and
"/setup-guide" was added to PREFIX_PERMS as owner-only (the "settings" area), same as
/settings/integrations.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_setup_guide_role_gate.db")
DB_URI = f"sqlite:///{DB_PATH}"

from tests.helpers import login  # noqa: E402

ROLE_EMAILS = {"paralegal": "sg165_para@example.test", "readonly": "sg165_ro@example.test"}
TOKEN = "cl-secret-token-1234567890abcdef1234"


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = dict(os.environ, DATABASE_URL=DB_URI)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    a = create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True})
    with a.app_context():
        from app.extensions import db
        from app.models import Firm, User
        for role, email in ROLE_EMAILS.items():
            u = User(email=email, name=role.title() + " User", role=role, initials=role[:2].upper())
            u.set_password("password123")
            db.session.add(u)
        firm = Firm.get()
        firm.courtlistener_token = TOKEN
        db.session.add(firm)
        db.session.commit()
    return a


def _as(app, role):
    c = app.test_client()
    c.tok = login(c, email=ROLE_EMAILS[role])
    return c


@pytest.fixture(params=["paralegal", "readonly"])
def non_owner(app, request):
    return _as(app, request.param)


def test_setup_guide_index_refused(non_owner):
    assert non_owner.get("/setup-guide").status_code == 403


def test_setup_guide_steps_refused_and_token_never_in_the_body(non_owner):
    for key in ("smtp", "courtlistener", "stripe", "imap", "twilio"):
        r = non_owner.get(f"/setup-guide/{key}")
        assert r.status_code == 403, key
        assert TOKEN not in r.get_data(as_text=True)


def test_setup_guide_post_refused(non_owner):
    r = non_owner.post("/setup-guide/courtlistener", data={"COURTLISTENER_TOKEN": "hijacked", "_csrf": non_owner.tok})
    assert r.status_code == 403


def test_owner_is_unaffected(app):
    owner = app.test_client()
    owner.tok = login(owner)
    assert owner.get("/setup-guide").status_code == 200
    r = owner.get("/setup-guide/courtlistener")
    assert r.status_code == 200
    assert TOKEN in r.get_data(as_text=True)


def test_the_pre_login_wizard_route_is_unaffected(app):
    """"/setup" itself (the fresh-install wizard) must stay reachable without a boundary regression."""
    c = app.test_client()
    r = c.get("/setup")
    assert r.status_code in (200, 302)
