"""A user's API token must not outlive their role.

The scope grid on a token is chosen under the role the user held when they made it. If an
owner later demotes or promotes that user, a token minted under the old role has no business
riding along under the new one, so a role change revokes it (checklist item 7: "Downgrade or
deactivate a disposable token owner and confirm the existing token immediately loses access.").
Deactivation already 401s via User.is_active; this covers the role-change half.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_token_revoke_on_role_change.db")
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


def _make_attorney_with_token(app):
    from app.extensions import db
    from app.models import User, Office
    from app.blueprints.api import create_token, reset_rate_limits
    reset_rate_limits()
    with app.app_context():
        office = Office.query.first()
        u = User(name="QA Downgrade Target", email="qa-downgrade@example.com", role="attorney",
                 is_active=True, office_id=office.id if office else None)
        u.set_password("password123")
        db.session.add(u)
        db.session.flush()
        _, raw = create_token(u, "test", ["matters:read"], "full")
        db.session.commit()
        return u.id, raw


def test_role_change_revokes_the_existing_token(app):
    uid, raw = _make_attorney_with_token(app)
    c = app.test_client()
    h = {"Authorization": f"Bearer {raw}"}
    assert c.get("/api/v1/me", headers=h).status_code == 200

    tok = login(c)
    r = c.get(f"/settings/users/{uid}/edit")
    assert r.status_code == 200
    r = c.post(f"/settings/users/{uid}/edit", data={
        "name": "QA Downgrade Target", "email": "qa-downgrade@example.com", "role": "readonly",
        "is_active": "1", "hourly_rate": "0", "_csrf": tok,
    })
    assert r.status_code == 302, r.data[:300]

    other = app.test_client()
    r = other.get("/api/v1/me", headers=h)
    assert r.status_code == 401, r.get_json()
    r = other.get("/api/v1/matters", headers=h)
    assert r.status_code == 401, r.get_json()


def test_editing_without_changing_role_leaves_the_token_alone(app):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token, reset_rate_limits
    reset_rate_limits()
    with app.app_context():
        u = User(name="QA Stable Role", email="qa-stable@example.com", role="attorney", is_active=True)
        u.set_password("password123")
        db.session.add(u)
        db.session.flush()
        uid = u.id
        _, raw = create_token(u, "test", ["matters:read"], "full")
        db.session.commit()

    c = app.test_client()
    tok = login(c)
    r = c.post(f"/settings/users/{uid}/edit", data={
        "name": "QA Stable Role Renamed", "email": "qa-stable@example.com", "role": "attorney",
        "is_active": "1", "hourly_rate": "0", "_csrf": tok,
    })
    assert r.status_code == 302, r.data[:300]

    h = {"Authorization": f"Bearer {raw}"}
    r = c.get("/api/v1/me", headers=h)
    assert r.status_code == 200, r.get_json()
