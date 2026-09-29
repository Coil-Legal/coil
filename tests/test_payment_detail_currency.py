"""QA issue #81: same defect class as #79/#80. The payment detail page's heading
("Payment of $0.50") and its Amount row both used the plain `money` filter (always a
dollar sign) for `pay.amount_cents` on a EUR payment (INV-1045's payment 11), instead
of the invoice's own currency.

Run: .venv/bin/python -m pytest tests/test_payment_detail_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_payment_detail_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_payment_detail_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_payment_detail_currency")

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
def eur_payment_id(app, client):
    """A sent EUR 1.00 invoice with a EUR 0.50 payment against it, matching the QA
    fixture (INV-1045, a EUR 0.50 payment, "payment 11")."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, Payment
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number="PAY-DETAIL-EUR-1", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0, currency="EUR")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=100, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        inv_id = inv.id
    client.post("/payments/record", data={"invoice_id": inv_id, "amount": "0.50", "method": "check",
                                          "received_on": date.today().isoformat(), "_csrf": client._csrf},
               follow_redirects=True)
    with app.app_context():
        pay = Payment.query.filter_by(invoice_id=inv_id).first()
        return pay.id


def test_payment_detail_uses_the_invoices_own_currency(client, eur_payment_id):
    page = client.get(f"/payments/{eur_payment_id}").data.decode()
    assert "Payment of €0.50" in page, page
    assert "Payment of $0.50" not in page, page
    assert "<dt>Amount</dt><dd>€0.50</dd>" in page, page
