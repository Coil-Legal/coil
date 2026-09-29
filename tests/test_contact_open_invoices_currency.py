"""QA issue #76: same defect class as #60-#75, at the contact detail page's Open invoices
table (/contacts/<id>). It used the plain `money` filter (always a dollar sign) for an
invoice's Balance cell instead of `cur(i.currency)`, so a GBP invoice's balance showed with
a bare dollar sign even though the invoice's own page (fixed in #75's neighbor code) shows
pounds. The "Open invoices" stat tile above it summed every open invoice's balance_cents
into one scalar with the same plain `money` filter, which also misrepresents a non-USD
balance and would misrepresent a mix of currencies; fixed the same way as the dashboard's
"Outstanding A/R" tile (#60/#61), splitting by currency in the route and rendering with
`curmix`.

Run: .venv/bin/python -m pytest tests/test_contact_open_invoices_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_contact_open_invoices_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_contact_open_invoices_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_contact_open_invoices_currency")

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
def gbp_open_invoice(app):
    """A sent GBP invoice with a £0.50 balance and nothing paid, matching the QA fixture
    (INV-1049, a £0.50 balance)."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number="CONTACT-GBP-1", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0, currency="GBP")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=50, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return m.client_id


def test_contact_open_invoices_shows_balance_in_the_invoices_own_currency(client, gbp_open_invoice):
    page = client.get(f"/contacts/{gbp_open_invoice}").data.decode()
    assert page.count("£0.50") == 2, page  # the table cell and the stat tile
    assert "$0.50" not in page, page
