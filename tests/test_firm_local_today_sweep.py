"""Coil QA #153/#155/#156: #147 fixed the invoice builder, the statement date and the payment
'Recorded' line to use the firm's timezone instead of the server's raw UTC date, but several
other places that build or display a date the same way were not touched and kept defaulting
to date.today()/the plain `dt` filter: new time entries and expenses, a new matter's opened_on,
a manual payment's Received field, the invoice Activity list, a new payment plan's first
charge and its Created/Next/due badge, and /trust/new, /trust/reconcile and the reconciliation
report's "Prepared by" line.

Frozen instant: 7:10pm America/Chicago (CDT, UTC-5) on Oct 6, 2026 is 00:10 UTC Oct 7, so the
server's own clock is already a calendar day ahead of the firm's evening.

Run: .venv/bin/python -m pytest tests/test_firm_local_today_sweep.py -q
"""
from datetime import date, datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

SERVER_UTC_DATE = date(2026, 10, 7)
UTC_INSTANT = datetime(2026, 10, 7, 0, 10)
FIRM_LOCAL_DATE = date(2026, 10, 6)
FIRM_LOCAL_ISO = "2026-10-06"

# This suite's own machine runs on Central time already, same as #147's test file found, so a
# plain monkeypatch of app.helpers.utcnow alone would make pre-fix date.today() calls land on
# the right day by coincidence and hide the bug. Also fake date.today() in every module this
# sweep touches, to the server's raw UTC date, exactly as the real Docker deployment sees it.
_FAKE_DATE_MODULES = ("app.blueprints.time", "app.blueprints.matters", "app.blueprints.payments",
                     "app.blueprints.money", "app.blueprints.trust", "app.blueprints.invoices",
                     "app.blueprints.api")


class _FakeDate(date):
    @classmethod
    def today(cls):
        return SERVER_UTC_DATE


class _FakeDateTime(datetime):
    @classmethod
    def now(cls, tz=None):
        return UTC_INSTANT.replace(tzinfo=tz) if tz else UTC_INSTANT


def _freeze_evening(monkeypatch):
    monkeypatch.setattr("app.helpers.utcnow", lambda: UTC_INSTANT)
    # created_at columns default to app.models.now(), which reads datetime.now(timezone.utc)
    # directly, no path through app.helpers.utcnow or the per-module date patches below. Column
    # defaults capture that function object at class-definition time, so monkeypatching the
    # app.models.now *name* doesn't reach it; app.models.now's own body still does a fresh global
    # lookup of `datetime` on every call, so patching that name here does.
    monkeypatch.setattr("app.models.datetime", _FakeDateTime)
    for module in _FAKE_DATE_MODULES:
        monkeypatch.setattr(f"{module}.date", _FakeDate)


def _matter_id(app):
    with app.app_context():
        from app.models import Matter
        return Matter.query.filter_by(number="M-PHASE1").one().id


