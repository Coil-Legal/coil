"""Dashboard A/R must match invoice balances after issued credits."""
from datetime import date
import re
import pytest
from app import create_app
from app.extensions import db
from app.models import Contact, CreditNote, Firm, Invoice, Matter, User
from tests.helpers import login

@pytest.fixture
def app(tmp_path):
    app = create_app(dict(TESTING=True, SECRET_KEY='synthetic-dashboard-credit',
        SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'practice.db'),
        UPLOAD_DIR=str(tmp_path/'uploads'), PDF_DIR=str(tmp_path/'pdf'),
        SMTP_HOST='', STRIPE_SECRET_KEY=''))
    with app.app_context():
        user = User(id=1, email='qa@example.invalid', name='Synthetic QA')
        user.set_password('synthetic-pass')
        db.session.add_all([Firm(id=1), user, Contact(id=1, first_name='Synthetic')])
        db.session.flush()
        db.session.add(Matter(id=1, client_id=1, number='QA-AR-CREDIT', name='Synthetic credits'))
        db.session.commit()
    return app


def invoice(number, total, paid=0, currency='USD', status='partial', credits=()):
    inv = Invoice(number=number, matter_id=1, client_id=1, total_cents=total,
                  paid_cents=paid, currency=currency, status=status)
    db.session.add(inv)
    db.session.flush()
    for i, (amount, state) in enumerate(credits):
        db.session.add(CreditNote(number=number+'-CN-'+str(i), invoice_id=inv.id,
            client_id=1, matter_id=1, total_cents=amount, status=state))
    db.session.commit()
    return inv


def totals():
    from app.blueprints.dashboard import load_card_data
    return load_card_data(['ar'], db.session.get(User, 1), date.today())['ar_by_currency']


def test_dashboard_subtracts_multiple_issued_credits_once_and_ignores_void(app):
    with app.app_context():
        invoice('USD', 10001, 2501, credits=[(1000,'issued'),(500,'issued'),(900,'void')])
        invoice('GBP', 100, currency='GBP', credits=[(50,'issued')])
        invoice('EUR', 200, currency='EUR')
        assert totals() == {'USD':6000, 'GBP':50, 'EUR':200}
        expected = {}
        for inv in Invoice.query.all():
            expected[inv.currency] = expected.get(inv.currency,0) + inv.balance_cents
        assert totals() == expected
    client = app.test_client(); login(client, 'qa@example.invalid', 'synthetic-pass')
    page = client.get('/').get_data(as_text=True)
    value = re.search(r'data-card="ar">.*?<div class="value">([^<]+)</div>',page,re.S).group(1)
    assert value == '€2.00 + £0.50 + $60.00'


@pytest.mark.parametrize("overpayment", [False, True])
def test_each_invoice_is_clamped_before_aggregation(app, overpayment):
    with app.app_context():
        if overpayment:
            invoice('overpaid',100,200)
        else:
            invoice('overcredit',100,credits=[(200,'issued')])
        invoice('open',100)
        assert totals() == {'USD':100}


def test_legacy_null_paid_amount_matches_invoice_balance(app):
    with app.app_context():
        inv = invoice('legacy',100,credits=[(25,'issued')])
        db.session.execute(db.text('UPDATE invoices SET paid_cents=NULL WHERE id=:id'),{'id':inv.id})
        db.session.commit()
        assert totals() == {'USD':75}


def test_closed_invoice_statuses_do_not_contribute(app):
    with app.app_context():
        for status in ('draft','void','paid'):
            invoice(status,9000,status=status,credits=[(1000,'issued')])
        assert totals() == {}
