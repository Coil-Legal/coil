"""Offline recovery, migration and installment regression tests."""
from datetime import date, timedelta

import pytest

from tests.test_money_review import app, staff, invoice
from tests.helpers import post_stripe_event


@pytest.fixture
def provider(monkeypatch):
    from app.blueprints import _stripe
    monkeypatch.setattr(_stripe, "configured", lambda: True)
    monkeypatch.setattr(_stripe, "fee_cents_for_payment_intent", lambda _: 30)
    return _stripe


def test_lost_response_reuses_durable_attempt_and_provider_key(app, provider, monkeypatch):
    from app.extensions import db
    from app.models import CardChargeAttempt, Invoice, Payment
    iid, _ = invoice(app)
    client, csrf = staff(app)
    calls = []

    def charge(*args, **kw):
        calls.append(kw)
        if len(calls) == 1:
            raise TimeoutError("Response lost after the provider accepted the charge")
        return {"id": "pi_one_charge", "status": "succeeded"}

    monkeypatch.setattr(provider, "charge_payment_method", charge)
    data = {"_csrf": csrf, "amount": "100.00"}
    assert client.post(f"/money/charge/{iid}", data=data).status_code == 302
    with app.app_context():
        assert Payment.query.count() == 0
        assert CardChargeAttempt.query.one().state == "retry"
    assert client.post(f"/money/charge/{iid}", data=data).status_code == 302
    assert calls[0] == calls[1] and calls[0]["idempotency_key"]
    with app.app_context():
        assert Payment.query.count() == 1
        assert db.session.get(Invoice, iid).paid_cents == 10000
        assert CardChargeAttempt.query.one().state == "succeeded"


def test_webhook_repairs_failed_ledger_commit_once(app, provider, monkeypatch):
    from app.blueprints import collection_attempts as ca
    from app.extensions import db
    from app.models import CardChargeAttempt, Invoice, Payment
    iid, _ = invoice(app)
    client, csrf = staff(app)
    metadata = {}

    def charge(*args, **kw):
        metadata.update(kw["metadata"])
        return {"id": "pi_recovered", "status": "succeeded"}

    original_commit = db.session.commit
    fail = {"once": True}

    def commit():
        # The attempt reservation is committed first. Fail only the payment commit.
        if fail["once"] and any(isinstance(obj, Invoice) and obj.paid_cents for obj in db.session.dirty):
            fail["once"] = False
            raise RuntimeError("Synthetic commit failure")
        return original_commit()

    monkeypatch.setattr(provider, "charge_payment_method", charge)
    monkeypatch.setattr(db.session, "commit", commit)
    client.post(f"/money/charge/{iid}", data={"_csrf": csrf, "amount": "100.00"})
    assert fail["once"] is False
    with app.app_context():
        assert Payment.query.count() == 0
    payload = {"type": "payment_intent.succeeded", "data": {"object": {
        "id": "pi_recovered", "status": "succeeded", "currency": "usd", "amount_received": 10000,
        "customer": "cus_synthetic", "metadata": metadata}}}
    for _ in range(2):
        assert post_stripe_event(client, app, payload).status_code == 200
    with app.app_context():
        assert Payment.query.count() == 1
        assert db.session.get(Invoice, iid).status == "paid"
        assert CardChargeAttempt.query.one().state == "succeeded"


def test_old_uncertain_attempt_is_not_resubmitted_after_provider_key_expiry(app, provider, monkeypatch):
    from app.extensions import db
    from app.models import CardChargeAttempt, now
    iid, _ = invoice(app)
    client, csrf = staff(app)
    calls = []

    def charge(*args, **kw):
        calls.append(kw)
        raise TimeoutError("Uncertain result")

    monkeypatch.setattr(provider, "charge_payment_method", charge)
    data = {"_csrf": csrf, "amount": "100.00"}
    client.post(f"/money/charge/{iid}", data=data)
    with app.app_context():
        CardChargeAttempt.query.one().created_at = now() - timedelta(days=2)
        db.session.commit()
    response = client.post(f"/money/charge/{iid}", data=data, follow_redirects=True)
    assert len(calls) == 1 and b"needs reconciliation with Stripe" in response.data


