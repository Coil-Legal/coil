"""Defensive accounting regression checks using isolated synthetic records."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Barrier, Lock, get_ident

import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session

from tests.test_phase1_independent import app, staff


def invoice(app, currency="USD"):
    from app.extensions import db
    from app.models import Contact, Invoice, InvoiceLine
    with app.app_context():
        c = db.session.get(Contact, 1)
        c.stripe_customer_id = "cus_synthetic"
        c.stripe_payment_method_id = "pm_synthetic"
        inv = Invoice(number="REVIEW-1", matter_id=1, client_id=1,
                      status="sent", currency=currency, issued_on=date.today())
        inv.lines.append(InvoiceLine(kind="time", description="Synthetic work", quantity=1,
                                     unit_cents=10000, amount_cents=10000, sort=1))
        db.session.add(inv)
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id, inv.public_token


def test_simultaneous_trust_debits_preserve_nonnegative_balance(app):
    from app.extensions import db
    from app.models import TrustTransaction
    with app.app_context():
        db.session.add(TrustTransaction(client_id=1, matter_id=1, date=date.today(),
                                       type="deposit", amount_cents=10000))
        db.session.commit()
    clients = [staff(app), staff(app)]
    barrier, seen, lock = Barrier(2), set(), Lock()

    def align_debits(session, *_):
        if any(isinstance(row, TrustTransaction) and row.amount_cents < 0 for row in session.new):
            with lock:
                first = get_ident() not in seen
                seen.add(get_ident())
            if first:
                barrier.wait(timeout=10)

    def debit(item):
        client, csrf = item
        return client.post("/trust/new", data={"_csrf": csrf, "client_id": "1", "matter_id": "1",
                           "type": "disbursement", "date": date.today().isoformat(),
                           "amount": "80.00", "payee": "Synthetic payee"}).status_code

    event.listen(Session, "before_flush", align_debits)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(debit, clients))
    finally:
        event.remove(Session, "before_flush", align_debits)
    with app.app_context():
        rows = [row.amount_cents for row in TrustTransaction.query.all()]
    assert sum(rows) >= 0, f"HTTP {statuses}; ledger cents {rows}; balance {sum(rows)}"


def test_simultaneous_card_charges_match_recorded_payments(app, monkeypatch):
    from app.blueprints import _stripe
    from app.models import Payment
    iid, _ = invoice(app)
    clients = [staff(app), staff(app)]
    barrier, calls, lock = Barrier(2), [], Lock()
    monkeypatch.setattr(_stripe, "configured", lambda: True)
    monkeypatch.setattr(_stripe, "fee_cents_for_payment_intent", lambda _: 0)

    def charge(customer, method, amount, **kwargs):
        with lock:
            pi = f"pi_review_{len(calls) + 1}"
            calls.append({"amount": amount, "idempotency_key": kwargs.get("idempotency_key")})
        # Keep the first provider request in flight while the competing request arrives.
        import time
        time.sleep(0.15)
        return {"id": pi, "status": "succeeded"}

    monkeypatch.setattr(_stripe, "charge_payment_method", charge)

    def post(item):
        client, csrf = item
        barrier.wait(timeout=10)
        try:
            return client.post(f"/money/charge/{iid}", data={"_csrf": csrf, "amount": "100.00"}).status_code
        except Exception as exc:
            return type(exc).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(post, clients))
    with app.app_context():
        recorded = sum(p.amount_cents for p in Payment.query.all())
    charged = sum(call["amount"] for call in calls)
    assert charged == recorded and charged <= 10000, f"results={results}; charged={charged}; recorded={recorded}; calls={calls}"


@pytest.mark.parametrize("entry", ["saved_card", "plan_link"])
def test_non_usd_invoice_never_charges_usd(app, monkeypatch, entry):
    from app.blueprints import _stripe
    from app.extensions import db
    from app.models import PaymentPlan
    iid, token = invoice(app, "EUR")
    client, csrf = staff(app)
    calls = []
    monkeypatch.setattr(_stripe, "configured", lambda: True)
    monkeypatch.setattr(_stripe, "fee_cents_for_payment_intent", lambda _: 0)

    def charge(*args, **kwargs):
        calls.append((args, kwargs))
        return {"id": "pi_review_currency", "status": "succeeded"}

    def checkout(**kwargs):
        calls.append(kwargs)
        return {"id": "cs_review_currency", "url": "https://checkout.example.test/synthetic"}

    monkeypatch.setattr(_stripe, "charge_payment_method", charge)
    monkeypatch.setattr(_stripe, "create_checkout_session", checkout)
    if entry == "saved_card":
        response = client.post(f"/money/charge/{iid}", data={"_csrf": csrf, "amount": "100.00"})
    else:
        with app.app_context():
            plan = PaymentPlan(invoice_id=iid, contact_id=1, installments=2,
                               installment_cents=5000, next_charge_on=date.today(), status="active")
            db.session.add(plan)
            db.session.commit()
            pid = plan.id
        response = client.post(f"/pay/plan/{pid}/{token}")
    assert not calls, f"entry={entry}; HTTP {response.status_code}; USD payment submitted for EUR invoice: {calls}"


def test_card_setup_token_does_not_authenticate_portal(app):
    from app.blueprints.money import new_card_token
    from app.extensions import db
    from app.models import Contact
    with app.app_context():
        token = new_card_token(db.session.get(Contact, 1)).token
        db.session.commit()
    client = app.test_client()
    response = client.get(f"/portal/auth/{token}")
    with client.session_transaction() as session:
        authenticated = session.get("portal_contact_id")
    assert authenticated is None, f"Card setup link created portal session for synthetic contact {authenticated}; HTTP {response.status_code}"


def test_installment_checkout_updates_plan_once(app):
    from app.extensions import db
    from app.models import Invoice, PaymentPlan, Payment
    from tests.helpers import post_stripe_event
    iid, _ = invoice(app)
    with app.app_context():
        plan = PaymentPlan(invoice_id=iid, contact_id=1, installments=2, paid_installments=0,
                           installment_cents=5000, next_charge_on=date.today(), status="active")
        db.session.add(plan)
        db.session.commit()
        pid = plan.id
    payload = {"type": "checkout.session.completed", "data": {"object": {
        "id": "cs_review_installment", "mode": "payment", "payment_status": "paid",
        "payment_intent": "pi_review_installment", "amount_total": 5000,
        "metadata": {"kind": "invoice", "invoice_id": str(iid), "plan_id": str(pid),
                     "surcharge_cents": "0", "method": "card"}}}}
    client = app.test_client()
    for _ in range(2):
        assert post_stripe_event(client, app, payload).status_code == 200
    with app.app_context():
        plan = db.session.get(PaymentPlan, pid)
        balance = db.session.get(Invoice, iid).balance_cents
        rows = Payment.query.count()
        assert (plan.paid_installments, balance, rows) == (1, 5000, 1), (
            f"paid_installments={plan.paid_installments}; invoice balance={balance}; payment rows={rows}")
