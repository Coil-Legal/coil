"""Dashboard Unbilled time card must not fold a non-USD matter's time into a bare dollar total (issue #78)."""
from datetime import date
import re
import pytest
from app import create_app
from app.extensions import db
from app.models import Contact, Firm, Matter, TimeEntry, User
from tests.helpers import login

@pytest.fixture
def app(tmp_path):
    app = create_app(dict(TESTING=True, SECRET_KEY='synthetic-dashboard-wip',
        SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'practice.db'),
        UPLOAD_DIR=str(tmp_path/'uploads'), PDF_DIR=str(tmp_path/'pdf'),
        SMTP_HOST='', STRIPE_SECRET_KEY=''))
    with app.app_context():
        user = User(id=1, email='qa@example.invalid', name='Synthetic QA')
        user.set_password('synthetic-pass')
        db.session.add_all([Firm(id=1), user, Contact(id=1, first_name='Synthetic')])
        db.session.flush()
        db.session.add_all([
            Matter(id=1, client_id=1, number='QA-WIP-USD', name='Dollar matter', currency='USD'),
            Matter(id=2, client_id=1, number='QA-WIP-EUR', name='Euro matter', currency='EUR'),
        ])
        db.session.commit()
    return app


def unbilled_time(matter_id, minutes, rate_cents):
    db.session.add(TimeEntry(matter_id=matter_id, user_id=1, date=date.today(),
                             minutes=minutes, rate_cents=rate_cents, billable=True))
    db.session.commit()


def totals():
    from app.blueprints.dashboard import load_card_data
    return load_card_data(['wip'], db.session.get(User, 1), date.today())['wip_by_currency']


def test_dashboard_wip_keeps_each_currency_separate(app):
    with app.app_context():
        unbilled_time(1, 60, 20000)  # $200.00
        unbilled_time(2, 60, 20000)  # €200.00
        assert totals() == {'USD': 20000, 'EUR': 20000}
    client = app.test_client(); login(client, 'qa@example.invalid', 'synthetic-pass')
    page = client.get('/').get_data(as_text=True)
    value = re.search(r'data-card="wip">.*?<div class="value">([^<]+)</div>', page, re.S).group(1)
    assert value == '€200.00 + $200.00'


def test_dashboard_wip_matter_with_empty_currency_uses_firm_default(app):
    with app.app_context():
        db.session.get(Firm, 1).currency = 'GBP'
        db.session.execute(db.text("UPDATE matters SET currency='' WHERE id=1"))
        db.session.commit()
        unbilled_time(1, 60, 20000)  # £200.00, via firm default
        assert totals() == {'GBP': 20000}


def test_dashboard_wip_invoiced_and_non_billable_time_excluded(app):
    with app.app_context():
        assert totals() == {}
        db.session.add(TimeEntry(matter_id=1, user_id=1, date=date.today(),
                                 minutes=60, rate_cents=10000, billable=False))
        db.session.commit()
        assert totals() == {}
