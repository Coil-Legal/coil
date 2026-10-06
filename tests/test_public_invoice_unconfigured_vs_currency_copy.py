"""QA issue #142: on a USD invoice where online payments simply aren't configured (no Stripe
keys), the public invoice page's "Pay this invoice" card showed the sentence written for the
non-USD case ("This invoice is in USD ... payments only work in US dollars, so please pay by
bank transfer"), which is both self-contradictory and tells the client to use a method the page
never offers. `online_payment_ok()` (app/blueprints/invoices.py) returns False for two different
reasons (non-USD currency, or Stripe not configured) but public.html's `{% else %}` branch always
assumed the first one.

Run: .venv/bin/python -m pytest tests/test_public_invoice_unconfigured_vs_currency_copy.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_public_invoice_unconfigured_vs_currency_copy.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_public_invoice_unconfigured_vs_currency_copy")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_public_invoice_unconfigured_vs_currency_copy")


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


def _make_invoice(app, number, currency):
    from app.extensions import db
    from app.models import Contact, Invoice, InvoiceLine, Matter
    with app.app_context():
        client = Contact(first_name="Pay Copy", last_name=f"{currency} Client", is_client=True)
        db.session.add(client)
        db.session.flush()
        m = Matter(number=f"{number}-M", client_id=client.id, name=f"Pay copy {currency} matter",
                  billing_type="flat", currency=currency, status="open")
        db.session.add(m)
        db.session.flush()
        inv = Invoice(number=number, matter_id=m.id, client_id=client.id,
                      status="sent", issued_on=date.today(), due_on=date.today() + timedelta(days=30),
                      tax_cents=0, currency=currency)
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=20000, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id, inv.public_token


@pytest.fixture(scope="module")
def usd_sent_invoice(app):
    """A sent USD invoice on a firm seed.py never gives a Stripe key: not-configured, not currency."""
    return _make_invoice(app, "PAYCOPY-USD-INV-1", "USD")


@pytest.fixture(scope="module")
def gbp_sent_invoice(app):
    """A sent GBP invoice: the currency reason, which the page already states correctly."""
    return _make_invoice(app, "PAYCOPY-GBP-INV-1", "GBP")


def test_usd_invoice_says_not_set_up_not_wrong_currency(app, usd_sent_invoice):
    _, token = usd_sent_invoice
    c = app.test_client()
    page = c.get(f"/p/{token}").data.decode()
    assert "This invoice is in USD" not in page
    assert "pay by bank transfer" not in page
    assert "not able to take card or bank payments online" in page


def test_gbp_invoice_keeps_the_currency_sentence(app, gbp_sent_invoice):
    _, token = gbp_sent_invoice
    c = app.test_client()
    page = c.get(f"/p/{token}").data.decode()
    assert "This invoice is in GBP" in page
    assert "pay by bank transfer" in page


def test_usd_invoice_shows_currency_sentence_once_stripe_is_configured_but_currency_still_blocks(
        app, gbp_sent_invoice, monkeypatch):
    from app.blueprints import _stripe
    monkeypatch.setattr(_stripe, "configured", lambda: True)
    _, token = gbp_sent_invoice
    c = app.test_client()
    page = c.get(f"/p/{token}").data.decode()
    assert "This invoice is in GBP" in page
