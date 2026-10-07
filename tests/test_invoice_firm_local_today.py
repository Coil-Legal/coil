"""Coil QA #147: invoices built in the evening in a US timezone were dated tomorrow.

The invoice builder, the agent API's invoice-create fallback, and the client statement date
all used date.today(), the server clock's date, which in production is UTC. A Chicago firm
(firm.timezone defaults to America/Chicago) invoicing at 7pm local time is already past
midnight UTC, so the prefilled issue date and the statement date were a day ahead of the
work they billed.

date.today() can't be monkeypatched directly (it's a method on an immutable builtin type),
so these tests fake the server's clock two ways that must agree, the way they would for a
real request: `date.today()` (used by the pre-fix, buggy code) returns the server's UTC
date, and `utcnow()` (used by firm_today(), the fix) returns the matching instant, so the
fix's conversion to America/Chicago lands on the day before.

Run: .venv/bin/python -m pytest tests/test_invoice_firm_local_today.py -q
"""
from datetime import date, datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

# 7:10pm America/Chicago (CDT, UTC-5) on Oct 6, 2026 is 00:10 UTC Oct 7: the server's raw
# date.today() is already tomorrow relative to the firm's own evening.
SERVER_UTC_DATE = date(2026, 10, 7)
UTC_INSTANT = datetime(2026, 10, 7, 0, 10)
FIRM_LOCAL_DATE = date(2026, 10, 6)


class _FakeDate(date):
    @classmethod
    def today(cls):
        return SERVER_UTC_DATE


def _freeze_evening(monkeypatch):
    monkeypatch.setattr("app.helpers.utcnow", lambda: UTC_INSTANT)
    for module in ("app.blueprints.invoices", "app.blueprints.api", "app.blueprints.statements"):
        monkeypatch.setattr(f"{module}.date", _FakeDate)


def test_firm_today_uses_the_firms_timezone_not_the_server_clock(app, monkeypatch):
    from app.helpers import firm_today
    _freeze_evening(monkeypatch)
    with app.app_context():
        assert firm_today() == FIRM_LOCAL_DATE


def test_invoice_builder_prefills_todays_date_in_the_firms_timezone(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    with app.app_context():
        from app.models import Matter
        matter_id = Matter.query.filter_by(number="M-PHASE1").one().id
    r = c.get(f"/invoices/new?matter_id={matter_id}")
    assert r.status_code == 200
    body = r.data.decode()
    assert 'name="issued_on" value="2026-10-06"' in body
    assert 'name="due_on" value="2026-11-05"' in body
    assert "2026-10-07" not in body


def test_invoice_create_fallback_issued_on_is_firm_local(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    with app.app_context():
        from app.models import Matter, TimeEntry
        from app.extensions import db
        matter_id = Matter.query.filter_by(number="M-PHASE1").one().id
        db.session.add(TimeEntry(matter_id=matter_id, user_id=1, date=date(2026, 10, 6), minutes=30,
                                 rate_cents=20000, description="Evening work", billable=True))
        db.session.commit()
        time_ids = [t.id for t in TimeEntry.query.filter_by(matter_id=matter_id, invoice_id=None).all()]
    r = c.post("/invoices/new", data={"matter_id": matter_id, "_csrf": csrf,
                                      "time_ids": time_ids, "issued_on": "", "due_on": ""})
    assert r.status_code == 302
    with app.app_context():
        from app.models import Invoice
        inv = Invoice.query.order_by(Invoice.id.desc()).first()
        assert inv.issued_on == FIRM_LOCAL_DATE
        assert inv.due_on == date(2026, 11, 5)


def test_agent_api_invoice_create_fallback_issued_on_is_firm_local(app, monkeypatch):
    from app.extensions import db
    from app.models import User, TimeEntry, Matter
    from app.blueprints.api import create_token
    _freeze_evening(monkeypatch)
    with app.app_context():
        matter_id = Matter.query.filter_by(number="M-PHASE1").one().id
        user = db.session.get(User, 1)
        _, raw = create_token(user, "QA #147 api", "invoices:write")
        db.session.add(TimeEntry(matter_id=matter_id, user_id=1, date=date(2026, 10, 6), minutes=30,
                                 rate_cents=20000, description="Evening API work", billable=True))
        db.session.commit()
    c = app.test_client()
    r = c.post("/api/v1/invoices", headers={"Authorization": f"Bearer {raw}"}, json={"matter_id": matter_id})
    assert r.status_code == 201
    with app.app_context():
        from app.models import Invoice
        inv = Invoice.query.order_by(Invoice.id.desc()).first()
        assert inv.issued_on == FIRM_LOCAL_DATE


def test_statement_date_is_firm_local(app, monkeypatch):
    _freeze_evening(monkeypatch)
    with app.app_context():
        from app.models import Contact
        from app.blueprints.statements import build_statement
        client = Contact.query.filter_by(email="client@example.test").one()
        st = build_statement(client)
        assert st["today"] == FIRM_LOCAL_DATE
