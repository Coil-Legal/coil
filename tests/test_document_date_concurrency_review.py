"""Independent request transactions racing on accepted document dates."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock, get_ident

import pytest
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from tests.test_zip_import_review import app, client
from tests.helpers import login


@pytest.fixture()
def document(app):
    from app.extensions import db
    from app.models import Document
    with app.app_context():
        doc=Document(matter_id=1,name='Synthetic dates.txt',path='synthetic-dates.txt')
        db.session.add(doc);db.session.commit()
        return doc.id


def form(kinds, token):
    data={'_csrf':token,'n':str(len(kinds))}
    for i,kind in enumerate(kinds):
        data.update({f'sel_{i}':'1',f'date_{i}':'2026-12-01',f'desc_{i}':f'Synthetic {kind}',f'kind_{i}':kind})
    return data


def counts(app):
    from app.models import Task,CalendarEvent,AuditLog
    with app.app_context():
        return (Task.query.filter_by(matter_id=1).count(), CalendarEvent.query.filter_by(matter_id=1).count(),
                AuditLog.query.filter(AuditLog.action=='create',AuditLog.entity.in_(['task','calendar_event'])).count())


@pytest.mark.parametrize('kinds', [['deadline'],['event'],['deadline','event']])
def test_simultaneous_accepts_are_successful_and_create_once(app,document,kinds):
    from app.extensions import db
    clients=[app.test_client(),app.test_client()]
    tokens=[login(c) for c in clients]
    barrier=Barrier(2);lock=Lock();seen=set()
    def collide(conn,cursor,statement,parameters,context,executemany):
        if statement.startswith(('INSERT INTO tasks ', 'INSERT INTO calendar_events ')):
            ident=get_ident()
            with lock:
                first=ident not in seen;seen.add(ident)
            if first:barrier.wait(timeout=10)
    with app.app_context():engine=db.engine
    event.listen(engine,'before_cursor_execute',collide)
    def submit(i):
        try:return clients[i].post(f'/ai/document/{document}/dates/create',data=form(kinds,tokens[i])).status_code
        except Exception as exc:return type(exc).__name__
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(submit,range(2)))
    finally:event.remove(engine,'before_cursor_execute',collide)
    assert results==[302,302],results
    assert counts(app)==(int('deadline' in kinds),int('event' in kinds),len(kinds))


@pytest.mark.parametrize('persistent', [False,True])
def test_commit_collision_retries_entire_batch_without_partial_rows(app,client,document,monkeypatch,persistent):
    from app.extensions import db
    original=db.session.commit;attempts=[]
    def commit():
        attempts.append(1)
        if persistent or len(attempts)==1:
            raise OperationalError('commit',{},Exception('database is locked'))
        return original()
    monkeypatch.setattr(db.session,'commit',commit)
    response=client.post(f'/ai/document/{document}/dates/create',data=form(['deadline','event'],client.tok))
    if persistent:
        assert response.status_code==503
        assert b'Nothing was saved' in response.data
        assert counts(app)==(0,0,0)
        assert len(attempts)==5
    else:
        assert response.status_code==302 and len(attempts)==2
        assert counts(app)==(1,1,2)


def test_non_lock_database_errors_are_not_treated_as_retryable(app,client,document,monkeypatch):
    from app.extensions import db
    attempts=[]
    def commit():
        attempts.append(1)
        raise OperationalError('commit',{},Exception('disk I/O error'))
    monkeypatch.setattr(db.session,'commit',commit)
    with pytest.raises(OperationalError,match='disk I/O error'):
        client.post(f'/ai/document/{document}/dates/create',data=form(['deadline','event'],client.tok))
    assert len(attempts)==1 and counts(app)==(0,0,0)
