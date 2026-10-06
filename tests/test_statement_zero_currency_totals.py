"""Issue #129: a client statement's "Paid or applied" card listed every invoice currency even
at zero (totals_cur.paid is seeded per invoice currency, including zero amounts), but its own
sub-line and the Activity Totals row only got a currency key once a real payment existed, so an
all-unpaid EUR+GBP client saw "$0.00 received in period" instead of "€0.00 + £0.00": the wrong
symbol, same bug class as #125, just at zero. Seeding payments/credits/payments_and_credits with
the statement's own invoice currencies (at zero) makes every per-currency total on the page use
the same rule.

Run: .venv/bin/python -m pytest tests/test_statement_zero_currency_totals.py -q
"""
from datetime import date

from tests.test_phase1_independent import app  # noqa: F401


def fixture_two_currency_client(app):
    from app.extensions import db
    from app.models import Contact, Matter, Invoice, InvoiceLine, Payment
    with app.app_context():
        m = Matter.query.first()
        eur = Invoice(number="ZC-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                     currency="EUR", issued_on=date.today())
        eur.lines.append(InvoiceLine(description="Services", amount_cents=30000))
        gbp = Invoice(number="ZC-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                     currency="GBP", issued_on=date.today())
        gbp.lines.append(InvoiceLine(description="Services", amount_cents=25000))
        db.session.add(eur)
        db.session.add(gbp)
        db.session.flush()
        eur.recalc()
        gbp.recalc()
        db.session.commit()
        return m.client_id, eur.id


def statement(app, **kwargs):
    from app.models import Contact
    from app.extensions import db
    from app.blueprints.statements import build_statement
    return build_statement(db.session.get(Contact, 1), **kwargs)


def test_unpaid_mixed_currency_statement_has_no_usd_fallback(app):
    fixture_two_currency_client(app)
    with app.app_context():
        st = statement(app)
        assert st["totals_cur"]["paid"] == {"EUR": 0, "GBP": 0}
        assert st["totals_cur"]["payments"] == {"EUR": 0, "GBP": 0}
        assert st["totals_cur"]["credits"] == {"EUR": 0, "GBP": 0}
        assert st["totals_cur"]["payments_and_credits"] == {"EUR": 0, "GBP": 0}


def test_partial_payment_keeps_the_unpaid_currency_in_the_payments_total(app):
    from app.extensions import db
    from app.models import Payment
    client_id, eur_id = fixture_two_currency_client(app)
    with app.app_context():
        db.session.add(Payment(invoice_id=eur_id, client_id=client_id, matter_id=1,
                               amount_cents=10000, method="check", received_on=date.today()))
        db.session.commit()
        from app.models import Invoice
        db.session.get(Invoice, eur_id).recalc()
        db.session.commit()
        st = statement(app)
        assert st["totals_cur"]["payments"] == {"EUR": 10000, "GBP": 0}
        assert st["totals_cur"]["payments_and_credits"] == {"EUR": 10000, "GBP": 0}
