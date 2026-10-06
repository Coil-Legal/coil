"""Two payment-plan defects filed as Coil QA #121 and #122.

#121: advance_date() clamped a monthly step to the *previous result's* day of month instead of
the plan's original anchor day, so one short-month clamp (e.g. Jan 31 -> Feb 29) carried forward
into every later row even once a month had enough days to honor the real anchor again.

#122: the refusal flash for an action on a plan in the wrong status built the past participle by
stripping the "plan_" prefix off the action id and appending a bare "d" ("cancel" + "d" =
"canceld"), which only looked right for verbs that already end in "e" (paused, resumed).
"""
from datetime import date

from tests.test_phase1_independent import app, staff


def _plan(app_, due, installments=3, status="active", installment_cents=10000):
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, PaymentPlan
    with app_.app_context():
        inv = Invoice(number=f"INV-PLAN-{due.isoformat()}-{status}", matter_id=1, client_id=1, kind="hourly",
                      status="sent", issued_on=due, due_on=due)
        inv.lines.append(InvoiceLine(kind="time", description="Work", quantity=1.0,
                                     unit_cents=installment_cents * installments,
                                     amount_cents=installment_cents * installments, sort=1))
        db.session.add(inv)
        db.session.flush()
        inv.recalc()
        plan = PaymentPlan(invoice_id=inv.id, contact_id=1, installment_cents=installment_cents,
                           installments=installments, paid_installments=0, frequency="monthly",
                           next_charge_on=due, installment_due_on=due, auto_charge=False, status=status)
        db.session.add(plan)
        db.session.commit()
        return plan.id


def test_monthly_plan_schedule_keeps_the_original_anchor_day_after_a_leap_clamp(app):
    from app.extensions import db
    from app.models import PaymentPlan
    from app.blueprints.money import plan_schedule
    plan_id = _plan(app, date(2028, 1, 31))
    with app.app_context():
        plan = db.session.get(PaymentPlan, plan_id)
        dates = [d for _, d, _, _ in plan_schedule(plan)]
    assert dates == [date(2028, 1, 31), date(2028, 2, 29), date(2028, 3, 31)]


def test_cancel_refusal_spells_cancelled_correctly(app):
    plan_id = _plan(app, date.today(), status="completed")
    c, csrf = staff(app)
    r = c.post(f"/money/plans/{plan_id}/cancel", data={"_csrf": csrf}, follow_redirects=True)
    assert b"cannot be cancelled from there" in r.data
    assert b"canceld" not in r.data
