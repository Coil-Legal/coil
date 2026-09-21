"""Synthetic ZIP batching, transaction and worker-exit acceptance checks."""
import io
import json
import os
import subprocess
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest
from tests.test_phase1_independent import app, staff
from tests.test_import_resume import step
from tests.test_importer import _commit


def upload(c, csrf, count=5):
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        for i in range(count):
            z.writestr(f'M-PHASE1/synthetic-{i}.txt',f'Synthetic document {i}')
    response=c.post('/import/documents/upload',data={'_csrf':csrf,'source':'generic',
        'file':(io.BytesIO(buf.getvalue()),'batch.zip')})
    assert response.status_code==302 and '/preview/' in response.location
    return response.location.rsplit('/',1)[-1]


def start(app,monkeypatch,count=5):
    from app.blueprints import importer
    monkeypatch.setattr(importer,'ZIP_BATCH_FILES',2,raising=False)
    c,csrf=staff(app);token=upload(c,csrf,count)
    response=c.post('/import/preview/'+token,data={'_csrf':csrf,'do':'commit'})
    assert response.status_code==302 and '/jobs/' in response.location
    return c,csrf,token,int(response.location.rsplit('/',1)[-1])


def state(app,jid):
    from app.extensions import db
    from app.models import ImportJob,Document
    with app.app_context():
        j=db.session.get(ImportJob,jid)
        return j.status,json.loads(j.mapping_json),j.created,Document.query.count(),j.errors


def files(app):
    return [p for p in Path(app.config['UPLOAD_DIR']).glob('*/*') if p.parent.name!='imports' and p.is_file()]


def test_zip_starts_without_importing_and_resumes_once(app,monkeypatch):
    c,csrf,token,jid=start(app,monkeypatch)
    assert state(app,jid)[0]=='running' and state(app,jid)[3]==0
    assert step(c,csrf,jid,0).json['processed']==2
    assert step(c,csrf,jid,0).json['processed']==2
    assert step(c,csrf,jid,2).json['processed']==4
    assert step(c,csrf,jid,4).json['done']
    assert step(c,csrf,jid,4).json['done']
    assert state(app,jid)[2:4]==(5,5) and len(files(app))==5
    repeat=c.post('/import/preview/'+token,data={'_csrf':csrf,'do':'commit'})
    assert repeat.location.endswith('/jobs/'+str(jid))


def test_failed_document_save_does_not_leave_a_file(app,monkeypatch):
    from app.blueprints import documents
    original=documents.store_bytes
    def fail(*args,**kwargs):
        original(*args,**kwargs)
        raise ValueError('Synthetic failure after writing document')
    monkeypatch.setattr(documents,'store_bytes',fail)
    c,csrf=staff(app);c.tok=csrf
    jid=_commit(c,upload(c,csrf,1))
    assert len(state(app,jid)[4])==1
    assert files(app)==[]


def test_two_start_requests_and_same_cursor_are_idempotent(app,monkeypatch):
    from app.blueprints import importer
    monkeypatch.setattr(importer,'ZIP_BATCH_FILES',2,raising=False)
    c,csrf=staff(app);token=upload(c,csrf)
    pairs=[staff(app),staff(app)];barrier=Barrier(2)
    def begin(pair):
        client,tok=pair;barrier.wait(timeout=10)
        r=client.post('/import/preview/'+token,data={'_csrf':tok,'do':'commit'})
        assert r.status_code==302
        return int(r.location.rsplit('/',1)[-1])
    with ThreadPoolExecutor(max_workers=2) as pool: ids=list(pool.map(begin,pairs))
    assert ids[0]==ids[1]
    assert state(app,ids[0])[0]=='running'
    barrier=Barrier(2)
    def batch(pair):
        client,tok=pair;barrier.wait(timeout=10)
        r=step(client,tok,ids[0],0)
        return r.status_code,r.json
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(batch,pairs))
    assert all(code==200 and body['processed']==2 for code,body in results)
    assert state(app,ids[0])[2:4]==(2,2) and len(files(app))==2


