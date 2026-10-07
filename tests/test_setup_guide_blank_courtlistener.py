"""Regression for issue #167: a blank submit on /setup-guide/courtlistener erased the
stored Research token and still flashed "Saved. Case law research is set up."

Root cause: every other step in app/blueprints/setupguide.py routes its fields through
save_firm_values(), which only overwrites a field when the submitted value is non-blank
(blank keeps what is stored, typing the word none clears it). The courtlistener branch
was separate code that assigned the raw form value straight to Firm.courtlistener_token
with no blank guard, and its flash was unconditional. Fixed by giving courtlistener the
same blank-means-keep / none-means-clear rule, and by only flashing "is set up" when the
step is actually configured afterward.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_setup_guide_blank_courtlistener.db")
DB_URI = f"sqlite:///{DB_PATH}"

from tests.helpers import login  # noqa: E402

TOKEN = "cl-secret-token-abcdef0123456789abcd"


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


@pytest.fixture
def client(app):
    c = app.test_client()
    login(c)
    return c


def test_blank_submit_keeps_the_stored_token(client, app):
    from app.models import Firm
    tok = login(client)
    client.post("/setup-guide/courtlistener", data={"COURTLISTENER_TOKEN": TOKEN, "action": "save", "_csrf": tok})
    r = client.post("/setup-guide/courtlistener", data={"COURTLISTENER_TOKEN": "", "action": "save", "_csrf": tok})
    with app.app_context():
        assert Firm.get().courtlistener_token == TOKEN
    page = client.get(r.headers["Location"])
    body = page.get_data(as_text=True)
    assert "is set up" in body
    assert "not set up" not in body


def test_typing_none_clears_the_token(client, app):
    from app.models import Firm
    tok = login(client)
    client.post("/setup-guide/courtlistener", data={"COURTLISTENER_TOKEN": TOKEN, "action": "save", "_csrf": tok})
    r = client.post("/setup-guide/courtlistener", data={"COURTLISTENER_TOKEN": "none", "action": "save", "_csrf": tok})
    with app.app_context():
        assert Firm.get().courtlistener_token == ""
    page = client.get(r.headers["Location"])
    assert "is not set up yet" in page.get_data(as_text=True)


def test_a_real_value_still_saves(client, app):
    from app.models import Firm
    tok = login(client)
    r = client.post("/setup-guide/courtlistener", data={"COURTLISTENER_TOKEN": TOKEN, "action": "save", "_csrf": tok})
    with app.app_context():
        assert Firm.get().courtlistener_token == TOKEN
    page = client.get(r.headers["Location"])
    body = page.get_data(as_text=True)
    assert "is set up" in body
    assert "not set up" not in body
