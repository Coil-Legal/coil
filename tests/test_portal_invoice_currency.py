"""QA issue #132: same defect class as #60-#76, at the client portal home page
(/portal) Invoices due card. It used the plain `money` filter (always a dollar sign)
for an invoice's balance cell instead of `cur(i.currency)`, so a GBP invoice's balance
showed with a bare dollar sign even though the invoice's own staff page, its public
page and its pay page all show pounds.

Run: .venv/bin/python -m pytest tests/test_portal_invoice_currency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_portal_invoice_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_portal_invoice_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_portal_invoice_currency")


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
def gbp_sent_invoice(app):
    """A sent GBP invoice with a £200.00 balance on a matter with its own client,
    so the portal login below signs in as that invoice's own client."""
    from app.extensions import db
    from app.models import Contact, Invoice, InvoiceLine, Matter
    with app.app_context():
        client = Contact(first_name="Portal", last_name="GBP Test Client", is_client=True)
        db.session.add(client)
        db.session.flush()
        m = Matter(number="PORTAL-GBP-1", client_id=client.id, name="Portal GBP matter",
                  billing_type="flat", currency="GBP", status="open")
        db.session.add(m)
        db.session.flush()
        inv = Invoice(number="PORTAL-GBP-INV-1", matter_id=m.id, client_id=client.id,
                      status="sent", issued_on=date.today(), due_on=date.today() + timedelta(days=30),
                      tax_cents=0, currency="GBP")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=20000, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return client.id


def portal_login(app, contact_id):
    from app.extensions import db
    from app.models import PortalToken, now
    with app.app_context():
        tok = PortalToken(contact_id=contact_id, expires_at=now() + timedelta(minutes=30))
        db.session.add(tok)
        db.session.commit()
        token = tok.token
    c = app.test_client()
    r = c.get(f"/portal/auth/{token}")
    assert r.status_code == 302 and r.headers["Location"].endswith("/portal")
    return c


def test_portal_invoices_due_shows_balance_in_the_invoices_own_currency(app, gbp_sent_invoice):
    c = portal_login(app, gbp_sent_invoice)
    page = c.get("/portal").data.decode()
    assert "£200.00" in page, page
    assert "$200.00" not in page, page
