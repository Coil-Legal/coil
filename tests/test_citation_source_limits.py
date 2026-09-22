"""The search index's page/byte limits must not produce a partial citation pass."""
import io
from pathlib import Path
import pytest
from fpdf import FPDF
from tests.test_zip_import_review import app, client


def pdf(pages):
    doc=FPDF(); doc.set_font('Helvetica',size=12)
    for n in range(1,pages+1):
        doc.add_page()
        doc.text(15,20,'Miranda v. Arizona, 384 U.S. 436.' if n==1 else
                 'Zyx v. Qwerty, 384 U.S. 436.' if n==pages else 'Synthetic page '+str(n))
    return bytes(doc.output())


def upload(client,name,data):
    r=client.post('/documents/upload',data={'_csrf':client.tok,'matter_id':1,
                                         'file':(io.BytesIO(data),name)})
    assert r.status_code==302


@pytest.mark.parametrize('kind',['pdf','text'])
def test_partial_extraction_is_stopped_before_provider_or_saved_note(app,client,monkeypatch,kind):
    from app.blueprints import _courtlistener as cl
    from app.models import Document,Note
    from app.extensions import db
    raw=pdf(201) if kind=='pdf' else b'Miranda v. Arizona, 384 U.S. 436.'+b' '*400000+b'Zyx v. Qwerty, 384 U.S. 436.'
    upload(client,'source.pdf' if kind=='pdf' else 'source.txt',raw)
    calls=[]
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:calls.append(a) or {'ok':True,'data':[]})
    with app.app_context():
        d=Document.query.one();did=d.id
        assert 'Miranda' in d.extracted_text and 'Qwerty' not in d.extracted_text
        assert len(d.extracted_text)<64000
        before={col.name:getattr(d,col.name) for col in Document.__table__.columns}
        path=Path(app.config['UPLOAD_DIR'])/d.path
        n=Note(matter_id=1,body='[internal] Existing reference result');db.session.add(n);db.session.commit();nid=n.id
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did})
    assert r.status_code==200
    html=r.get_data(as_text=True)
    assert 'Document text may be incomplete' in html and 'No citation lookup was sent' in html
    assert ('201 pages' if kind=='pdf' else '400,000-byte') in html
    assert 'CourtListener is not answering' not in html and 'No case citations were recognised' not in html
    assert calls==[]
    with app.app_context():
        assert Note.query.count()==1 and db.session.get(Note,nid).body=='[internal] Existing reference result'
        d=db.session.get(Document,did)
        assert {col.name:getattr(d,col.name) for col in Document.__table__.columns}==before
        assert path.read_bytes()==raw


@pytest.mark.parametrize('kind',['pdf','text'])
def test_exact_extraction_boundary_still_checks_ending_text(app,client,monkeypatch,kind):
    from app.blueprints import _courtlistener as cl
    from app.models import Document,Note
    raw=pdf(200) if kind=='pdf' else b' '*(400000-len(b'Zyx v. Qwerty, 384 U.S. 436.'))+b'Zyx v. Qwerty, 384 U.S. 436.'
    upload(client,'boundary.pdf' if kind=='pdf' else 'boundary.txt',raw)
    sent=[]
    def post(path,data):
        sent.append(data['text']);return {'ok':True,'data':[]}
    monkeypatch.setattr(cl,'_post',post)
    with app.app_context(): did=Document.query.one().id
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did})
    assert r.status_code==200 and len(sent)==1 and 'Qwerty' in sent[0]
    with app.app_context():assert Note.query.one().body.startswith('[internal]')


@pytest.mark.parametrize('broken',['missing','unreadable'])
def test_unverifiable_pdf_is_stopped(app,client,monkeypatch,broken):
    from app.blueprints import _courtlistener as cl
    from app.models import Document,Note
    upload(client,'source.pdf',pdf(2))
    with app.app_context():
        d=Document.query.one();did=d.id;path=Path(app.config['UPLOAD_DIR'])/d.path
        if broken=='missing':path.unlink()
        else:path.write_bytes(b'%PDF-unreadable')
    calls=[];monkeypatch.setattr(cl,'_post',lambda *a,**kw:calls.append(a) or {'ok':True,'data':[]})
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did})
    assert r.status_code==200 and b'original file could not be read' in r.data and not calls
    with app.app_context():assert Note.query.count()==0


def test_pasted_text_overrides_selected_long_document(app,client,monkeypatch):
    from app.blueprints import _courtlistener as cl
    from app.models import Document
    upload(client,'long.pdf',pdf(201))
    with app.app_context():did=Document.query.one().id
    sent=[];monkeypatch.setattr(cl,'_post',lambda path,data:sent.append(data['text']) or {'ok':True,'data':[]})
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did,'text':'384 U.S. 436'})
    assert r.status_code==200 and sent==['384 U.S. 436']


def test_pdf_raw_character_cap_cannot_be_hidden_by_whitespace(app,client,monkeypatch):
    from app.blueprints import _courtlistener as cl
    from app.models import Document,Note
    upload(client,'whitespace.pdf',pdf(2))
    with app.app_context():did=Document.query.one().id
    class Page:
        def extract_text(self):return 'Miranda v. Arizona, 384 U.S. 436.'+' '*200000
    class Reader:
        pages=[Page(),Page()]
        def __init__(self,path):pass
    monkeypatch.setattr('pypdf.PdfReader',Reader)
    calls=[];monkeypatch.setattr(cl,'_post',lambda *a,**kw:calls.append(a) or {'ok':True,'data':[]})
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did})
    assert r.status_code==200 and b'before whitespace is normalized' in r.data and not calls
    with app.app_context():assert Note.query.count()==0
