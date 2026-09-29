"""QA issue #75: same defect class as #60-#74, on the invoice detail page's "Reduce the
balance" form. The Amount field's placeholder used the plain `money` filter (always a
dollar sign) for `inv.balance_cents` instead of `cur(cc)`, so a GBP invoice's PS0.50 balance
showed a placeholder of "$0.50".

Run: .venv/bin/python -m pytest tests/test_credit_note_placeholder_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_credit_note_placeholder_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_credit_note_placeholder_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_credit_note_placeholder_currency")

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
def gbp_invoice_with_balance(app):
    """A sent GBP invoice with a PS0.50 balance and nothing paid, matching the QA fixture
    (INV-1049, a PS0.50 balance)."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number="PLACEHOLDER-GBP-1", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0, currency="GBP")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=50, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id


def test_credit_amount_placeholder_uses_the_invoices_own_currency(client, gbp_invoice_with_balance):
    page = client.get(f"/invoices/{gbp_invoice_with_balance}").data.decode()
    assert 'placeholder="£0.50"' in page, page
    assert 'placeholder="$0.50"' not in page, page
