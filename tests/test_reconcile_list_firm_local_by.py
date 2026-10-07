"""Coil QA #162: /trust/reconcile's "Past reconciliations" table read a row's created_at with
the plain `d` filter (naive UTC date), while reconcile_report.html's own "Prepared by" line
already converts to the firm's timezone via `dtlocal` (#147's class, see
test_firm_local_today_sweep.py). A reconciliation prepared in the evening Central time, after
7pm, has a UTC created_at that has already rolled to the next calendar day, so the list
disagreed with the report it links to by one day.

Run: .venv/bin/python -m pytest tests/test_reconcile_list_firm_local_by.py -q
"""
from datetime import date, datetime

from tests.test_phase1_independent import app, staff  # noqa: F401


def test_past_reconciliations_by_date_matches_report_date(app):
    from app.extensions import db
    from app.models import TrustReconciliation

    c, _csrf = staff(app)
    with app.app_context():
        # 8:56pm Central (CDT, UTC-5) on Oct 6, 2026 is 01:56 UTC Oct 7: the server's naive
        # created_at has already rolled to the next day while the firm's evening has not.
        r = TrustReconciliation(period_end=date(2026, 11, 1), balanced=True,
                                book_balance_cents=0, bank_statement_cents=0,
                                client_ledgers_cents=0, adjusted_bank_cents=0)
        db.session.add(r)
        db.session.flush()
        r.created_at = datetime(2026, 10, 7, 1, 56)
        db.session.commit()
        rid = r.id

    report = c.get(f"/trust/reconcile/{rid}").data.decode()
    assert "Prepared by" in report and "Oct 6, 2026" in report

    listing = c.get("/trust/reconcile").data.decode()
    assert "Oct 6, 2026" in listing
    assert "Oct 7, 2026" not in listing
