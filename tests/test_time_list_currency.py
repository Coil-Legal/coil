"""QA issue #83: the time list footer (Totals/Unbilled) summed every matching row into one
bare-dollar figure, folding a EUR matter's time into a USD total, same defect class as #60/#61.
Fix keeps the footer totals split per currency via `curmix`, like the invoice/payment list tabs.

Run: .venv/bin/python -m pytest tests/test_time_list_currency.py -q
"""
from datetime import date
import re
import pytest
from app import create_app
from app.extensions import db
from app.models import Contact, Firm, Matter, TimeEntry, User
from tests.helpers import login


@pytest.fixture
def app(tmp_path):
    app = create_app(dict(TESTING=True, SECRET_KEY='synthetic-time-list',
        SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'practice.db'),
        UPLOAD_DIR=str(tmp_path/'uploads'), PDF_DIR=str(tmp_path/'pdf'),
        SMTP_HOST='', STRIPE_SECRET_KEY=''))
    with app.app_context():
        user = User(id=1, email='qa@example.invalid', name='Synthetic QA')
        user.set_password('synthetic-pass')
        db.session.add_all([Firm(id=1), user, Contact(id=1, first_name='Synthetic')])
        db.session.flush()
        db.session.add_all([
            Matter(id=1, client_id=1, number='QA-TL-USD', name='Dollar matter', currency='USD'),
            Matter(id=2, client_id=1, number='QA-TL-EUR', name='Euro matter', currency='EUR'),
        ])
        db.session.add_all([
            TimeEntry(matter_id=1, user_id=1, date=date.today(), minutes=60, rate_cents=20000, billable=True),
            TimeEntry(matter_id=2, user_id=1, date=date.today(), minutes=60, rate_cents=20000, billable=True),
        ])
        db.session.commit()
    return app


@pytest.fixture
def client(app):
    c = app.test_client()
    login(c, 'qa@example.invalid', 'synthetic-pass')
    return c


def _totals_row(page):
    m = re.search(r'<tr><th colspan="4">Totals.*?</tr>', page, re.S)
    assert m, page
    return m.group(0)


def test_time_list_totals_keep_each_currency_separate(client):
    row = _totals_row(client.get('/time').get_data(as_text=True))
    assert '€200.00 + $200.00' in row, row
    assert 'Unbilled: €200.00 + $200.00' in row, row
    assert '$400.00' not in row, row


def test_time_list_single_matter_filter_still_shows_bare_currency(client):
    row = _totals_row(client.get('/time?matter_id=2').get_data(as_text=True))
    assert 'Unbilled: €200.00' in row, row
    assert '$' not in row, row
