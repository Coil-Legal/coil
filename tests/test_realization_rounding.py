"""Collected realization must conserve an invoice's allocated receipt cents."""
from datetime import date
import csv
import io

import pytest
from tests.test_phase1_independent import app, staff


def paid_time(app, amounts, payment, currency='EUR', expense=0):
    from app.extensions import db
    from app.models import Matter, TimeEntry, Invoice, InvoiceLine, Payment
    with app.app_context():
        matter = db.session.get(Matter, 1)
        matter.currency = currency
        invoice = Invoice(number='QA-REAL-ROUND', client_id=1, matter_id=1,
                          currency=currency, status='partial', issued_on=date(2026, 9, 1))
        db.session.add(invoice); db.session.flush()
        ids = []
        for index, cents in enumerate(amounts):
            entry = TimeEntry(matter_id=1, user_id=(index % 2)+1, date=date(2026, 9, index+1),
                              minutes=60, rate_cents=cents, billable=True, invoice_id=invoice.id)
            db.session.add(entry); db.session.flush(); ids.append(entry.id)
            db.session.add(InvoiceLine(invoice_id=invoice.id, kind='time', time_entry_id=entry.id,
                                       amount_cents=cents, sort=index, description='Synthetic time'))
        if expense:
            db.session.add(InvoiceLine(invoice_id=invoice.id, kind='expense', amount_cents=expense,
                                       sort=99, description='Synthetic expense'))
        db.session.add(Payment(invoice_id=invoice.id, client_id=1, matter_id=1,
                               amount_cents=payment, method='check', received_on=date(2026,9,10)))
        db.session.flush();invoice.recalc();db.session.commit()
        return ids


@pytest.mark.parametrize('amounts,payment,expected', [([1,1],1,1),([1,1,1],2,2)])
def test_partial_receipt_cents_are_not_lost_or_invented(app, amounts, payment, expected):
    from app.blueprints.reports import realization_data
    paid_time(app, amounts, payment)
    with app.app_context():
        users,matters,total=realization_data(date(2026,9,1),date(2026,9,30))
        assert total['collected']=={'EUR':expected}
        assert sum(r['collected'].get('EUR',0) for r in users)==expected
        assert matters[0]['collected']==expected


def test_date_windows_use_the_same_receipt_allocation(app):
    from app.blueprints.reports import realization_data
    paid_time(app,[1,1],1)
    with app.app_context():
        days=[realization_data(date(2026,9,n),date(2026,9,n))[2]['collected']['EUR'] for n in [1,2]]
        assert days==[1,0]
        assert sum(days)==realization_data(date(2026,9,1),date(2026,9,30))[2]['collected']['EUR']==1


def test_expense_share_is_not_reclassified_as_collected_time(app):
    from app.blueprints.reports import realization_data
    paid_time(app,[1,1],2,expense=2)
    with app.app_context():
        assert realization_data(date(2026,9,1),date(2026,9,30))[2]['collected']=={'EUR':1}


def test_csv_matches_collected_receipt_cents(app):
    paid_time(app,[1,1],1)
    client,_=staff(app)
    response=client.get('/reports/realization?from=2026-09-01&to=2026-09-30&format=csv')
    assert response.status_code==200
    rows=list(csv.DictReader(io.StringIO(response.data.decode('utf-8-sig'))))
    totals=[r for r in rows if r['Group']=='total']
    assert len(totals)==1 and totals[0]['Currency']=='EUR'
    assert totals[0]['Collected']=='0.01'


def test_legacy_entries_without_source_lines_conserve_cents(app):
    from app.extensions import db
    from app.models import InvoiceLine
    from app.blueprints.reports import realization_data
    paid_time(app,[1,1],1)
    with app.app_context():
        for line in InvoiceLine.query.all():
            line.time_entry_id=None
        db.session.commit()
        assert realization_data(date(2026,9,1),date(2026,9,30))[2]['collected']=={'EUR':1}


def test_split_payer_receipts_are_allocated_separately(app):
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Payment
    from app.blueprints.reports import realization_data
    paid_time(app,[1,1],1)
    with app.app_context():
        first=Invoice.query.one();first.split_group='QA-ROUND-SPLIT'
        second=Invoice(number='QA-ROUND-SECOND',client_id=1,matter_id=1,currency='EUR',
                       status='partial',split_group=first.split_group)
        db.session.add(second);db.session.flush()
        for index in range(2):
            db.session.add(InvoiceLine(invoice_id=second.id,kind='time',amount_cents=1,
                                       sort=index,description='Copied split time'))
        db.session.add(Payment(invoice_id=second.id,client_id=1,matter_id=1,
                               amount_cents=1,method='check'))
        db.session.flush();second.recalc();db.session.commit()
        assert realization_data(date(2026,9,1),date(2026,9,30))[2]['collected']=={'EUR':2}


def test_full_payment_and_void_invoice_control(app):
    from app.extensions import db
    from app.models import Invoice
    from app.blueprints.reports import realization_data
    paid_time(app,[1,2],3)
    with app.app_context():
        assert realization_data(date(2026,9,1),date(2026,9,30))[2]['collected']=={'EUR':3}
        Invoice.query.one().status='void';db.session.commit()
        assert realization_data(date(2026,9,1),date(2026,9,30))[2]['collected']=={'EUR':0}
