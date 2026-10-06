"""Payment plan pages must show a GBP invoice's own currency symbol, never a bare $.

Issue #136: the setup flash, the plan detail page (Balance now, Schedule, Next,
installment rows, the Charge-now confirm and the Payments table), the plans list row
and the invoice Activity line all built their money strings with cents_to_str()/the
plain |money filter, which always defaults to "$". Card-surcharge figures stay in $ on
purpose: automatic charging is USD-only (app/blueprints/money.py::plan_new), so a
surcharge is always a dollar amount even on a plan whose installments are not.

Run: .venv/bin/python -m pytest tests/test_plan_currency_display.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_plan_currency_display.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_plan_currency_display")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_plan_currency_display")

from tests.helpers import login  # noqa: E402

_seq = iter(range(1, 9999))


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


@pytest.fixture(scope="module")
def gbp_invoice(app):
    """A sent £100.00 invoice with no payment plan yet."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"PCD-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0, currency="GBP")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=10000, kind="fee"))
        db.session.flush()
        inv.recalc()
        inv.status = "sent"
        db.session.commit()
        return inv.id


def test_plan_setup_flash_and_activity_line_use_the_invoice_currency(app, client, gbp_invoice):
    first = (date.today() + timedelta(days=30)).isoformat()
    resp = post(client, "/money/plans/new", {"invoice_id": gbp_invoice, "installments": "2",
                                             "frequency": "monthly", "first_charge_on": first})
    assert "£50.00".encode() in resp.data, "setup flash should read £50.00, not a bare $"
    assert b"$50.00" not in resp.data

    resp = client.get(f"/invoices/{gbp_invoice}")
    assert "payment plan: 2 monthly installments of £50.00".encode() in resp.data


def test_plan_detail_page_uses_the_invoice_currency(app, client, gbp_invoice):
    from app.models import PaymentPlan
    from app.extensions import db
    with app.app_context():
        plan_id = PaymentPlan.query.filter_by(invoice_id=gbp_invoice).first().id
    resp = client.get(f"/money/plans/{plan_id}")
    body = resp.data
    assert "£100.00".encode() in body, "Balance now should read £100.00"
    assert "£50.00".encode() in body, "Schedule/Next/installment rows should read £50.00"
    assert b"$50.00" not in body
    assert b"$100.00" not in body


def test_plans_list_uses_the_invoice_currency(app, client, gbp_invoice):
    resp = client.get("/money/plans")
    body = resp.data
    assert "£100.00".encode() in body, "the list's balance column should read £100.00"
    assert "£50.00".encode() in body, "the list's schedule/next-amount columns should read £50.00"
    assert b"$50.00" not in body
    assert b"$100.00" not in body
