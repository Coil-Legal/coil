"""QA issue #73: same defect class as #60-#71, at the matters list (/matters) and the
dashboard's "Recent matters" widget. Both used the plain `money` filter (always a dollar
sign) for a matter's Unbilled and Trust cells instead of `cur(m.currency_code)`, so a EUR
matter's figures showed with a bare dollar sign.

Run: .venv/bin/python -m pytest tests/test_matters_list_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_matters_list_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_matters_list_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_matters_list_currency")

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
def eur_matter_with_unbilled_and_trust(app):
    """A EUR matter with 200.00 unbilled (2h at 100/hr, its own currency) and a 50.00 trust
    deposit, both distinguishable from any USD figure already in the seed data."""
    from app.extensions import db
    from app.models import Matter, TimeEntry, TrustTransaction, User
    with app.app_context():
        u = User.query.first()
        usd = Matter.query.filter_by(number="M-1001").first()
        eur = Matter(number="LIST-EUR-1", client_id=usd.client_id, name="Euro list matter",
                    billing_type="hourly", currency="EUR", status="open")
        db.session.add(eur)
        db.session.flush()
        db.session.add(TimeEntry(matter_id=eur.id, user_id=u.id, date=date.today(), minutes=120,
                                 rate_cents=10000, billable=True))
        db.session.add(TrustTransaction(client_id=eur.client_id, matter_id=eur.id, date=date.today(),
                                        type="deposit", amount_cents=5000, created_by_id=u.id))
        db.session.commit()
        return eur.number, eur.id


def test_matters_list_shows_unbilled_and_trust_in_the_matters_own_currency(client, eur_matter_with_unbilled_and_trust):
    page = client.get("/matters").data.decode()
    assert "€200.00" in page, page
    assert "€50.00" in page, page


def test_dashboard_recent_matters_widget_shows_unbilled_and_trust_in_the_matters_own_currency(
        client, eur_matter_with_unbilled_and_trust):
    page = client.get("/").data.decode()
    assert "€200.00" in page, page
    assert "€50.00" in page, page
