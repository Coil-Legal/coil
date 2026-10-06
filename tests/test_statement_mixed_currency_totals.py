"""Issue #125: a client statement with invoices in two currencies summed their cents together
and labelled the sum with one currency's $ symbol (EUR 275.00 + GBP 275.00 shown as "$550.00").
Same bug class as #60/#61/#62/#63, applied via fmt_money_by_currency/curmix everywhere else;
statements never got the fix. Covers the summary cards, the per-matter subtotal row and the
all-matters totals row, which is what the issue's own retest steps check.

Run: .venv/bin/python -m pytest tests/test_statement_mixed_currency_totals.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_statement_mixed_currency_totals.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_statement_mixed_currency_totals")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_statement_mixed_currency_totals")

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
def mixed_currency_client(app):
    """Issue #125's own numbers: one EUR invoice and one GBP invoice, 27500 cents each, same
    client, same matter, both sent and unpaid. A raw sum would be 55000 cents, shown as $550.00."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        eur = Invoice(number="SMC-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="EUR")
        db.session.add(eur)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur.id, description="Services", amount_cents=27500, kind="fee"))
        db.session.flush()
        eur.recalc()

        gbp = Invoice(number="SMC-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="GBP")
        db.session.add(gbp)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=gbp.id, description="Services", amount_cents=27500, kind="fee"))
        db.session.flush()
        gbp.recalc()
        db.session.commit()
        return m.client_id


def test_statement_cards_split_currencies_instead_of_summing_them(client, mixed_currency_client):
    """The Activity table's chronological running balance (st.closing, tested in
    test_statement_credits.py as a plain int) still blends currencies, unchanged by this fix;
    only the cards, subtotal row and all-matters row that #125 actually reported are checked here."""
    page = client.get(f"/statements/{mixed_currency_client}").data.decode()
    assert page.count("€275.00 + £275.00") >= 3, page  # Invoiced, Balance due cards + all-matters row


def test_statement_subtotal_row_splits_currencies_instead_of_summing_them(client, mixed_currency_client):
    page = client.get(f"/statements/{mixed_currency_client}").data.decode()
    assert "Subtotal" in page
    assert "€275.00 + £275.00" in page, page


def test_statement_mixed_banner_still_shown(client, mixed_currency_client):
    page = client.get(f"/statements/{mixed_currency_client}").data.decode()
    assert "This client has invoices in more than one currency." in page
