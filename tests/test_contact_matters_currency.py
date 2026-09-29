"""QA issue #74: same defect class as #60-#73, at the contact detail page's Matters table
(/contacts/<id>). It used the plain `money` filter (always a dollar sign) for a matter's
Unbilled cell instead of `cur(m.currency_code)`, so a EUR matter's unbilled figure showed
with a bare dollar sign even though the matter's own page and the matters list (fixed in
#73) both show it in euros.

Run: .venv/bin/python -m pytest tests/test_contact_matters_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_contact_matters_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_contact_matters_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_contact_matters_currency")

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


@pytest.fixture(scope="module")
def eur_matter_with_unbilled(app):
    """A EUR matter with 200.00 unbilled (2h at 100/hr, its own currency), distinguishable
    from any USD figure already in the seed data for the same contact."""
    from app.extensions import db
    from app.models import Matter, TimeEntry, User
    with app.app_context():
        u = User.query.first()
        usd = Matter.query.filter_by(number="M-1001").first()
        client_id = usd.client_id
        eur = Matter(number="CONTACT-EUR-1", client_id=client_id, name="Euro contact matter",
                    billing_type="hourly", currency="EUR", status="open")
        db.session.add(eur)
        db.session.flush()
        db.session.add(TimeEntry(matter_id=eur.id, user_id=u.id, date=date.today(), minutes=120,
                                 rate_cents=10000, billable=True))
        db.session.commit()
        return client_id


def test_contact_detail_shows_unbilled_in_the_matters_own_currency(client, eur_matter_with_unbilled):
    page = client.get(f"/contacts/{eur_matter_with_unbilled}").data.decode()
    assert "€200.00" in page, page