# ---- time entries and expenses (#156) ----
def test_time_entry_new_prefills_firm_local_date(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    r = c.get("/time/new")
    assert r.status_code == 200
    body = r.data.decode()
    assert f'value="{FIRM_LOCAL_ISO}"' in body
    assert "2026-10-07" not in body


def test_time_entry_create_without_date_field_falls_back_to_firm_local(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    _freeze_evening(monkeypatch)
    r = c.post("/time/new", data={"matter_id": matter_id, "duration": "1.0",
                                 "description": "evening work", "_csrf": csrf})
    assert r.status_code == 302
    with app.app_context():
        from app.models import TimeEntry
        entry = TimeEntry.query.order_by(TimeEntry.id.desc()).first()
        assert entry.date == FIRM_LOCAL_DATE


def test_timer_stop_logs_firm_local_date(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    c.post("/time/timer/start", data={"matter_id": matter_id, "_csrf": csrf})
    _freeze_evening(monkeypatch)
    r = c.post("/time/timer/stop", data={"matter_id": matter_id, "_csrf": csrf})
    assert r.status_code == 302
    with app.app_context():
        from app.models import TimeEntry
        entry = TimeEntry.query.order_by(TimeEntry.id.desc()).first()
        assert entry.date == FIRM_LOCAL_DATE


def test_expense_new_prefills_firm_local_date(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    r = c.get("/time/expenses/new")
    assert r.status_code == 200
    body = r.data.decode()
    assert f'value="{FIRM_LOCAL_ISO}"' in body
    assert "2026-10-07" not in body


# ---- matters (#156) ----
def test_matter_new_prefills_firm_local_opened_on(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    r = c.get("/matters/new")
    assert r.status_code == 200
    body = r.data.decode()
    assert f'value="{FIRM_LOCAL_ISO}"' in body
    assert "2026-10-07" not in body


def test_matter_close_stamps_firm_local_closed_on(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    _freeze_evening(monkeypatch)
    r = c.post(f"/matters/{matter_id}/close", data={"_csrf": csrf})
    assert r.status_code == 302
    with app.app_context():
        from app.models import Matter
        m = app_get_matter(matter_id)
        assert m.closed_on == FIRM_LOCAL_DATE


def app_get_matter(matter_id):
    from app.extensions import db
    from app.models import Matter
    return db.session.get(Matter, matter_id)


# ---- manual payment Received field (#156) ----
def test_manual_payment_received_on_falls_back_to_firm_local(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    _freeze_evening(monkeypatch)
    with app.app_context():
        from app.extensions import db
        from app.models import Invoice, InvoiceLine
        inv = Invoice(matter_id=matter_id, client_id=1, status="sent", issued_on=FIRM_LOCAL_DATE,
                     due_on=FIRM_LOCAL_DATE, currency="USD")
        inv.lines.append(InvoiceLine(kind="fee", description="work", quantity=1.0, unit_cents=10000,
                                     amount_cents=10000, sort=1))
        db.session.add(inv)
        db.session.commit()
        inv.recalc()
        db.session.commit()
        inv_id = inv.id
    r = c.post("/payments/record", data={"invoice_id": inv_id, "amount": "50.00", "method": "check",
                                         "_csrf": csrf})
    assert r.status_code == 302
    with app.app_context():
        from app.models import Payment
        p = Payment.query.filter_by(invoice_id=inv_id).order_by(Payment.id.desc()).first()
        assert p.received_on == FIRM_LOCAL_DATE


def test_invoice_detail_prefills_received_on_and_first_charge_firm_local(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    with app.app_context():
        from app.extensions import db
        from app.models import Invoice, InvoiceLine
        inv = Invoice(matter_id=matter_id, client_id=1, status="sent", issued_on=FIRM_LOCAL_DATE,
                     due_on=FIRM_LOCAL_DATE, currency="USD")
        inv.lines.append(InvoiceLine(kind="fee", description="work", quantity=1.0, unit_cents=10000,
                                     amount_cents=10000, sort=1))
        db.session.add(inv)
        db.session.commit()
        inv.recalc()
        db.session.commit()
        inv_id = inv.id
    _freeze_evening(monkeypatch)
    r = c.get(f"/invoices/{inv_id}")
    assert r.status_code == 200
    body = r.data.decode()
    assert f'name="received_on" value="{FIRM_LOCAL_ISO}"' in body
    assert f'name="first_charge_on" value="{FIRM_LOCAL_ISO}"' in body
    assert "2026-10-07" not in body


def test_invoice_activity_timestamp_uses_firm_local_time(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    # The "sent" event's own created_at is the firm-local timestamp under test, so it must be
    # inserted after the freeze, not before; a pre-freeze insert stamps the real wall clock.
    _freeze_evening(monkeypatch)
    with app.app_context():
        from app.extensions import db
        from app.models import Invoice, InvoiceLine, InvoiceEvent
        inv = Invoice(matter_id=matter_id, client_id=1, status="draft", issued_on=FIRM_LOCAL_DATE,
                     due_on=FIRM_LOCAL_DATE, currency="USD")
        inv.lines.append(InvoiceLine(kind="fee", description="work", quantity=1.0, unit_cents=10000,
                                     amount_cents=10000, sort=1))
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceEvent(invoice_id=inv.id, event="sent"))
        db.session.commit()
        inv_id = inv.id
    r = c.get(f"/invoices/{inv_id}")
    assert r.status_code == 200
    body = r.data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body


# ---- payment plans (#153) ----
def test_plan_detail_created_next_and_due_badge_are_firm_local(app, monkeypatch):
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    with app.app_context():
        from app.extensions import db
        from app.models import Invoice, InvoiceLine
        inv = Invoice(matter_id=matter_id, client_id=1, status="sent", issued_on=FIRM_LOCAL_DATE,
                     due_on=FIRM_LOCAL_DATE, currency="USD")
        inv.lines.append(InvoiceLine(kind="fee", description="work", quantity=1.0, unit_cents=60000,
                                     amount_cents=60000, sort=1))
        db.session.add(inv)
        db.session.commit()
        inv.recalc()
        db.session.commit()
        inv_id = inv.id
    _freeze_evening(monkeypatch)
    r = c.post("/money/plans/new", data={"invoice_id": inv_id, "installments": "3", "frequency": "monthly",
                                         "first_charge_on": FIRM_LOCAL_ISO, "_csrf": csrf})
    assert r.status_code == 302
    with app.app_context():
        from app.models import PaymentPlan
        plan = PaymentPlan.query.filter_by(invoice_id=inv_id).one()
        plan_id = plan.id
    r = c.get(f"/money/plans/{plan_id}")
    body = r.data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body


# ---- trust (#155) ----
def test_trust_new_prefills_firm_local_date(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    r = c.get("/trust/new")
    assert r.status_code == 200
    body = r.data.decode()
    assert f'value="{FIRM_LOCAL_ISO}"' in body
    assert "2026-10-07" not in body


def test_trust_reconcile_prefills_firm_local_period_end(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    r = c.get("/trust/reconcile")
    assert r.status_code == 200
    body = r.data.decode()
    assert f'value="{FIRM_LOCAL_ISO}"' in body
    assert "2026-10-07" not in body


def test_trust_reconcile_report_prepared_on_is_firm_local(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    r = c.post("/trust/reconcile", data={"period_end": FIRM_LOCAL_ISO, "bank_statement": "0.00", "_csrf": csrf})
    assert r.status_code == 302
    r = c.get(r.headers["Location"])
    assert r.status_code == 200
    body = r.data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body


def test_trust_apply_as_of_matches_invoice_detail_card(app, monkeypatch):
    """#143 made the invoice detail card and /trust/apply agree on what is available 'as of
    today'; both must still use the same (now firm-local) today or that class of bug returns."""
    c, csrf = staff(app)
    matter_id = _matter_id(app)
    with app.app_context():
        from app.extensions import db
        from app.models import Invoice, InvoiceLine, TrustTransaction
        inv = Invoice(matter_id=matter_id, client_id=1, status="sent", issued_on=FIRM_LOCAL_DATE,
                     due_on=FIRM_LOCAL_DATE, currency="USD")
        inv.lines.append(InvoiceLine(kind="fee", description="work", quantity=1.0, unit_cents=10000,
                                     amount_cents=10000, sort=1))
        db.session.add(inv)
        # Deposited "tomorrow" (server UTC date, not yet the firm's today): not on hand yet.
        db.session.add(TrustTransaction(client_id=1, matter_id=matter_id, date=date(2026, 10, 7),
                                        type="deposit", amount_cents=10000, description="post-dated"))
        db.session.commit()
        inv.recalc()
        db.session.commit()
        inv_id = inv.id
    _freeze_evening(monkeypatch)
    r = c.get(f"/invoices/{inv_id}")
    assert r.status_code == 200
    assert "apply_default=0" not in r.data.decode()  # sanity: template rendered, not an error page
    r = c.post("/trust/apply", data={"invoice_id": inv_id, "amount": "100.00", "_csrf": csrf})
    assert r.status_code == 302
    r = c.get(r.headers["Location"])
    body = r.data.decode()
    assert "dated after today" in body or "dated later" in body or "Only $0.00" in body
