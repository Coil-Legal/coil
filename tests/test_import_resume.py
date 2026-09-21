"""Large imports use bounded requests with atomic, retryable progress."""
import io
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from tests.test_phase1_independent import app, staff


def upload(client, csrf, count=7):
    body='Id,Name,Email\n'+''.join(f'bulk{i},Bulk Person {i},bulk{i}@example.test\n' for i in range(count))
    response=client.post('/import/contacts/upload',data={'_csrf':csrf,'source':'generic','file':(io.BytesIO(body.encode()),'bulk.csv')})
    assert response.status_code==302
    return response.location.rsplit('/',1)[-1]


def start(app, monkeypatch, count=7):
    from app.blueprints import importer
    monkeypatch.setattr(importer,'CSV_BATCH_ROWS',3,raising=False)
    client,csrf=staff(app)
    token=upload(client,csrf,count)
    response=client.post('/import/preview/'+token,data={'_csrf':csrf,'do':'commit'})
    assert response.status_code==302
    jid=int(response.location.rsplit('/',1)[-1])
    return client,csrf,token,jid


def state(app,jid):
    from app.extensions import db
    from app.models import ImportJob,Contact
    with app.app_context():
        job=db.session.get(ImportJob,jid)
        return job.status,json.loads(job.mapping_json),job.created,Contact.query.count(),job.errors


def step(client,csrf,jid,cursor):
    return client.post(f'/import/jobs/{jid}/continue',data={'_csrf':csrf,'cursor':cursor},headers={'Accept':'application/json'})


def test_large_preview_is_bounded_and_says_it_is_a_sample(app,monkeypatch):
    from app.blueprints import importer
    client,csrf=staff(app)
    token=upload(client,csrf,501)
    seen=[];original=importer.run_import
    def measure(data,*args,**kwargs):
        seen.append(len(data['rows']))
        return original(data,*args,**kwargs)
    monkeypatch.setattr(importer,'run_import',measure)
    response=client.get('/import/preview/'+token)
    assert response.status_code==200
    assert max(seen)<=200
    assert b'501 rows' in response.data and b'sample' in response.data


def test_large_import_resumes_and_replayed_requests_do_not_advance_twice(app,monkeypatch):
    client,csrf,token,jid=start(app,monkeypatch)
    assert state(app,jid)[0]=='running'
    assert state(app,jid)[3]==1
    first=step(client,csrf,jid,0)
    assert first.status_code==200 and first.json['processed']==3
    assert step(client,csrf,jid,0).json['processed']==3
    assert state(app,jid)[3]==4
    # Revisiting the preview or repeating the start must return the same saved job.
    response=client.post('/import/preview/'+token,data={'_csrf':csrf,'do':'commit'})
    assert response.location.endswith('/jobs/'+str(jid))
    assert step(client,csrf,jid,3).json['processed']==6
    assert step(client,csrf,jid,6).json['done']
    assert step(client,csrf,jid,6).json['done']
    status,meta,created,contacts,errors=state(app,jid)
    assert (status,created,contacts,errors)==('committed',7,8,[])
    assert meta['cursor']==7


def test_failed_batch_rolls_back_records_and_progress_together(app,monkeypatch):
    from app.blueprints import importer
    client,csrf,token,jid=start(app,monkeypatch,3+1)
    assert step(client,csrf,jid,0).json['processed']==3
    original=importer.audit
    def fail(*args,**kwargs):
        raise RuntimeError('Synthetic interruption before final commit')
    monkeypatch.setattr(importer,'audit',fail)
    with pytest.raises(RuntimeError,match='Synthetic interruption'):
        step(client,csrf,jid,3)
    assert state(app,jid)[1]['cursor']==3 and state(app,jid)[3]==4
    monkeypatch.setattr(importer,'audit',original)
    assert step(client,csrf,jid,3).json['done']
    assert state(app,jid)[2:4]==(4,5)


def test_two_workers_on_same_cursor_apply_only_one_batch(app,monkeypatch):
    client,csrf,token,jid=start(app,monkeypatch)
    barrier=Barrier(2)
    clients=[staff(app),staff(app)]
    def worker(pair):
        c,t=pair
        barrier.wait(timeout=10)
        response=step(c,t,jid,0)
        return response.status_code,response.json
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(worker,clients))
    assert all(code==200 and body['processed']==3 for code,body in results)
    assert state(app,jid)[2:4]==(3,4)


def test_batched_trust_is_sorted_and_refuses_overdraw_across_batches(app,monkeypatch):
    from app.blueprints import importer
    from app.models import Contact,TrustTransaction
    from app.extensions import db
    monkeypatch.setattr(importer,'CSV_BATCH_ROWS',2)
    client,csrf=staff(app)
    body=('ID,Date,Type,Client,Matter,Description,Funds In,Funds Out\n'
          'tr3,01/03/2026,Disbursement,Synthetic Client,M-PHASE1,Refuse this,,25.00\n'
          'tr2,01/02/2026,Disbursement,Synthetic Client,M-PHASE1,Valid withdrawal,,10.00\n'
          'tr4,01/04/2026,Deposit,Synthetic Client,M-PHASE1,Later deposit,8.00,\n'
          'tr1,01/01/2026,Deposit,Synthetic Client,M-PHASE1,First deposit,30.00,\n')
    response=client.post('/import/trust/upload',data={'_csrf':csrf,'source':'clio','file':(io.BytesIO(body.encode()),'trust.csv')})
    response=client.post(response.location,data={'_csrf':csrf,'do':'commit'})
    jid=int(response.location.rsplit('/',1)[-1])
    assert step(client,csrf,jid,0).json['processed']==2
    assert step(client,csrf,jid,2).json['done']
    assert step(client,csrf,jid,2).json['done']
    status,meta,created,contacts,errors=state(app,jid)
    assert status=='committed' and created==3 and len(errors)==1
    with app.app_context():
        assert TrustTransaction.query.count()==3
        assert db.session.get(Contact,1).trust_balance_cents()==2800
    failed=client.get(f'/import/jobs/{jid}/failed.csv').get_data(as_text=True)
    assert 'tr3' in failed and 'tr2' not in failed


def test_resume_requires_owner_and_csrf(app,monkeypatch):
    client,csrf,token,jid=start(app,monkeypatch)
    assert client.post(f'/import/jobs/{jid}/continue',data={'cursor':0}).status_code==400
    other,other_csrf=staff(app,'paralegal')
    assert step(other,other_csrf,jid,0).status_code==403
    assert state(app,jid)[3]==1
