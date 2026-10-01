"""Issue #85: editing a user to use another user's email must flash, not 500.

`_fill_user` sets `u.email` on the already-session-tracked user before checking for a
duplicate. The duplicate-check query used to autoflush that pending change first, so the
unique constraint on `users.email` raised an uncaught IntegrityError instead of returning
the "Another user already has that email." flash.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_user_edit_duplicate_email.db")
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


def _make_user(app, name, email):
    from app.extensions import db
    from app.models import User
    with app.app_context():
        u = User(name=name, email=email, role="paralegal", is_active=True)
        u.set_password("password123")
        db.session.add(u)
        db.session.commit()
        return u.id


def test_editing_a_user_to_a_duplicate_email_flashes_instead_of_500(app):
    owner_email = "owner@example.com"
    uid = _make_user(app, "QA Duplicate Email Target", "qa-dup-target@example.com")

    c = app.test_client()
    tok = login(c)
    r = c.post(f"/settings/users/{uid}/edit", data={
        "name": "QA Duplicate Email Target", "email": owner_email, "role": "paralegal",
        "is_active": "1", "hourly_rate": "0", "_csrf": tok,
    })
    assert r.status_code == 200, r.data[:300]
    assert b"Another user already has that email" in r.data

    from app.extensions import db
    from app.models import User
    with app.app_context():
        u = db.session.get(User, uid)
        assert u.email == "qa-dup-target@example.com"
        assert u.name == "QA Duplicate Email Target"
