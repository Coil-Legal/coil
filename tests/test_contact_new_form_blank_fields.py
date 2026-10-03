"""QA issue #92: the new-contact form rendered the literal text "None" in first name,
last name, email and phone when those fields were untouched, because `Contact()` is
unflushed at render time and SQLAlchemy only applies the column's `default=""` at INSERT,
not at construction. An untouched field then posted back the string "None", which got
saved as the contact's actual value, and a contact with phone "None" is truthy so the
message thread's "Send text" button was not disabled for a contact with no real phone.

Run: .venv/bin/python -m pytest tests/test_contact_new_form_blank_fields.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_contact_new_form_blank_fields.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_contact_new_form_blank_fields")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_contact_new_form_blank_fields")

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
    c._csrf = login(c)
    return c


def test_new_contact_form_has_no_literal_none_in_its_fields(client):
    page = client.get("/contacts/new").data.decode()
    assert "None" not in page, page


def test_untouched_new_contact_fields_save_blank_not_the_text_none(client):
    r = client.post("/contacts/new", data={
        "_csrf": client._csrf, "kind": "person", "first_name": "QA Blank 20261002",
        "last_name": "", "company_name": "", "email": "", "phone": "", "address": "",
        "tags": "", "aliases": "", "notes": "", "language": "", "ledes_client_id": "",
    })
    assert r.status_code == 302, r.data[:300]
    contact_id = int(r.headers["Location"].rstrip("/").rsplit("/", 1)[-1])

    from app.models import Contact
    with client.application.app_context():
        from app.extensions import db
        c = db.session.get(Contact, contact_id)
        assert c.last_name == "", c.last_name
        assert c.email == "", c.email
        assert c.phone == "", c.phone

    thread = client.get(f"/messages/{contact_id}").data.decode()
    assert 'disabled' in thread[thread.index("Send text") - 80:thread.index("Send text")], thread
