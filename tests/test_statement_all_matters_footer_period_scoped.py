"""Coil QA #177: #175 made the statement stat card's "Balance due" account-wide (every open
invoice, ignoring the From/To filter). The By-matter table's "All matters" footer row kept
reading that same account-wide `totals_cur["balance"]` next to its own period-scoped Total/Paid
columns and the period-scoped matter subtotal rows above it, so the footer didn't add up to
what the table actually listed.

The footer should use a period-scoped balance (the sum of the shown matter subtotals), same as
its Total and Paid columns. The stat card keeps the account-wide figure, with its own note.

Run: .venv/bin/python -m pytest tests/test_statement_all_matters_footer_period_scoped.py -q
"""
from datetime import date

from tests.test_phase1_independent import app, staff  # noqa: F401


def _client_with_old_and_new_invoice(app):
    from app.extensions import db
    from app.models import Matter, Invoice, InvoiceLine

    with app.app_context():
        m = Matter.query.first()
        old_inv = Invoice(number="AM-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                          currency="USD", issued_on=date(2026, 9, 1))
        old_inv.lines.append(InvoiceLine(description="Services", amount_cents=10000))
        new_inv = Invoice(number="AM-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                          currency="USD", issued_on=date(2026, 10, 7))
        new_inv.lines.append(InvoiceLine(description="Services", amount_cents=5000))
        db.session.add(old_inv)
        db.session.add(new_inv)
        db.session.flush()
        old_inv.recalc()
        new_inv.recalc()
        db.session.commit()
        return m.client_id


def test_period_balance_sums_only_the_shown_groups(app):
    from app.models import Contact
    from app.extensions import db
    from app.blueprints.statements import build_statement

    client_id = _client_with_old_and_new_invoice(app)
    with app.app_context():
        client = db.session.get(Contact, client_id)
        # From date after the old invoice: only the new $50.00 invoice is in period, but the
        # account owes $150.00 across both.
        st = build_statement(client, d_from=date(2026, 10, 2))
        assert len(st["groups"]) == 1
        assert st["groups"][0]["balance"] == 5000
        assert st["totals"]["period_balance"] == 5000
        assert st["totals_cur"]["period_balance"] == {"USD": 5000}
        assert st["totals"]["balance"] == 15000
        assert st["totals_cur"]["balance"] == {"USD": 15000}


def test_statement_page_all_matters_footer_matches_shown_subtotals(app):
    client_id = _client_with_old_and_new_invoice(app)
    c, _csrf = staff(app)
    body = c.get(f"/statements/{client_id}?from=2026-10-02").data.decode()
    marker = ">All matters</th>"
    footer = body[body.index(marker):body.index(marker) + 300]
    assert "$50.00" in footer
    assert "$150.00" not in footer
    assert '<div class="value">$150.00</div>' in body
