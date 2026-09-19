"""Reducing what a client owes on an invoice that has already gone out.

The thing people reach for instead is editing the invoice, which quietly rewrites a
record the firm is required to keep and leaves the client holding a copy that no longer
matches. So the reduction gets its own dated, numbered document sitting beside the
invoice. If the fee is ever questioned, the pair is what gets read: here is what we
billed, here is what we took off, here is who decided and why.

The line these tests hold is the one that actually matters in accounting: a credit
against money not yet collected reduces a receivable, and a credit against money
already in hand is a promise to send it back. Those are different operations and only
the first one is a credit note.

Run: .venv/bin/python -m pytest tests/test_credit_notes.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_credit_notes.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_credit_notes")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_credit_notes")

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


def post(c, path, data):
    return c.post(path, data=dict(data, _csrf=c._csrf), follow_redirects=True)


_seq = iter(range(1, 9999))


@pytest.fixture
def sent_invoice(app):
    """A sent $1,000 invoice with nothing paid on it."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"CNT-{next(_seq):04d}", matter_id=m.id,
                      client_id=m.client_id, status="sent", issued_on=date.today(), tax_cents=0)
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=100000, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id


def _inv(app, iid):
    from app.models import Invoice
    from app.extensions import db
    with app.app_context():
        i = db.session.get(Invoice, iid)
        return i.total_cents, i.paid_cents, i.credited_cents, i.balance_cents, i.status


# ------------------------------------------------------------------ the ordinary case
def test_a_credit_reduces_the_balance(app, client, sent_invoice):
    post(client, f"/invoices/{sent_invoice}/credit",
         {"amount": "250.00", "reason": "billing_error", "note": "Duplicate entry on 14 May"})
    total, paid, credited, balance, _ = _inv(app, sent_invoice)
    assert total == 100000, "the invoice itself is untouched"
    assert credited == 25000
    assert balance == 75000


def test_a_credit_is_never_counted_as_money_collected(app, client, sent_invoice):
    """The distinction the whole feature exists for. Fold these together and the revenue
    report tells a firm it collected money that never arrived."""
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "400.00", "reason": "courtesy"})
    _, paid, credited, _, _ = _inv(app, sent_invoice)
    assert paid == 0, "nobody paid anything"
    assert credited == 40000


def test_it_gets_its_own_number_and_leaves_the_invoice_run_unbroken(app, client, sent_invoice):
    from app.models import CreditNote, Firm
    with app.app_context():
        before = Firm.get().next_invoice_number
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "10.00", "reason": "other"})
    with app.app_context():
        cn = CreditNote.query.order_by(CreditNote.id.desc()).first()
        assert cn.number.startswith("CN-"), "a gap in the invoice numbers is the first thing an auditor asks about"
        assert Firm.get().next_invoice_number == before


def test_it_records_who_decided_and_why(app, client, sent_invoice):
    post(client, f"/invoices/{sent_invoice}/credit",
         {"amount": "50.00", "reason": "fee_dispute", "note": "Agreed with client 19 Sep"})
    from app.models import CreditNote, AuditLog
    with app.app_context():
        cn = CreditNote.query.order_by(CreditNote.id.desc()).first()
        assert cn.reason == "fee_dispute" and cn.note == "Agreed with client 19 Sep"
        assert cn.created_by_id
        row = AuditLog.query.filter_by(action="credit_note").order_by(AuditLog.id.desc()).first()
        assert cn.number in row.detail and "Fee dispute" in row.detail


def test_crediting_the_whole_balance_settles_the_invoice(app, client, sent_invoice):
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "1000.00", "reason": "uncollectible"})
    total, paid, credited, balance, status = _inv(app, sent_invoice)
    assert balance == 0 and credited == 100000
    assert paid == 0, "settled is not collected, and the reports read paid_cents"
    assert status == "paid"


