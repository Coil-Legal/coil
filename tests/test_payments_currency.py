"""A manual payment recorded against a non-USD invoice must be reported in that invoice's
currency, not defaulted to USD. Companion to tests/test_credit_notes.py, which covers the
same class of bug in the credit-note flow.

Run: .venv/bin/python -m pytest tests/test_payments_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_payments_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_payments_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_payments_currency")

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


def post(c, path, data):
    return c.post(path, data=dict(data, _csrf=c._csrf), follow_redirects=True)


_seq = iter(range(1, 9999))


@pytest.fixture
def sent_eur_invoice(app):
    """A sent EUR 500 invoice with nothing paid on it."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"PCE-{next(_seq):04d}", matter_id=m.id,
                      client_id=m.client_id, status="sent", issued_on=date.today(), tax_cents=0,
                      currency="EUR")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=50000, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id


def test_over_balance_payment_flash_uses_the_invoice_currency(app, client, sent_eur_invoice):
    """A check for more than a EUR invoice's balance must be refused in EUR, not $."""
    r = post(client, "/payments/record", {"invoice_id": sent_eur_invoice, "amount": "600.00",
                                          "method": "check", "received_on": date.today().isoformat()})
    body = r.data.decode()
    assert "more than the invoice balance of €500.00" in body
    assert "invoice balance of $500.00" not in body


def test_recorded_payment_flash_uses_the_invoice_currency(app, client, sent_eur_invoice):
    """A valid check payment on a EUR invoice must confirm in EUR, not $."""
    r = post(client, "/payments/record", {"invoice_id": sent_eur_invoice, "amount": "500.00",
                                          "method": "check", "received_on": date.today().isoformat()})
    body = r.data.decode()
    assert "Recorded €500.00 check payment" in body


def test_paid_invoice_over_balance_flash_uses_the_invoice_currency(app, client, sent_eur_invoice):
    """The exact issue #53 repro: a 0.01 check against an already-paid EUR invoice must be
    refused in EUR (balance 0.00), not with a dollar sign."""
    post(client, "/payments/record", {"invoice_id": sent_eur_invoice, "amount": "500.00",
                                       "method": "check", "received_on": date.today().isoformat()})
    r = post(client, "/payments/record", {"invoice_id": sent_eur_invoice, "amount": "0.01",
                                          "method": "check", "received_on": date.today().isoformat()})
    body = r.data.decode()
    assert "more than the invoice balance of €0.00" in body
    assert "invoice balance of $0.00" not in body
