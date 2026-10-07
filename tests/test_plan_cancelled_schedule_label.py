"""Issue #152: a cancelled payment plan's schedule still labelled its first unpaid
installment "next when resumed", the same label a paused plan correctly gets. A cancelled
plan can't be resumed (plan_resume only allows paused/failed), so the label told staff the
plan would pick up again when it can't.

Run: .venv/bin/python -m pytest tests/test_plan_cancelled_schedule_label.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_plan_cancelled_schedule_label.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_plan_cancelled_schedule_label")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_plan_cancelled_schedule_label")

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


def _plan(app, status="active"):
    """A sent $600.00 USD invoice with a 3-installment plan in the given status."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, PaymentPlan
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"PCL-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0, currency="USD")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=60000, kind="fee"))
        db.session.flush()
        inv.recalc()
        inv.status = "sent"
        plan = PaymentPlan(invoice_id=inv.id, contact_id=m.client_id, installments=3, installment_cents=20000,
                           next_charge_on=date.today() + timedelta(days=30), status=status)
        db.session.add(plan)
        db.session.commit()
        return inv.id, plan.id


def test_cancelled_plan_schedule_does_not_promise_a_resume(app, client):
    inv_id, plan_id = _plan(app, status="active")
    r = client.post(f"/money/plans/{plan_id}/cancel", data={"_csrf": client._csrf}, follow_redirects=True)
    assert b"Plan cancelled" in r.data
    resp = client.get(f"/money/plans/{plan_id}")
    assert resp.status_code == 200
    assert b"next when resumed" not in resp.data
    assert b"cancelled" in resp.data.lower()


def test_paused_plan_schedule_still_promises_a_resume(app, client):
    inv_id, plan_id = _plan(app, status="active")
    client.post(f"/money/plans/{plan_id}/pause", data={"_csrf": client._csrf}, follow_redirects=True)
    resp = client.get(f"/money/plans/{plan_id}")
    assert resp.status_code == 200
    assert b"next when resumed" in resp.data
