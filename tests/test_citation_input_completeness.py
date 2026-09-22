"""Never report a citation check after silently discarding the end of its source."""
from pathlib import Path
from html import unescape
import pytest
from tests.test_zip_import_review import app, client


def oversized():
    return 'Synthetic narrative. '*3300+'\nEnd citation: 999 QA 123.'


@pytest.mark.parametrize('document_input',[False,True])
def test_oversized_source_stops_before_provider_or_note(app,client,monkeypatch,document_input):
    from app.blueprints import _courtlistener as cl
    from app.extensions import db
    from app.models import Document,Note
    text=oversized();calls=[]
    def post(*args,**kwargs):
        calls.append((args,kwargs));return {'ok':True,'data':[]}
    monkeypatch.setattr(cl,'_post',post)
    form={'_csrf':client.tok,'matter_id':'1','text':text}
    with app.app_context():
        original_notes=Note.query.count()
        if document_input:
            path=Path(app.config['UPLOAD_DIR'])/'synthetic-long.txt';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            d=Document(matter_id=1,name='Synthetic long source',path=path.name,extracted_text=text)
            db.session.add(d);db.session.commit();did=d.id
            form.update(text='',document_id=str(did))
    response=client.post('/research/cite-check',data=form)
    assert response.status_code==200
    assert calls==[], 'Oversized input must never be clipped and checked as if complete'
    html=unescape(response.get_data(as_text=True))
    assert 'Text is too long to check' in html and '64,000' in html
    assert 'No citation lookup was sent' in html and 'No result note was saved' in html
    assert 'CourtListener is not answering' not in html
    assert 'No case citations were recognised' not in html and 'Saved as a note on' not in html
    with app.app_context():
        assert Note.query.count()==original_notes
        if document_input:
            assert db.session.get(Document,did).extracted_text==text
            assert path.read_text()==text
        else:
            draft=html.split('name="text"',1)[1].split('>',1)[1].split('</textarea>',1)[0]
            assert draft==text


def test_exact_limit_is_sent_in_full(monkeypatch):
    from app.blueprints import _courtlistener as cl
    text='a'*(cl.CITE_TEXT_CAP-len(' 999 QA 123.'))+' 999 QA 123.'
    sent=[]
    def post(path,data):
        sent.append(data['text']);return {'ok':True,'data':[]}
    monkeypatch.setattr(cl,'_post',post)
    assert cl.citation_lookup(text)['ok']
    assert sent==[text]


def test_direct_client_rejects_one_character_over_limit(monkeypatch):
    from app.blueprints import _courtlistener as cl
    calls=[]
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:calls.append(a) or {'ok':True,'data':[]})
    result=cl.citation_lookup('a'*(cl.CITE_TEXT_CAP+1))
    assert not result['ok'] and result['error']=='input_too_long'
    assert calls==[]


def test_valid_result_can_still_save_internal_note(app,client,monkeypatch):
    from app.blueprints import _courtlistener as cl
    from app.models import Note
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:{'ok':True,'data':[{'citation':'999 QA 123','status':404,'clusters':[]}]})
    response=client.post('/research/cite-check',data={'_csrf':client.tok,'matter_id':1,'text':'999 QA 123'})
    assert response.status_code==200 and b'not found, verify before filing' in response.data
    with app.app_context():
        note=Note.query.one();assert note.body.startswith('[internal]') and '999 QA 123' in note.body


def test_case_name_parser_does_not_restart_inside_long_tokens():
    import time
    from app.blueprints import _courtlistener as cl
    text='A'*64000+'; Synthetic v. Example, 999 QA 123.'
    start=time.monotonic()
    claims=cl._claimed_names(text)
    assert time.monotonic()-start < 2.0
    assert [name for _,name in claims]==['Synthetic v. Example']
