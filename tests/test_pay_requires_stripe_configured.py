"""QA issue #134: a firm with no Stripe keys configured still showed both pay buttons on a USD
invoice's public page, and `GET /pay/<token>` still rendered the confirm page, surcharge and all,
before failing on the submit with "Online payments are not set up yet". `online_payment_ok()` in
app/blueprints/invoices.py checked only the invoice's currency, never `_stripe.configured()`; the
two checks that did exist both lived in the POST handler of `pay()` in payments.py, after the
confirm page (and its surcharge figure) had already been shown on GET.

Run: .venv/bin/python -m pytest tests/test_pay_requires_stripe_configured.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_pay_requires_stripe_configured.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_pay_requires_stripe_configured")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_pay_requires_stripe_configured")


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
def usd_sent_invoice(app):
    """A sent USD invoice with a $200.00 balance, on a firm seed.py never gives a Stripe key."""
    from app.extensions import db
    from app.models import Contact, Invoice, InvoiceLine, Matter
    with app.app_context():
        client = Contact(first_name="Pay Gate", last_name="Test Client", is_client=True)
        db.session.add(client)
        db.session.flush()
        m = Matter(number="PAYGATE-USD-1", client_id=client.id, name="Pay gate USD matter",
                  billing_type="flat", currency="USD", status="open")
        db.session.add(m)
        db.session.flush()
        inv = Invoice(number="PAYGATE-USD-INV-1", matter_id=m.id, client_id=client.id,
                      status="sent", issued_on=date.today(), due_on=date.today() + timedelta(days=30),
                      tax_cents=0, currency="USD")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=20000, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id, inv.public_token


def test_public_page_shows_no_pay_button_without_a_stripe_key(app, usd_sent_invoice):
    _, token = usd_sent_invoice
    c = app.test_client()
    page = c.get(f"/p/{token}").data.decode()
    assert "Pay by bank transfer" not in page
    assert "Pay by card" not in page
    assert f"/pay/{token}" not in page


@pytest.mark.parametrize("method", ["card", "ach"])
def test_pay_page_refuses_before_computing_a_surcharge(app, usd_sent_invoice, method):
    _, token = usd_sent_invoice
    c = app.test_client()
    r = c.get(f"/pay/{token}?method={method}")
    assert r.status_code == 200
    assert b"not set up" in r.data
    assert b"Card processing surcharge" not in r.data
    assert b"Continue to secure payment" not in r.data


def test_pay_page_post_refuses_too(app, usd_sent_invoice):
    _, token = usd_sent_invoice
    c = app.test_client()
    r = c.post(f"/pay/{token}?method=card")
    assert r.status_code == 200
    assert b"not set up" in r.data


def test_pay_button_and_confirm_page_return_once_stripe_is_configured(app, usd_sent_invoice, monkeypatch):
    from app.blueprints import _stripe
    monkeypatch.setattr(_stripe, "configured", lambda: True)
    _, token = usd_sent_invoice
    c = app.test_client()
    page = c.get(f"/p/{token}").data.decode()
    assert f"/pay/{token}?method=card" in page
    r = c.get(f"/pay/{token}?method=card")
    assert r.status_code == 200
    assert b"not set up" not in r.data
