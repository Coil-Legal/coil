"""Issued credits reconcile statements without being counted as money received."""
from datetime import date
import io

import pytest
from pypdf import PdfReader
from tests.test_phase1_independent import app, staff


def fixture_invoice(app, number='QA-STMT-1', client_id=1, matter_id=1, status='sent'):
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Payment, CreditNote
    with app.app_context():
        inv = Invoice(number=number, client_id=client_id, matter_id=matter_id,
                      status=status, currency='USD', issued_on=date(2026, 1, 1))
        inv.lines.append(InvoiceLine(description='Synthetic services', amount_cents=10001))
        inv.payments.append(Payment(client_id=client_id, matter_id=matter_id, amount_cents=2501,
                                    method='check', reference='QA-STMT', received_on=date(2026, 1, 2)))
        inv.credit_notes.append(CreditNote(number='CN-'+number, client_id=client_id,
                                          matter_id=matter_id, total_cents=1000,
                                          issued_on=date(2026, 1, 3), status='issued'))
        db.session.add(inv)
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id


def statement(app, **kwargs):
    from app.models import Contact
    from app.extensions import db
    from app.blueprints.statements import build_statement
    return build_statement(db.session.get(Contact, 1), **kwargs)


def test_issued_credit_reconciles_without_inflating_payments(app):
    fixture_invoice(app)
    with app.app_context():
        st = statement(app)
        assert st['closing'] == st['totals']['balance'] == 6500
        assert [e['balance'] for e in st['entries']] == [10001, 7500, 6500]
        assert st['entries'][-1]['description'] == 'Credit note CN-QA-STMT-1 on QA-STMT-1'
        assert st['totals']['payments'] == st['totals']['paid'] == 2501
        assert st['totals']['credits'] == st['totals']['credited'] == 1000


@pytest.mark.parametrize('start,end,opening,closing,has_credit', [
    (date(2026,1,3), None, 7500, 6500, True),
    (date(2026,1,4), None, 6500, 6500, False),
    (None, date(2026,1,2), 0, 7500, False),
    (date(2026,1,3), date(2026,1,3), 7500, 6500, True),
])
def test_credit_date_controls_opening_and_activity(app, start,end,opening,closing,has_credit):
    fixture_invoice(app)
    with app.app_context():
        st = statement(app, d_from=start, d_to=end)
        assert st['opening'] == opening
        assert st['closing'] == closing
        assert any(e['kind']=='credit_note' for e in st['entries']) == has_credit
        assert st['totals']['credits'] == (1000 if has_credit else 0)


def test_void_credits_and_other_clients_matters_and_drafts_are_excluded(app):
    from app.extensions import db
    from app.models import Contact, Matter, CreditNote
    fixture_invoice(app)
    with app.app_context():
        db.session.add(Contact(id=2, first_name='Other', last_name='Synthetic'))
        db.session.add_all([Matter(id=2,number='QA-OTHER',client_id=1,name='Other matter'),
                            Matter(id=3,number='QA-CLIENT',client_id=2,name='Other client')])
        db.session.commit()
    fixture_invoice(app,'OTHER-MATTER',matter_id=2)
    fixture_invoice(app,'OTHER-CLIENT',client_id=2,matter_id=3)
    fixture_invoice(app,'DRAFT',status='draft')
    fixture_invoice(app,'VOID',status='void')
    with app.app_context():
        st=statement(app,matter_id=1)
        assert st['closing']==6500
        assert [e['description'] for e in st['entries'] if e['kind']=='credit_note']==['Credit note CN-QA-STMT-1 on QA-STMT-1']
        CreditNote.query.filter_by(number='CN-QA-STMT-1').one().status='void'
        db.session.commit()
        st=statement(app,matter_id=1)
        assert st['closing']==7500
        assert st['totals']['credits']==0
        assert not any(e['kind']=='credit_note' for e in st['entries'])


def test_html_pdf_and_mocked_email_show_credit_separately(app, monkeypatch, tmp_path):
    fixture_invoice(app)
    client,csrf=staff(app)
    html=client.get('/statements/1?matter_id=1').get_data(as_text=True)
    assert 'Credit note CN-QA-STMT-1 on QA-STMT-1' in html
    assert 'Payment / credit' in html
    assert '$25.01 received in period' in html
    assert '$10.00 credited' in html
    pdf=client.get('/statements/1/pdf?matter_id=1')
    assert pdf.status_code==200
    text='\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.data)).pages)
    assert 'Credit note CN-QA-STMT-1 on' in text
    assert '$65.00' in text and 'Credited' in text
    captured=[]
    monkeypatch.setattr('app.blueprints.statements.send_email',lambda *a,**k:captured.append((a,k)))
    result=client.post('/statements/1/send',data={'_csrf':csrf,'matter_id':'1'})
    assert result.status_code==302 and len(captured)==1
    args,kwargs=captured[0]
    assert 'Credited' in args[2] and '$10.00' in args[2]
    assert 'Paid: $25.01' in kwargs['text'] and 'Credited: $10.00' in kwargs['text']
    attachment=kwargs['attachments'][0][1]
    assert 'CN-QA-STMT-1' in '\n'.join(p.extract_text() for p in PdfReader(io.BytesIO(attachment)).pages)
