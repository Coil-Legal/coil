"""Saved-card collection with durable reservations and provider reconciliation."""
from datetime import date, timedelta

from flask import current_app
from sqlalchemy import update

from ..extensions import db
from ..models import (CardChargeAttempt, Invoice, InvoiceEvent, Payment, PaymentPlan,
                      PlanInstallmentReceipt, Firm, audit, now)
from . import _stripe


def write_snapshot(invoice_id):
    """Acquire the SQLite writer before reading a balance, without holding it over HTTP."""
    db.session.rollback()
    db.session.execute(update(Invoice).where(Invoice.id == invoice_id).values(version=Invoice.version),
                       execution_options={"synchronize_session": False})


def installment_due(plan):
    return plan.installment_due_on or plan.next_charge_on or date.today()


def apply_installment(plan, payment, number=None, due_on=None):
    """Caller holds the payment transaction. A repeated installment never advances twice."""
    from .money import advance_date, _complete_if_done, _plan_anchor_day
    if not plan or plan.invoice_id != payment.invoice_id:
        return
    if payment.amount_cents <= 0:
        return
    number = int(number or (plan.paid_installments or 0) + 1)
    if not 1 <= number <= plan.installments:
        raise ValueError("Invalid installment number")
    if PlanInstallmentReceipt.query.filter_by(plan_id=plan.id, number=number).first():
        return
    due = due_on or installment_due(plan)
    db.session.add(PlanInstallmentReceipt(plan_id=plan.id, number=number, payment_id=payment.id, due_on=due))
    db.session.flush()
    while (plan.paid_installments or 0) < plan.installments:
        receipt = PlanInstallmentReceipt.query.filter_by(
            plan_id=plan.id, number=(plan.paid_installments or 0) + 1).first()
        if not receipt:
            break
        plan.paid_installments = receipt.number
        next_due = advance_date(receipt.due_on or installment_due(plan), plan.frequency,
                                anchor_day=_plan_anchor_day(plan))
        plan.installment_due_on = next_due
        # The reminder scheduler may already have advanced its notification date.
        if not plan.next_charge_on or plan.next_charge_on < next_due:
            plan.next_charge_on = next_due
    payment.note = f"Payment plan {plan.id}: installment {number} of {plan.installments}"
    plan.last_error = ""
    _complete_if_done(plan)


def reserve(invoice_id, amount, user_id, note, plan_id, charge_on, expected_paid):
    from .money import has_card, surcharge_cents, OPEN_INVOICE
    write_snapshot(invoice_id)
    inv = db.session.get(Invoice, invoice_id)
    attempt = CardChargeAttempt.query.filter_by(active_invoice_id=invoice_id).first()
    if attempt:
        if attempt.amount_cents != amount or attempt.plan_id != plan_id:
            raise ValueError("A previous card charge is awaiting confirmation. Retry its original amount first.")
        if attempt.state == "processing" and attempt.claimed_at > now() - timedelta(minutes=5):
            raise ValueError("A card charge is already in progress. Wait for its confirmation before trying again.")
        if attempt.created_at < now() - timedelta(hours=23):
            raise ValueError("This charge needs reconciliation with Stripe before another charge can be made.")
        attempt.state, attempt.claimed_at = "processing", now()
    else:
        if expected_paid is not None and inv.paid_cents != expected_paid:
            raise ValueError("Another payment changed this invoice. Reload it before charging again.")
        if (inv.currency or "USD").upper() != "USD":
            raise ValueError("Online payments support USD invoices only.")
        if inv.status not in OPEN_INVOICE:
            raise ValueError(f"Invoice {inv.number} is {inv.status}; only sent, viewed or partial invoices can be charged.")
        if amount <= 0:
            raise ValueError("Enter a positive amount.")
        if amount > inv.balance_cents:
            raise ValueError("That is more than the balance of this invoice.")
        if not has_card(inv.client):
            raise ValueError(f"{inv.client.display_name} has no card on file.")
        plan = db.session.get(PaymentPlan, plan_id) if plan_id else None
        if plan and (plan.invoice_id != inv.id or plan.status not in ("active", "paused", "failed")):
            raise ValueError("The payment plan cannot be charged.")
        attempt = CardChargeAttempt(
            invoice_id=inv.id, active_invoice_id=inv.id, plan_id=plan_id,
            installment=(plan.paid_installments or 0) + 1 if plan else None,
            due_on=installment_due(plan) if plan else None, charge_on=charge_on or date.today(),
            user_id=user_id, amount_cents=amount, surcharge_cents=surcharge_cents(amount, Firm.get()),
            customer_id=inv.client.stripe_customer_id, method_id=inv.client.stripe_payment_method_id,
            description=f"Invoice {inv.number}" + (f" (payment plan {plan.id})" if plan else ""), note=note[:300])
        db.session.add(attempt)
    db.session.commit()
    # Freeze provider parameters, then release the read snapshot before the network call.
    result = {column.name: getattr(attempt, column.name) for column in CardChargeAttempt.__table__.columns}
    db.session.rollback()
    return result


