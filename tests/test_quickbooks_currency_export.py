"""QA issue #59: the QuickBooks CSV exports have no currency column and were writing a euro
amount as if it were the same kind of number as a dollar amount, with no label and no refusal.
QuickBooks' own CSV import reads ItemAmount/Amount as a plain number, so that euro row would be
misread as that many USD. The fix leaves non-USD invoices and payments out of these exports and
flashes which ones, pointing at the full data dumps (which do carry a Currency column) instead.

Run: .venv/bin/python -m pytest tests/test_quickbooks_currency_export.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_quickbooks_currency_export.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_quickbooks_currency_export")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_quickbooks_currency_export")

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


_seq = iter(range(1, 9999))


@pytest.fixture
def usd_and_eur_invoices_with_payments(app):
    """One USD and one EUR invoice, each sent and each with a payment recorded against it."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Payment, Matter
    with app.app_context():
        m = Matter.query.first()
        usd_inv = Invoice(number=f"QBC-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                          status="sent", issued_on=date.today(), tax_cents=0, currency="USD")
        db.session.add(usd_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=usd_inv.id, description="Services", amount_cents=10000, kind="fee"))
        db.session.flush()
        usd_inv.recalc()

        eur_inv = Invoice(number=f"QBC-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                          status="sent", issued_on=date.today(), tax_cents=0, currency="EUR")
        db.session.add(eur_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur_inv.id, description="Services", amount_cents=20000, kind="fee"))
        db.session.flush()
        eur_inv.recalc()

        db.session.add(Payment(invoice_id=usd_inv.id, matter_id=m.id, client_id=m.client_id,
                               amount_cents=5000, method="check", received_on=date.today()))
        db.session.add(Payment(invoice_id=eur_inv.id, matter_id=m.id, client_id=m.client_id,
                               amount_cents=7500, method="check", received_on=date.today()))
        db.session.commit()
        return usd_inv.number, eur_inv.number


def test_quickbooks_invoices_csv_leaves_out_the_eur_invoice_and_says_so(client, usd_and_eur_invoices_with_payments):
    usd_number, eur_number = usd_and_eur_invoices_with_payments
    r = client.get("/exports/quickbooks/invoices.csv")
    body = r.data.decode("utf-8-sig")
    assert usd_number in body
    assert eur_number not in body, "a EUR invoice must not appear in a USD-only QuickBooks export"
    # the CSV response itself carries the flash (message_flashed fires before the body is built)
    page = client.get("/exports").data.decode()
    assert eur_number in page and "non-USD" in page and "USD" in page


def test_quickbooks_payments_csv_leaves_out_the_eur_payment_and_says_so(client, usd_and_eur_invoices_with_payments):
    usd_number, eur_number = usd_and_eur_invoices_with_payments
    r = client.get("/exports/quickbooks/payments.csv")
    body = r.data.decode("utf-8-sig")
    assert usd_number in body
    assert eur_number not in body, "a payment against a EUR invoice must not appear in a USD-only QuickBooks export"
    page = client.get("/exports").data.decode()
    assert eur_number in page and "non-USD" in page
