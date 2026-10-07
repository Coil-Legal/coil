"""Coil QA #157: POST /api/v1/invoices defaulted due_on to the issue date when omitted,
ignoring the firm's invoice_terms_days. The UI builder (invoices.py new()/bulk()) has always
defaulted due_on to issued_on + invoice_terms_days; the agent API's own fallback instead reused
whatever issued_on resolved to, so an API-created invoice with no dates was due the day it was
issued instead of after the firm's normal payment window.

Run: .venv/bin/python -m pytest tests/test_api_invoice_due_on_default.py -q
"""
from datetime import date, timedelta

from tests.test_phase1_independent import app, staff  # noqa: F401


def _token(app):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token
    with app.app_context():
        user = db.session.get(User, 1)
        _, raw = create_token(user, "QA #157 api", "invoices:write")
        db.session.commit()
    return raw


def test_due_on_defaults_to_issued_on_plus_invoice_terms_days(app):
    from app.extensions import db
    from app.models import Matter, TimeEntry, Firm
    raw = _token(app)
    with app.app_context():
        matter_id = Matter.query.filter_by(number="M-PHASE1").one().id
        terms_days = Firm.get().invoice_terms_days
        db.session.add(TimeEntry(matter_id=matter_id, user_id=1, date=date.today(), minutes=30,
                                 rate_cents=20000, description="API due_on default", billable=True))
        db.session.commit()
    c = app.test_client()
    r = c.post("/api/v1/invoices", headers={"Authorization": f"Bearer {raw}"}, json={"matter_id": matter_id})
    assert r.status_code == 201
    with app.app_context():
        from app.models import Invoice
        inv = Invoice.query.order_by(Invoice.id.desc()).first()
        assert inv.due_on == inv.issued_on + timedelta(days=terms_days)
        assert inv.due_on != inv.issued_on


def test_due_on_still_honors_an_explicit_value(app):
    from app.extensions import db
    from app.models import Matter, TimeEntry
    raw = _token(app)
    with app.app_context():
        matter_id = Matter.query.filter_by(number="M-PHASE1").one().id
        db.session.add(TimeEntry(matter_id=matter_id, user_id=1, date=date.today(), minutes=30,
                                 rate_cents=20000, description="API explicit due_on", billable=True))
        db.session.commit()
    c = app.test_client()
    r = c.post("/api/v1/invoices", headers={"Authorization": f"Bearer {raw}"},
               json={"matter_id": matter_id, "issued_on": "2026-01-01", "due_on": "2026-01-15"})
    assert r.status_code == 201
    with app.app_context():
        from app.models import Invoice
        inv = Invoice.query.order_by(Invoice.id.desc()).first()
        assert inv.issued_on == date(2026, 1, 1)
        assert inv.due_on == date(2026, 1, 15)
