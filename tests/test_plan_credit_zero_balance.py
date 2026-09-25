"""A payment plan whose invoice reaches a zero balance through a credit note.

Credit notes let staff settle an invoice without a payment ever landing. Before this
fix, nothing on that path told an open payment plan its invoice was done: the plan
stayed "active" with $0.00 due on every remaining row, and the manual Remind button
would happily email the client about a $0.00 installment. The scheduled charge job and
the public pay page already refused at a zero balance; only the credit path and the
manual reminder button did not.

Run: .venv/bin/python -m pytest tests/test_plan_credit_zero_balance.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_plan_credit_zero_balance.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_plan_credit_zero_balance")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_plan_credit_zero_balance")

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


@pytest.fixture
def invoice_with_plan(app):
    """A sent $3.00 invoice with an active, non-auto-charge payment plan on it."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, PaymentPlan
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"PCZ-{next(_seq):04d}", matter_id=m.id,
                      client_id=m.client_id, status="sent", issued_on=date.today(), tax_cents=0)
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=300, kind="fee"))
        db.session.flush()
        inv.recalc()
        plan = PaymentPlan(invoice_id=inv.id, contact_id=inv.client_id, installment_cents=100,
                           installments=3, paid_installments=0, frequency="monthly",
                           next_charge_on=date.today() + timedelta(days=30), auto_charge=False,
                           status="active")
        db.session.add(plan)
        db.session.commit()
        return inv.id, plan.id


def _plan_status(app, pid):
    from app.models import PaymentPlan
    from app.extensions import db
    with app.app_context():
        return db.session.get(PaymentPlan, pid).status


def test_crediting_an_invoice_to_zero_completes_its_open_plan(app, client, invoice_with_plan):
    inv_id, plan_id = invoice_with_plan
    post(client, f"/invoices/{inv_id}/credit", {"amount": "1.00", "reason": "other"})
    assert _plan_status(app, plan_id) == "active", "still $2.00 outstanding"
    post(client, f"/invoices/{inv_id}/credit", {"amount": "2.00", "reason": "other"})
    assert _plan_status(app, plan_id) == "completed", "nothing left to pay, so the plan should not still be active"


def test_remind_refuses_once_the_plan_is_complete(app, client, invoice_with_plan):
    inv_id, plan_id = invoice_with_plan
    post(client, f"/invoices/{inv_id}/credit", {"amount": "3.00", "reason": "other"})
    assert _plan_status(app, plan_id) == "completed"
    resp = post(client, f"/money/plans/{plan_id}/remind", {})
    assert b"The plan is completed." in resp.data


def test_remind_refuses_on_a_zero_balance_plan_even_if_still_marked_active(app, invoice_with_plan):
    """Belt and braces: whatever state a plan is in, Remind must not fire on a settled invoice."""
    from app.extensions import db
    from app.models import PaymentPlan
    inv_id, plan_id = invoice_with_plan
    with app.app_context():
        plan = db.session.get(PaymentPlan, plan_id)
        inv = plan.invoice
        inv.paid_cents = inv.total_cents
        plan.status = "active"
        db.session.commit()
    c = app.test_client()
    c._csrf = login(c)
    resp = post(c, f"/money/plans/{plan_id}/remind", {})
    assert b"nothing left to pay" in resp.data


def test_voiding_the_credit_leaves_the_plan_completed_and_says_so(app, client, invoice_with_plan):
    """Reopening the plan silently would restart reminders the client was told had ended.
    Leave it completed, and tell the attorney so they can decide."""
    inv_id, plan_id = invoice_with_plan
    post(client, f"/invoices/{inv_id}/credit", {"amount": "3.00", "reason": "other"})
    assert _plan_status(app, plan_id) == "completed"
    from app.models import CreditNote
    with app.app_context():
        cid = CreditNote.query.filter_by(invoice_id=inv_id).order_by(CreditNote.id.desc()).first().id
    resp = post(client, f"/invoices/credit/{cid}/void", {})
    assert _plan_status(app, plan_id) == "completed", "voiding a credit must not quietly reopen the plan"
    assert b"stays completed" in resp.data
