"""A shared party name must not clear an unverified opposing party."""
from html import unescape
import pytest
from tests.test_zip_import_review import app, client
from app.blueprints import _courtlistener as cl

CITE='384 U.S. 436'

def provider_row(source, actual):
    return {'citation':CITE,'status':200,'start_index':source.index(CITE),
            'clusters':[{'id':107252,'case_name':actual,'date_filed':'1966-06-13'}]}

@pytest.mark.parametrize('claimed,actual',[
    ('Zyx v. Arizona','Miranda v. Arizona'),
    ('Miranda v. Qwerty','Miranda v. Arizona'),
    ('Arizona v. Miranda','Miranda v. Arizona'),
    ('United States v. Zyx','United States v. Jones'),
    ('State v. Qwerty','State v. Jones'),
    ('Miranda v. Arizona','Miranda'),
])
def test_partial_party_match_is_held_for_review(monkeypatch,claimed,actual):
    source=f'{claimed}, {CITE}'
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:{'ok':True,'data':[provider_row(source,actual)]})
    row=cl.citation_lookup(source)['citations'][0]
    assert row['resolution']=='name_uncertain'
    assert row['name_uncertain'] and not row['found'] and not row['name_mismatch']

@pytest.mark.parametrize('claimed,actual',[
    ('Miranda v. Arizona','Miranda v. Arizona'),
    ('Celotex Corp. v. Catrett','Celotex Corp. v. Catrett, Administratrix of the Estate'),
    ('Matsushita Elec. Indus. Co. v. Zenith Radio Corp.','Matsushita Electric Industrial Co. v. Zenith Radio Corp.'),
    ('Anderson v. Liberty Lobby','Anderson v. Liberty Lobby, Inc.'),
])
def test_two_party_name_variants_keep_database_match(monkeypatch,claimed,actual):
    source=f'{claimed}, {CITE}'
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:{'ok':True,'data':[provider_row(source,actual)]})
    row=cl.citation_lookup(source)['citations'][0]
    assert row['resolution']=='resolved' and row['found']

def test_partial_names_remain_reviewable_in_page_note_and_audit(app,client,monkeypatch):
    from app.models import Note,AuditLog
    names=['Miranda v. Arizona','Zyx v. Arizona','Miranda v. Qwerty','Zyx v. Qwerty']
    source='\n'.join(f'{name}, {CITE}.' for name in names)
    positions=[i for i in range(len(source)) if source.startswith(CITE,i)]
    rows=[dict(provider_row(source,'Miranda v. Arizona'),start_index=i) for i in positions]
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:{'ok':True,'data':rows})
    response=client.post('/research/cite-check',data={'_csrf':client.tok,'text':source,'matter_id':1})
    html=unescape(response.get_data(as_text=True))
    assert response.status_code==200
    assert '1 resolved' in html and '2 case names needing review' in html
    assert html.count('case name needs review</span>')==2
    assert 'wrong case, do not file' in html
    with app.app_context():
        body=Note.query.one().body
        assert body.startswith('[internal]') and '1 resolved' in body
        assert body.count('CASE NAME NEEDS REVIEW')==2 and '2 case names needing review' in body
        assert 'Zyx v. Arizona' in body and 'Miranda v. Qwerty' in body
        assert '2 case names needing review' in AuditLog.query.filter_by(entity='note').one().detail