def test_stale_partial_charge_form_does_not_collect_twice(app, provider, monkeypatch):
    from app.models import Payment
    iid, _ = invoice(app)
    client, csrf = staff(app)
    calls = []

    def charge(*args, **kw):
        calls.append(kw)
        return {"id": f"pi_partial_{len(calls)}", "status": "succeeded"}

    monkeypatch.setattr(provider, "charge_payment_method", charge)
    data = {"_csrf": csrf, "amount": "20.00", "paid_cents": "0"}
    client.post(f"/money/charge/{iid}", data=data)
    client.post(f"/money/charge/{iid}", data=data)
    assert len(calls) == 1
    with app.app_context():
        assert Payment.query.one().amount_cents == 2000


def test_installment_after_reminder_keeps_due_date_and_duplicate_delivery_progress(app, monkeypatch):
    from app.blueprints import money
    from app.extensions import db
    from app.models import PaymentPlan, Payment
    iid, _ = invoice(app)
    client, csrf = staff(app)
    first = date.today()
    response = client.post("/money/plans/new", data={"_csrf": csrf, "invoice_id": str(iid),
        "installments": "2", "frequency": "monthly", "first_charge_on": first.isoformat()})
    pid = int(response.location.rsplit("/", 1)[1])
    monkeypatch.setattr(money, "send_plan_reminder", lambda plan: "client@example.test")
    with app.app_context():
        assert money.run_payment_plans(first)["reminded"] == 1
        advanced = db.session.get(PaymentPlan, pid).next_charge_on
    for number in (1, 2):
        payload = {"type": "checkout.session.completed", "data": {"object": {
            "id": f"cs_installment_{number}", "mode": "payment", "payment_status": "paid",
            "payment_intent": f"pi_installment_{number}", "amount_total": 5000,
            "metadata": {"kind": "invoice", "invoice_id": str(iid), "plan_id": str(pid),
                         "installment": str(number), "installment_due_on": first.isoformat(),
                         "surcharge_cents": "0", "method": "card"}}}}
        for _ in range(2):
            assert post_stripe_event(client, app, payload).status_code == 200
        with app.app_context():
            plan = db.session.get(PaymentPlan, pid)
            assert plan.paid_installments == number
            assert Payment.query.count() == number
            if number == 1:
                assert plan.next_charge_on == advanced
            else:
                assert plan.status == "completed"
        first = advanced


def test_token_migration_expires_ambiguous_links_and_keeps_new_links_separate(app):
    from app.extensions import db
    from app.migrate import add_missing_columns
    from app.models import PortalToken, now
    with app.app_context():
        db.session.add(PortalToken(contact_id=1, token="old-ambiguous-token", expires_at=now() + timedelta(days=7)))
        db.session.commit()
        # Recreate the old schema in this disposable test database.
        db.session.remove()
        with db.engine.begin() as connection:
            connection.exec_driver_sql("ALTER TABLE portal_tokens DROP COLUMN purpose")
        from sqlalchemy import inspect
        assert "purpose" not in {c["name"] for c in inspect(db.engine).get_columns("portal_tokens")}
        result = add_missing_columns()
        assert "portal_tokens.purpose" in result
        assert add_missing_columns() == []
        assert PortalToken.query.one().purpose == "legacy"
        db.session.add(PortalToken(contact_id=1, token="new-login-token", expires_at=now() + timedelta(minutes=30)))
        db.session.commit()
    client = app.test_client()
    assert client.get("/portal/auth/old-ambiguous-token").status_code == 410
    assert client.get("/pay/card/old-ambiguous-token").status_code == 404
    assert client.get("/pay/card/new-login-token").status_code == 404
    assert client.get("/portal/auth/new-login-token").status_code == 302
    assert client.get("/portal/auth/new-login-token").status_code == 410


@pytest.mark.parametrize("amount", ["0", "invalid", "-10.00"])
def test_invalid_amount_never_defaults_to_full_balance(app, provider, monkeypatch, amount):
    from app.models import CardChargeAttempt
    iid, _ = invoice(app)
    client, csrf = staff(app)
    def unexpected(*args, **kwargs):
        pytest.fail("Invalid amount must not contact the payment provider")
    monkeypatch.setattr(provider, "charge_payment_method", unexpected)
    client.post(f"/money/charge/{iid}", data={"_csrf": csrf, "amount": amount})
    with app.app_context():
        assert CardChargeAttempt.query.count() == 0
