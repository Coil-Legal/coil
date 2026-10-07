"""Coil QA #161: send_plan_reminder()'s HTML part includes ", due <Month D, Year>" built from
plan.next_charge_on, but the text/plain part never did, regardless of whether Stripe is
configured. A client whose mail client renders the plain-text alternative (text-only clients,
some screen readers, many previews and notifications) learned the installment amount but not
when it was due.

Run: .venv/bin/python -m pytest tests/test_plan_reminder_text_due_date.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_plan_reminder_text_due_date.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_plan_reminder_text_due_date")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_plan_reminder_text_due_date")

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


def _plan(app):
    """A sent $600.00 USD invoice with a 3-installment active plan, next charge 30 days out."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, PaymentPlan
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"PRT-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0, currency="USD")
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=60000, kind="fee"))
        db.session.flush()
        inv.recalc()
        inv.status = "sent"
        plan = PaymentPlan(invoice_id=inv.id, contact_id=m.client_id, installments=3, installment_cents=20000,
                           next_charge_on=date.today() + timedelta(days=30), status="active")
        db.session.add(plan)
        db.session.commit()
        return plan.id


def _capture_send_email(store):
    def _send(to, subject, html, text=None, attachments=None, reply_to=None, headers=None):
        store["to"], store["subject"], store["html"], store["text"] = to, subject, html, text
        return True
    return _send


def test_plain_text_part_states_the_due_date_no_stripe(app, monkeypatch):
    from app.extensions import db
    from app.models import PaymentPlan
    from app.blueprints import money as money_bp

    plan_id = _plan(app)
    captured = {}
    monkeypatch.setattr(money_bp, "send_email", _capture_send_email(captured))
    with app.app_context():
        plan = db.session.get(PaymentPlan, plan_id)
        plan.contact.email = "prtclient@example.test"
        db.session.commit()
        due_str = plan.next_charge_on.strftime("%B %-d, %Y")
        money_bp.send_plan_reminder(plan)
    assert due_str in captured["html"]
    assert due_str in captured["text"], "plain-text part must state the installment's due date too"


def test_plain_text_part_states_the_due_date_stripe_configured(app, monkeypatch):
    from app.extensions import db
    from app.models import PaymentPlan
    from app.blueprints import money as money_bp

    monkeypatch.setitem(app.config, "STRIPE_SECRET_KEY", "sk_test_fake")
    plan_id = _plan(app)
    captured = {}
    monkeypatch.setattr(money_bp, "send_email", _capture_send_email(captured))
    with app.app_context():
        plan = db.session.get(PaymentPlan, plan_id)
        plan.contact.email = "prtclient2@example.test"
        db.session.commit()
        due_str = plan.next_charge_on.strftime("%B %-d, %Y")
        money_bp.send_plan_reminder(plan)
    assert due_str in captured["html"]
    assert due_str in captured["text"], "plain-text part must state the installment's due date too"
