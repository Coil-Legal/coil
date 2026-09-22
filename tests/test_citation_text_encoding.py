"""Citation checking must not trust text created by dropping undecodable bytes."""
import io
from pathlib import Path
import pytest
from tests.test_zip_import_review import app, client
from app.blueprints import _courtlistener as cl
from app.models import Document, Note, AuditLog

@pytest.mark.parametrize('raw', [
    b'Miranda v. Arizo\xf1na, 384 U.S. 436.',
    'Miranda v. Arizona, 384 U.S. 436.'.encode('utf-16'),
    'Miranda v. Arizona, 384 U.S. 436.'.encode('utf-16-le'),
    'Miranda v. Arizona, 384 U.S. 436.'.encode('utf-32'),
    b'Miranda v. Ari\x00zona, 384 U.S. 436.',
])
def test_unsupported_encoding_stops_lookup_and_note(app, client, monkeypatch, raw):
    r=client.post('/documents/upload',data={'_csrf':client.tok,'matter_id':1,
        'file':(io.BytesIO(raw),'encoding.txt')})
    assert r.status_code==302
    with app.app_context():
        d=Document.query.one(); did=d.id
        before={c.name:getattr(d,c.name) for c in Document.__table__.columns}
        path=Path(app.config['UPLOAD_DIR'])/d.path
        audit_count=AuditLog.query.count()
    calls=[]
    monkeypatch.setattr(cl,'_post',lambda *a,**kw:calls.append(kw) or {'ok':True,'data':[]})
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did})
    assert r.status_code==200
    assert b'UTF-8' in r.data and b'No citation lookup was sent' in r.data
    assert calls==[]
    with app.app_context():
        assert Note.query.count()==0 and AuditLog.query.count()==audit_count
        d=Document.query.one()
        assert {c.name:getattr(d,c.name) for c in Document.__table__.columns}==before
        assert path.read_bytes()==raw

@pytest.mark.parametrize('raw', [
    'José reviewed Miranda v. Arizona, 384 U.S. 436.'.encode('utf-8'),
    'José reviewed Miranda v. Arizona, 384 U.S. 436.'.encode('utf-8-sig'),
])
def test_valid_utf8_still_checks_and_saves(app,client,monkeypatch,raw):
    r=client.post('/documents/upload',data={'_csrf':client.tok,'matter_id':1,
        'file':(io.BytesIO(raw),'utf8.txt')})
    assert r.status_code==302
    with app.app_context():did=Document.query.one().id
    calls=[]
    monkeypatch.setattr(cl,'_post',lambda path,data:calls.append(data['text']) or {'ok':True,'data':[]})
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did})
    assert r.status_code==200 and len(calls)==1 and 'José' in calls[0]
    with app.app_context():assert Note.query.one().body.startswith('[internal]')

def test_complete_paste_overrides_unsupported_file(app,client,monkeypatch):
    client.post('/documents/upload',data={'_csrf':client.tok,'matter_id':1,
        'file':(io.BytesIO(b'Arizo\xf1na'),'unsupported.txt')})
    with app.app_context():did=Document.query.one().id
    sent=[]
    monkeypatch.setattr(cl,'_post',lambda path,data:sent.append(data['text']) or {'ok':True,'data':[]})
    source='Miranda v. Arizona, 384 U.S. 436.'
    r=client.post('/research/cite-check',data={'_csrf':client.tok,'document_id':did,'text':source})
    assert r.status_code==200 and sent==[source]
