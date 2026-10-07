"""Coil QA #175: a client statement's "Balance due" figure (the stat card, the PDF summary
box, the PDF's bottom "Balance due" line, and the emailed statement's totals) was built from
`totals["balance"]`/`totals_cur["balance"]`, a sum over only the in-period ("shown") invoices.
With a From date after every invoice's own date, every invoice dropped out of that sum and the
client was told they owed $0.00, even though the Activity table's own "Balance forward" and
"Totals Balance" rows (built from the running `opening`/`closing` balance, not from groups)
correctly showed the full amount still owed.

Balance due has to reflect every currently open invoice regardless of the statement's own
period filter, since it is a present-tense fact ("what does this client owe right now"), not a
period total.

Run: .venv/bin/python -m pytest tests/test_statement_balance_due_ignores_period_filter.py -q
"""
from datetime import date, timedelta

from tests.test_phase1_independent import app, staff  # noqa: F401


def _two_open_invoices(app):
    from app.extensions import db
    from app.models import Matter, Invoice, InvoiceLine, Payment

    with app.app_context():
        m = Matter.query.first()
        today = date.today()
        inv1 = Invoice(number="BD-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                       currency="USD", issued_on=today)
        inv1.lines.append(InvoiceLine(description="Services", amount_cents=20000))
        inv1.payments.append(Payment(matter_id=m.id, client_id=m.client_id, amount_cents=7500,
                                     method="check", received_on=today))
        inv2 = Invoice(number="BD-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                       currency="USD", issued_on=today)
        inv2.lines.append(InvoiceLine(description="Services", amount_cents=15000))
        db.session.add(inv1)
        db.session.add(inv2)
        db.session.flush()
        inv1.recalc()
        inv2.recalc()
        db.session.commit()
        return m.client_id, today


def test_balance_due_counts_open_invoices_from_before_the_period(app):
    from app.models import Contact
    from app.extensions import db
    from app.blueprints.statements import build_statement

    client_id, today = _two_open_invoices(app)
    with app.app_context():
        client = db.session.get(Contact, client_id)
        # A From date after both invoices: the Activity table shows no in-period rows, but the
        # client still owes $125.00 (inv1) + $150.00 (inv2) = $275.00.
        st = build_statement(client, d_from=today + timedelta(days=1))
        assert st["invoices"] == []
        assert st["totals"]["balance"] == 27500
        assert st["totals_cur"]["balance"] == {"USD": 27500}
        assert st["closing"] == 27500


def test_statement_page_balance_due_card_matches(app):
    client_id, today = _two_open_invoices(app)
    c, _csrf = staff(app)
    body = c.get(f"/statements/{client_id}?from={(today + timedelta(days=1)).isoformat()}").data.decode()
    card = body[body.index("Balance due"):body.index("Balance due") + 100]
    assert '<div class="value">$275.00</div>' in card
