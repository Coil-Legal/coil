"""Coil QA #181: a statement PDF saved after 7pm Central was named for tomorrow.

_filename() in app/blueprints/statements.py built the Content-Disposition filename with
date.today(), the server clock's date (UTC in production), while the PDF body already used
firm_today() (the #147 fix). A Chicago firm downloading a statement in the evening got a
file named for the next day even though the PDF itself, correctly, said today.

Uses the same frozen-evening fixture as test_invoice_firm_local_today.py: date.today()
(what the buggy code read) returns the server's UTC date, utcnow() (what firm_today() reads)
returns the matching instant, and the fix's conversion to America/Chicago lands on the day
before.

Run: .venv/bin/python -m pytest tests/test_statement_pdf_filename_firm_local.py -q
"""
from datetime import date, datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

SERVER_UTC_DATE = date(2026, 10, 9)
UTC_INSTANT = datetime(2026, 10, 9, 0, 51)
FIRM_LOCAL_DATE = date(2026, 10, 8)


class _FakeDate(date):
    @classmethod
    def today(cls):
        return SERVER_UTC_DATE


def _freeze_evening(monkeypatch):
    monkeypatch.setattr("app.helpers.utcnow", lambda: UTC_INSTANT)
    monkeypatch.setattr("app.blueprints.statements.date", _FakeDate)


def test_statement_pdf_filename_is_firm_local_not_server_utc(app, monkeypatch):
    c, csrf = staff(app)
    _freeze_evening(monkeypatch)
    with app.app_context():
        from app.models import Contact
        client = Contact.query.filter_by(email="client@example.test").one()
        client_id = client.id
    r = c.get(f"/statements/{client_id}/pdf")
    assert r.status_code == 200
    disposition = r.headers["Content-Disposition"]
    assert f"-{FIRM_LOCAL_DATE.isoformat()}.pdf" in disposition
    assert SERVER_UTC_DATE.isoformat() not in disposition
