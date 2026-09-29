"""Payments list must not fold a non-USD payment's amount into a bare dollar figure (issue #80),
same defect class as #52/#53/#57/#75/#78/#79: a euro payment's row, the "Received" stat card and
the footer Total all used the plain `money` filter (always `$`)."""
from datetime import date
import re
import pytest
from app import create_app
from app.extensions import db
from app.models import Contact, Firm, Invoice, InvoiceLine, Matter, Payment, User
from tests.helpers import login


@pytest.fixture
def app(tmp_path):
    app = create_app(dict(TESTING=True, SECRET_KEY='synthetic-payments-list',
        SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'practice.db'),
        UPLOAD_DIR=str(tmp_path/'uploads'), PDF_DIR=str(tmp_path/'pdf'),
        SMTP_HOST='', STRIPE_SECRET_KEY=''))
    with app.app_context():
        user = User(id=1, email='qa@example.invalid', name='Synthetic QA')
        user.set_password('synthetic-pass')
        db.session.add_all([Firm(id=1), user, Contact(id=1, first_name='Synthetic')])
        db.session.flush()
        usd = Matter(id=1, client_id=1, number='QA-PAY-USD', name='Dollar matter', currency='USD')
        eur = Matter(id=2, client_id=1, number='QA-PAY-EUR', name='Euro matter', currency='EUR')
        db.session.add_all([usd, eur])
        db.session.flush()
        inv_usd = Invoice(id=1, number='QA-INV-USD', matter_id=1, client_id=1, status='sent',
                          issued_on=date.today(), currency='USD')
        inv_eur = Invoice(id=2, number='QA-INV-EUR', matter_id=2, client_id=1, status='sent',
                          issued_on=date.today(), currency='EUR')
        db.session.add_all([inv_usd, inv_eur])
        db.session.flush()
        db.session.add_all([
            InvoiceLine(invoice_id=1, description='Services', amount_cents=20000, kind='fee'),
            InvoiceLine(invoice_id=2, description='Services', amount_cents=5000, kind='fee'),
        ])
        db.session.flush()
        inv_usd.recalc()
        inv_eur.recalc()
        db.session.add_all([
            Payment(invoice_id=1, matter_id=1, client_id=1, amount_cents=20000, method='check',
                   account='operating', received_on=date.today()),
            Payment(invoice_id=2, matter_id=2, client_id=1, amount_cents=5000, method='check',
                   account='operating', received_on=date.today()),
        ])
        db.session.commit()
    return app


def test_payments_list_row_uses_its_own_currency(app):
    client = app.test_client(); login(client, 'qa@example.invalid', 'synthetic-pass')
    page = client.get('/payments?month=all').get_data(as_text=True)
    assert '€50.00' in page, page
    assert '$50.00' not in page, page


def test_payments_list_stat_card_and_total_keep_currencies_separate(app):
    client = app.test_client(); login(client, 'qa@example.invalid', 'synthetic-pass')
    page = client.get('/payments?month=all').get_data(as_text=True)
    value = re.search(r'Received, All time.*?<div class="value">([^<]+)</div>', page, re.S).group(1)
    assert value == '€50.00 + $200.00'
    total = re.search(r'<strong>Total</strong></td><td class="num"><strong>([^<]+)</strong>', page).group(1)
    assert total == '€50.00 + $200.00'
