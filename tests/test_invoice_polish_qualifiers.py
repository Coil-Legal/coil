"""Invoice suggestions must not silently lose limits or acquire timing/purpose claims."""
import json
from datetime import date
import pytest
from tests.test_zip_import_review import app, client

ORIGINAL = 'Reviewed the demand letter only. No strategy advice was provided. Client did not approve a settlement.'
BAD = 'The demand letter was reviewed. No strategic advice was provided to the client, and the client did not approve a settlement at this time.'

@pytest.fixture
def invoice(app):
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m=db.session.get(Matter,1)
        inv=Invoice(number='QA-POLISH',matter_id=m.id,client_id=m.client_id,status='draft')
        db.session.add(inv);db.session.flush()
        line=InvoiceLine(invoice_id=inv.id,kind='time',date=date(2026,9,22),description=ORIGINAL,quantity=.4,unit_cents=25000,amount_cents=10000)
        other=InvoiceLine(invoice_id=inv.id,kind='time',description='Reviewed file.',quantity=1,unit_cents=5000,amount_cents=5000)
        db.session.add_all([line,other]);db.session.flush();inv.recalc();db.session.commit()
        return inv.id,line.id,other.id


def test_preview_retains_original_and_explains_held_suggestion(app,client,invoice,monkeypatch):
    from app import llm
    inv,line,_=invoice
    monkeypatch.setattr(llm,'complete_json',lambda *a,**kw:{'lines':[{'id':line,'text':BAD}]})
    r=client.post(f'/ai/invoice/{inv}/polish',data={'_csrf':client.tok})
    assert r.status_code==200
    html=r.get_data(as_text=True)
    assert 'Original retained' in html
    from html.parser import HTMLParser
    class Textareas(HTMLParser):
        def __init__(self):super().__init__();self.name=None;self.values={}
        def handle_starttag(self,tag,attrs):
            if tag=='textarea':self.name=dict(attrs).get('name');self.values[self.name]=''
        def handle_endtag(self,tag):
            if tag=='textarea':self.name=None
        def handle_data(self,data):
            if self.name:self.values[self.name]+=data
    p=Textareas();p.feed(html)
    assert p.values[f'line_{line}']==ORIGINAL


def test_apply_rejects_changed_qualifiers_without_partial_updates(app,client,invoice):
    from app.extensions import db
    from app.models import Invoice,InvoiceLine,AuditLog
    inv,line,other=invoice
    r=client.post(f'/ai/invoice/{inv}/polish/apply',data={'_csrf':client.tok,f'line_{other}':'Reviewed the file.',f'line_{line}':BAD})
    assert r.status_code==200 and b'Original retained' in r.data
    with app.app_context():
        assert db.session.get(InvoiceLine,line).description==ORIGINAL
        assert db.session.get(InvoiceLine,other).description=='Reviewed file.'
        assert db.session.get(Invoice,inv).total_cents==15000
        assert AuditLog.query.filter_by(entity='invoice',entity_id=inv,action='update').count()==0

@pytest.mark.parametrize('before,after',[
    ('Reviewed demand strategy.','Reviewed demand strategy to determine the next steps.'),
    ('Client did not approve settlement.','Client approved settlement.'),
    ('No advice was provided.','Advice was provided.'),
    ('Reviewed the letter only.','Reviewed the letter.'),
    ('Client did not approve settlement.','Client did not approve settlement at this time.'),
    ('Settlement remains pending.','Settlement was reviewed.'),
])
def test_changed_qualifiers_are_detected(before,after):
    from app.blueprints.ai import _polish_warnings
    assert _polish_warnings(before,after)

@pytest.mark.parametrize('before,after',[
    ('tc w/ client re: settlement','Telephone call with the client regarding settlement.'),
    ('Reviewed the letter only.','Only the letter was reviewed.'),
    ('Client did not approve settlement.','Settlement was not approved by the client.'),
    ('Reviewed strategy to determine next steps.','The strategy was reviewed to determine next steps.'),
    (ORIGINAL,ORIGINAL),
])
def test_preserved_qualifiers_allow_cleanup(before,after):
    from app.blueprints.ai import _polish_warnings
    assert not _polish_warnings(before,after)
