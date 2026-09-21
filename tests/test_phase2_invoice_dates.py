"""Agent invoice drafts must not silently substitute dates supplied by the caller."""
from datetime import date
import pytest
from tests.test_phase1_independent import app


def invoice_client(app):
    from app.extensions import db
    from app.models import User, TimeEntry
    from app.blueprints.api import create_token
    with app.app_context():
        user = db.session.get(User, 1)
        _, raw = create_token(user, 'QA invoice dates', 'invoices:write,invoices:read')
        db.session.add(TimeEntry(matter_id=1, user_id=1, date=date(2026, 1, 2), minutes=30,
                                rate_cents=20000, description='Synthetic review', billable=True))
        db.session.commit()
    return app.test_client(), {'Authorization': f'Bearer {raw}'}


@pytest.mark.parametrize('field,value', [
    ('issued_on', 'not-a-date'), ('due_on', '2026-02-30'), ('issued_on', '2026-01-02garbage'),
    ('due_on', 20260102), ('issued_on', {'year': 2026}),
])
def test_invalid_invoice_date_refused_before_billing_sources(app, field, value):
    from app.models import Invoice, TimeEntry
    client, headers = invoice_client(app)
    response = client.post('/api/v1/invoices', headers=headers, json={'matter_id': 1, field: value})
    assert response.status_code == 400
    assert field in response.json['error']
    with app.app_context():
        assert Invoice.query.count() == 0
        assert TimeEntry.query.one().invoice_id is None


def test_valid_invoice_dates_and_amount_are_preserved(app):
    from app.models import Invoice
    client, headers = invoice_client(app)
    response = client.post('/api/v1/invoices', headers=headers,
                           json={'matter_id': 1, 'issued_on': '2026-01-02', 'due_on': '2026-02-01'})
    assert response.status_code == 201
    with app.app_context():
        invoice = Invoice.query.one()
        assert invoice.issued_on == date(2026, 1, 2) and invoice.due_on == date(2026, 2, 1)
        assert invoice.status == 'draft' and invoice.total_cents == 10000
