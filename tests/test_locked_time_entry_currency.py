"""QA issue #82: same defect class as #52-#81, at the locked (invoiced) time entry and
expense edit pages (/time/<id>/edit, /time/expenses/<id>/edit). Both used the plain
`money` filter (always a dollar sign) for the Rate/Amount fields instead of
`cur(entry.matter.currency_code)`/`cur(expense.matter.currency_code)`, so a EUR matter's
locked entry showed its rate and amount with a bare dollar sign even though the invoice
it is locked to is in euros.

Run: .venv/bin/python -m pytest tests/test_locked_time_entry_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_locked_time_entry_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_locked_time_entry_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_locked_time_entry_currency")

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
def eur_locked_entries(app):
    """A EUR matter with a locked (invoiced) time entry and a locked expense, each with a
    round, distinctive amount so a bare '$' vs '€' is unambiguous."""
    from app.extensions import db
    from app.models import Matter, TimeEntry, Expense, Invoice, User
    with app.app_context():
        u = User.query.first()
        usd = Matter.query.filter_by(number="M-1001").first()
        eur = Matter(number="LOCKED-EUR-1", client_id=usd.client_id, name="Euro locked matter",
                    billing_type="hourly", currency="EUR", status="open")
        db.session.add(eur)
        db.session.flush()
        inv = Invoice(number="LOCKED-EUR-INV-1", matter_id=eur.id, client_id=eur.client_id,
                     kind="hourly", status="sent", currency="EUR", total_cents=30000)
        db.session.add(inv)
        db.session.flush()
        entry = TimeEntry(matter_id=eur.id, user_id=u.id, date=date.today(), minutes=120,
                          rate_cents=10000, billable=True, invoice_id=inv.id)
        expense = Expense(matter_id=eur.id, user_id=u.id, date=date.today(), amount_cents=10000,
                          billable=True, invoice_id=inv.id, description="Filing fee")
        db.session.add_all([entry, expense])
        db.session.commit()
        return entry.id, expense.id


def test_locked_time_entry_shows_rate_and_amount_in_the_matters_own_currency(client, eur_locked_entries):
    entry_id, _ = eur_locked_entries
    page = client.get(f"/time/{entry_id}/edit").data.decode()
    assert "€100.00/hr" in page, page
    assert "€200.00" in page, page
    assert "$100.00" not in page and "$200.00" not in page, page


def test_locked_expense_shows_amount_in_the_matters_own_currency(client, eur_locked_entries):
    _, expense_id = eur_locked_entries
    page = client.get(f"/time/expenses/{expense_id}/edit").data.decode()
    assert "€100.00" in page, page
    assert "$100.00" not in page, page