def test_final_checkpoint_failure_rolls_back_and_cleans_files(app,monkeypatch):
    from app.blueprints import importer
    c,csrf,token,jid=start(app,monkeypatch,3)
    assert step(c,csrf,jid,0).json['processed']==2
    original=importer.audit
    def fail(*args,**kwargs):raise RuntimeError('Synthetic checkpoint failure')
    monkeypatch.setattr(importer,'audit',fail)
    with pytest.raises(RuntimeError,match='checkpoint failure'):step(c,csrf,jid,2)
    assert state(app,jid)[1]['cursor']==2 and state(app,jid)[3]==2
    assert len(files(app))==2
    monkeypatch.setattr(importer,'audit',original)
    assert step(c,csrf,jid,2).json['done']
    assert len(files(app))==3


def test_worker_exit_after_file_write_recovers_without_orphans(app,monkeypatch):
    c,csrf,token,jid=start(app,monkeypatch,3)
    assert state(app,jid)[0]=='running'
    config={k:app.config[k] for k in ['SQLALCHEMY_DATABASE_URI','UPLOAD_DIR','PDF_DIR','SECRET_KEY']}
    code='''import json,os,sys
from app import create_app
from app.blueprints import documents
from tests.test_phase1_independent import staff
from tests.test_import_resume import step
config=json.loads(sys.argv[1]);config['TESTING']=True
a=create_app(config);original=documents.store_bytes
def die(*args,**kwargs):
 original(*args,**kwargs)
 os._exit(73)
documents.store_bytes=die
c,t=staff(a);step(c,t,int(sys.argv[2]),0)
'''
    result=subprocess.run([sys.executable,'-c',code,json.dumps(config),str(jid)],capture_output=True,text=True,timeout=30)
    assert result.returncode==73,result.stderr
    assert len(files(app))==1 and state(app,jid)[3]==0
    assert step(c,csrf,jid,0).json['processed']==2
    assert len(files(app))==2 and state(app,jid)[3]==2
    assert step(c,csrf,jid,2).json['done']
    assert len(files(app))==3 and state(app,jid)[3]==3


def test_zip_batch_limits_uncompressed_bytes_and_missing_source_can_resume(app,monkeypatch):
    from app.blueprints import importer
    c,csrf,token,jid=start(app,monkeypatch,3)
    monkeypatch.setattr(importer,'ZIP_BATCH_FILES',20)
    monkeypatch.setattr(importer,'ZIP_BATCH_BYTES',25)
    assert step(c,csrf,jid,0).json['processed']==1
    meta=state(app,jid)[1]
    with app.app_context(): archive=Path(importer._token_path(meta['file_token'],'zip'))
    parked=archive.with_suffix('.parked');archive.rename(parked)
    assert step(c,csrf,jid,1).status_code==409
    assert state(app,jid)[1]['cursor']==1
    parked.rename(archive)
    assert step(c,csrf,jid,1).json['processed']==2
    assert step(c,csrf,jid,2).json['done']
    assert len(files(app))==3


def test_zip_commit_then_worker_exit_preserves_committed_files(app,monkeypatch):
    from app.blueprints import importer
    c,csrf,token,jid=start(app,monkeypatch,3)
    original=importer._cleanup_zip_files;calls=[]
    def die_after_commit(*args):
        calls.append(1)
        if len(calls)==2:raise SystemExit('Synthetic exit after database commit')
        return original(*args)
    monkeypatch.setattr(importer,'_cleanup_zip_files',die_after_commit)
    with pytest.raises(SystemExit):step(c,csrf,jid,0)
    assert state(app,jid)[1]['cursor']==2 and len(files(app))==2
    monkeypatch.setattr(importer,'_cleanup_zip_files',original)
    assert step(c,csrf,jid,0).json['processed']==2
    assert len(files(app))==2
    assert step(c,csrf,jid,2).json['done']
    assert len(files(app))==3


def test_zip_resume_rejects_staff_and_missing_csrf(app,monkeypatch):
    c,csrf,token,jid=start(app,monkeypatch)
    assert c.post(f'/import/jobs/{jid}/continue',data={'cursor':0}).status_code==400
    other,tok=staff(app,'paralegal')
    assert step(other,tok,jid,0).status_code==403
    assert state(app,jid)[3]==0