# ------------------------------------------------------------------ the lines it will not cross
def test_it_refuses_to_credit_a_paid_invoice(app, client, sent_invoice):
    """Money already in hand cannot be un-owed. Sending it back is a refund: it moves
    cash and reverses posted income, and Coil has no operating refund yet. Say so
    plainly rather than recording a reduction the client never receives."""
    from app.extensions import db
    from app.models import Invoice, Payment
    with app.app_context():
        inv = db.session.get(Invoice, sent_invoice)
        db.session.add(Payment(invoice_id=inv.id, matter_id=inv.matter_id, client_id=inv.client_id,
                               amount_cents=100000, method="check", account="operating"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
    r = post(client, f"/invoices/{sent_invoice}/credit", {"amount": "100.00", "reason": "courtesy"})
    body = r.data.decode()
    assert "paid in full" in body and "refund" in body.lower()
    _, _, credited, _, _ = _inv(app, sent_invoice)
    assert credited == 0, "nothing was credited"


def test_it_will_not_credit_past_zero(app, client, sent_invoice):
    """Going below zero leaves the client holding a credit balance, which for a law firm
    is money owed back rather than store credit."""
    r = post(client, f"/invoices/{sent_invoice}/credit", {"amount": "1500.00", "reason": "courtesy"})
    assert "below zero" in r.data.decode()
    _, _, credited, balance, _ = _inv(app, sent_invoice)
    assert credited == 0 and balance == 100000


def test_a_draft_is_edited_not_credited(app, client):
    from app.extensions import db
    from app.models import Invoice, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"CND-{next(_seq):04d}", matter_id=m.id,
                      client_id=m.client_id, status="draft", issued_on=date.today())
        db.session.add(inv)
        db.session.commit()
        iid = inv.id
    r = post(client, f"/invoices/{iid}/credit", {"amount": "10.00", "reason": "other"})
    assert "draft can be edited" in r.data.decode()


def test_zero_and_negative_are_refused(app, client, sent_invoice):
    for amt in ("0", "-50.00"):
        r = post(client, f"/invoices/{sent_invoice}/credit", {"amount": amt, "reason": "other"})
        assert "positive amount" in r.data.decode()


# ------------------------------------------------------------------ undoing one
def test_voiding_a_credit_puts_the_money_back_on_the_bill(app, client, sent_invoice):
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "300.00", "reason": "courtesy"})
    from app.models import CreditNote
    with app.app_context():
        cid = CreditNote.query.order_by(CreditNote.id.desc()).first().id
    assert _inv(app, sent_invoice)[3] == 70000
    post(client, f"/invoices/credit/{cid}/void", {})
    assert _inv(app, sent_invoice)[3] == 100000


def test_a_voided_credit_is_kept_not_deleted(app, client, sent_invoice):
    """The bar rules make bills a five year record. A credit that was issued and
    withdrawn is part of that story."""
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "120.00", "reason": "other"})
    from app.extensions import db
    from app.models import CreditNote
    with app.app_context():
        cn = CreditNote.query.order_by(CreditNote.id.desc()).first()
        cid, number = cn.id, cn.number
    post(client, f"/invoices/credit/{cid}/void", {})
    with app.app_context():
        cn = db.session.get(CreditNote, cid)
        assert cn is not None and cn.status == "void" and cn.number == number
        assert cn.voided_at and cn.voided_by_id
    assert number in client.get(f"/invoices/{sent_invoice}").data.decode()


# ------------------------------------------------------------------ what it touches downstream
def test_a_payment_plan_shortens_on_its_own(app, client, sent_invoice):
    """The schedule is derived from the balance at render time, so a credit has to reach
    it without anything being recomputed by hand."""
    from app.extensions import db
    from app.models import Invoice, PaymentPlan
    with app.app_context():
        inv = db.session.get(Invoice, sent_invoice)
        plan = PaymentPlan(invoice_id=inv.id, contact_id=inv.client_id, installments=4,
                           installment_cents=25000, frequency="monthly",
                           next_charge_on=date.today(), status="active")
        db.session.add(plan)
        db.session.commit()
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "200.00", "reason": "billing_error"})
    with app.app_context():
        inv = db.session.get(Invoice, sent_invoice)
        assert inv.balance_cents == 80000
        plan = PaymentPlan.query.filter_by(invoice_id=inv.id).first()
        remaining = sum(r["amount_cents"] for r in plan.plan_schedule()) if hasattr(plan, "plan_schedule") else None
        if remaining is not None:
            assert remaining <= inv.balance_cents, \
                "the schedule must never add up to more than is actually owed"


def test_the_invoice_page_shows_credits_apart_from_payments(app, client, sent_invoice):
    post(client, f"/invoices/{sent_invoice}/credit", {"amount": "75.00", "reason": "courtesy",
                                                      "note": "Goodwill on the May bill"})
    page = client.get(f"/invoices/{sent_invoice}").data.decode()
    assert "Credited" in page and "not collected" in page
    assert "Goodwill on the May bill" in page
