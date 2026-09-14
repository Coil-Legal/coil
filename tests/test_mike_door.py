"""The optional door to Mike: a nav link that exists only when a firm has set one up.

Mike is an add-on a firm may run beside Coil (docs/MIKE.md). Coil must not depend on it,
must not show a link to nowhere, and must not turn a stray setting into a dangerous href.

Run: .venv/bin/python -m pytest tests/test_mike_door.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_mike_door.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_mike_door")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_mike_door")

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
    login(c)
    return c


def _set_firm(app, value):
    from app.extensions import db
    from app.integrations import save_firm_values
    with app.app_context():
        save_firm_values({"MIKE_URL": value})
        db.session.commit()


def test_no_link_when_nothing_is_set(app, client, monkeypatch):
    monkeypatch.delenv("MIKE_URL", raising=False)
    _set_firm(app, "")
    assert b"AI workbench" not in client.get("/").data


def test_env_setting_shows_the_door(app, client, monkeypatch):
    monkeypatch.setenv("MIKE_URL", "https://ai.example-firm.test")
    body = client.get("/").data
    assert b"AI workbench" in body
    assert b'href="https://ai.example-firm.test"' in body
    assert b'rel="noopener"' in body, "it opens another site in a new tab"


def test_hosted_firm_can_set_it_without_env(app, client, monkeypatch):
    monkeypatch.delenv("MIKE_URL", raising=False)
    _set_firm(app, "https://mike.hosted-firm.test")
    body = client.get("/").data
    assert b'href="https://mike.hosted-firm.test"' in body
    _set_firm(app, "")


def test_a_non_http_value_never_becomes_a_link(app, client, monkeypatch):
    """A setting is text a person typed. It must not be able to become javascript: in the nav."""
    monkeypatch.setenv("MIKE_URL", "javascript:alert(1)")
    body = client.get("/").data
    assert b"AI workbench" not in body
    assert b"javascript:alert" not in body


def test_integrations_page_explains_mike_in_both_states(app, client, monkeypatch):
    monkeypatch.delenv("MIKE_URL", raising=False)
    _set_firm(app, "")
    body = client.get("/settings/integrations").data
    assert b"AI workbench (Mike)" in body
    assert b"MIKE_URL is empty" in body
    assert b"Coil does not need Mike to work" in body

    monkeypatch.setenv("MIKE_URL", "https://ai.example-firm.test")
    body = client.get("/settings/integrations").data
    assert b"Linked in the navigation to https://ai.example-firm.test" in body
    assert b"Open Mike" in body
