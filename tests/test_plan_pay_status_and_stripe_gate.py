"""Issues #145, #146 and #151: the public installment pay page (/pay/plan/<id>/<token>) must
refuse up front, on GET, in the cases where the only thing that can follow is "not set up" or
"this plan isn't active", and must quote the right amount when it does:

- #145: when the firm has no Stripe key, the GET page still rendered money/plan_pay.html,
  computing a card surcharge and a Continue-to-secure-payment button that could never complete;
  the refusal only fired once Checkout creation was attempted on POST. send_plan_reminder()
  had the same gap in the email it sends.
- #146: when a plan is cancelled or paused, the route only ever checked for "completed", so an
  old reminder's link kept offering a live installment and surcharge for a plan staff had
  already turned off.
- #151: the #145 "not set up" refusal page quoted the invoice's full balance ($600.00) instead
  of the installment the client was actually asked to pay ($200.00), because plan_pay() rendered
  payments/pay_unconfigured.html with only inv and f, and the template always read
  inv.balance_cents. Fixed by passing plan/amount/k through and having the template quote the
  installment when a plan is present.

Run: .venv/bin/python -m pytest tests/test_plan_pay_status_and_stripe_gate.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_plan_pay_status_and_stripe_gate.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_plan_pay_status_and_stripe_gate")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_plan_pay_status_and_stripe_gate")

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


@pytest.fixture
def stripe_on(app, monkeypatch):
    monkeypatch.setitem(app.config, "STRIPE_SECRET_KEY", "sk_test_fake")


def _plan(app, status="active"):
    """A sent $600.00 USD invoice with a 3-installment plan in the given status."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, PaymentPlan
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"PPS-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
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
        return inv.id, inv.public_token, plan.id


def test_installment_page_refuses_up_front_when_stripe_not_configured(app, client):
    inv_id, token, plan_id = _plan(app)
    anon = app.test_client()
    r = anon.get(f"/pay/plan/{plan_id}/{token}")
    assert r.status_code == 200
    assert b"not able to take card or bank payments online" in r.data
    assert b"Continue to secure payment" not in r.data
    assert b"surcharge" not in r.data.lower()
    assert b"installment 1 of 3" in r.data
    assert b"$200.00" in r.data
    assert b"$600.00" not in r.data
    r = anon.get(f"/pay/plan/{plan_id}/{token}?method=ach")
    assert b"Continue to secure payment" not in r.data


def test_installment_page_still_works_once_stripe_is_configured(app, client, stripe_on):
    inv_id, token, plan_id = _plan(app)
    anon = app.test_client()
    r = anon.get(f"/pay/plan/{plan_id}/{token}")
    assert r.status_code == 200
    assert b"Pay installment 1 of 3" in r.data
    assert b"Continue to secure payment" in r.data


def test_cancelled_plan_closes_the_installment_link(app, client, stripe_on):
    inv_id, token, plan_id = _plan(app, status="cancelled")
    anon = app.test_client()
    r = anon.get(f"/pay/plan/{plan_id}/{token}")
    assert r.status_code == 200
    assert b"This payment plan was cancelled" in r.data
    assert b"Continue to secure payment" not in r.data
    assert b"Pay installment" not in r.data
    r = anon.post(f"/pay/plan/{plan_id}/{token}")
    assert r.status_code == 200
    assert b"This payment plan was cancelled" in r.data


def test_paused_plan_closes_the_installment_link(app, client, stripe_on):
    inv_id, token, plan_id = _plan(app, status="paused")
    anon = app.test_client()
    r = anon.get(f"/pay/plan/{plan_id}/{token}")
    assert r.status_code == 200
    assert b"This payment plan is paused" in r.data
    assert b"Continue to secure payment" not in r.data


def test_reminder_email_does_not_promise_online_payment_when_stripe_not_configured(app):
    from app.extensions import db
    from app.models import PaymentPlan, Contact
    from app.blueprints import money as money_bp
    from app.services.mail import _dev_outbox
    inv_id, token, plan_id = _plan(app)
    with app.app_context():
        plan = db.session.get(PaymentPlan, plan_id)
        plan.contact.email = "ppsclient@example.test"
        db.session.commit()
        _dev_outbox.clear()
        to = money_bp.send_plan_reminder(plan)
        db.session.commit()
    assert to == "ppsclient@example.test"
    mail = _dev_outbox[-1]
    assert "not able to take card or bank payments online" in mail["html"]
    assert "Pay $200.00" not in mail["html"]
    assert f"/pay/plan/{plan_id}/{token}" not in mail["html"]


def test_reminder_email_offers_the_pay_link_when_stripe_is_configured(app, stripe_on):
    from app.extensions import db
    from app.models import PaymentPlan
    from app.blueprints import money as money_bp
    from app.services.mail import _dev_outbox
    inv_id, token, plan_id = _plan(app)
    with app.app_context():
        plan = db.session.get(PaymentPlan, plan_id)
        plan.contact.email = "ppsclient2@example.test"
        db.session.commit()
        _dev_outbox.clear()
        to = money_bp.send_plan_reminder(plan)
        db.session.commit()
    assert to == "ppsclient2@example.test"
    mail = _dev_outbox[-1]
    assert f"/pay/plan/{plan_id}/{token}" in mail["html"]
    assert "Pay $200.00" in mail["html"]