def finish(attempt_id, pi_id, fee=0):
    """Atomically record a successful charge and its plan progress. Commits."""
    attempt = db.session.get(CardChargeAttempt, attempt_id)
    if not attempt:
        raise ValueError("Unknown card collection attempt")
    invoice_id = attempt.invoice_id
    write_snapshot(invoice_id)
    attempt = db.session.get(CardChargeAttempt, attempt_id)
    if attempt.payment_id:
        if attempt.stripe_payment_intent != pi_id:
            raise ValueError("Different Stripe payment for an already settled attempt")
        payment = db.session.get(Payment, attempt.payment_id)
        if fee:
            payment.stripe_fee_cents = fee
        db.session.commit()
        return payment
    if not pi_id:
        raise ValueError("Missing Stripe payment identity")
    inv = db.session.get(Invoice, invoice_id)
    payment = Payment(invoice_id=inv.id, matter_id=inv.matter_id, client_id=inv.client_id,
                      amount_cents=attempt.amount_cents, surcharge_cents=attempt.surcharge_cents,
                      stripe_fee_cents=fee or 0, method="card", account="operating",
                      stripe_payment_intent=pi_id, received_on=attempt.charge_on, reference=pi_id, note=attempt.note)
    inv.payments.append(payment)
    db.session.flush()
    inv.recalc()
    if attempt.plan_id:
        plan = db.session.get(PaymentPlan, attempt.plan_id)
        apply_installment(plan, payment, attempt.installment, attempt.due_on)
        audit("plan_charged", "payment_plan", attempt.plan_id, attempt.charge_on.isoformat(), attempt.user_id)
    attempt.payment_id = payment.id
    attempt.stripe_payment_intent = pi_id
    attempt.state, attempt.active_invoice_id = "succeeded", None
    db.session.add(InvoiceEvent(invoice_id=inv.id, event="paid", detail=f"Card payment recorded: {pi_id}"))
    audit("card_charged", "invoice", inv.id, f"{attempt.amount_cents} cents, {pi_id}", attempt.user_id)
    db.session.commit()
    return payment


def retryable(attempt_id):
    db.session.rollback()
    # Never overwrite a success that arrived through the webhook in the meantime.
    db.session.execute(update(CardChargeAttempt).where(CardChargeAttempt.id == attempt_id,
                       CardChargeAttempt.payment_id.is_(None)).values(state="retry"))
    db.session.commit()


def collect(invoice_id, amount, user_id=None, note="Charged card on file", plan_id=None, charge_on=None,
            expected_paid=None):
    from .money import NOT_CONFIGURED
    if not _stripe.configured():
        return None, NOT_CONFIGURED
    try:
        attempt = reserve(invoice_id, int(amount), user_id, note, plan_id, charge_on, expected_paid)
    except ValueError as exc:
        db.session.rollback()
        return None, str(exc)
    except Exception:
        db.session.rollback()
        current_app.logger.exception("could not reserve card collection")
        return None, "The charge could not be started. Please try again."
    try:
        pi = _stripe.charge_payment_method(
            attempt["customer_id"], attempt["method_id"], attempt["amount_cents"] + attempt["surcharge_cents"],
            description=attempt["description"], idempotency_key=attempt["idempotency_key"],
            metadata={"kind": "invoice", "invoice_id": str(invoice_id), "method": "card",
                      "surcharge_cents": str(attempt["surcharge_cents"]),
                      "plan_id": str(plan_id) if plan_id else "", "charge_attempt_id": str(attempt["id"])})
        if pi.get("status") != "succeeded":
            retryable(attempt["id"])
            return None, "The card payment was not completed. Retry after resolving the payment with Stripe."
        try:
            fee = _stripe.fee_cents_for_payment_intent(pi["id"])
        except Exception:
            fee = 0
        return finish(attempt["id"], pi["id"], fee), None
    except Exception as exc:
        current_app.logger.exception("card collection %s awaits confirmation", attempt["id"])
        import stripe
        if isinstance(exc, stripe.CardError):
            db.session.rollback()
            db.session.execute(update(CardChargeAttempt).where(CardChargeAttempt.id == attempt["id"],
                               CardChargeAttempt.payment_id.is_(None)).values(state="failed", active_invoice_id=None))
            db.session.commit()
            return None, f"The card was not charged: {exc.user_message or 'The card was declined.'}"
        try:
            retryable(attempt["id"])
        except Exception:
            db.session.rollback()
        return None, "We could not confirm the card payment. Retry the same amount; the existing charge will be checked."


def reconcile_intent(pi):
    """Only called after Stripe signature verification. Ignore unrelated PaymentIntents."""
    raw = (pi.get("metadata") or {}).get("charge_attempt_id")
    if not raw or not str(raw).isdigit():
        return None
    attempt = db.session.get(CardChargeAttempt, int(raw))
    if not attempt:
        raise ValueError("Unknown card collection attempt")
    if (pi.get("status") != "succeeded" or pi.get("currency") != "usd"
            or pi.get("amount_received") != attempt.amount_cents + attempt.surcharge_cents
            or pi.get("customer") != attempt.customer_id):
        raise ValueError("Stripe payment does not match the collection attempt")
    try:
        fee = _stripe.fee_cents_for_payment_intent(pi.get("id")) if _stripe.configured() else 0
    except Exception:
        fee = 0
    return finish(attempt.id, pi.get("id"), fee)
