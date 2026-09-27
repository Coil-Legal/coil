"""Deterministic races against a disposable database, never live portal links."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event

import pytest
from flask import request
from flask_sqlalchemy.query import Query

from tests.test_phase1_independent import app
from tests.test_portal_link_lifecycle import token, capture_mail
from app.extensions import db
from app.models import AuditLog, PortalToken


def intercept_read(monkeypatch, callback):
    original = Query.first
    def first(query):
        value = original(query)
        if (query.column_descriptions[0].get('entity') is PortalToken
                and request.path.startswith('/portal/auth/')):
            callback()
        return value
    monkeypatch.setattr(Query, 'first', first)


def consume(app, value):
    c = app.test_client()
    response = c.get(f'/portal/auth/{value}')
    with c.session_transaction() as session:
        logged_in = 'portal_contact_id' in session
    return response.status_code, logged_in


@pytest.mark.parametrize('workers', [2, 4])
def test_only_one_simultaneous_consumer_gets_session(app, monkeypatch, workers):
    _, value = token(app)
    barrier = Barrier(workers)
    intercept_read(monkeypatch, lambda: barrier.wait(timeout=10))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(consume, app, value) for _ in range(workers)]
        results = [f.result(timeout=15) for f in futures]
    assert sorted(results) == [(302, True)] + [(410, False)] * (workers - 1), results
    with app.app_context():
        assert AuditLog.query.filter_by(action='portal_login', entity='contact', entity_id=1).count() == 1
        assert PortalToken.query.one().used_at is not None


def test_replacement_wins_over_stale_token_read(app, monkeypatch):
    old_id, old = token(app)
    read, release = Event(), Event()
    def pause():
        read.set()
        assert release.wait(timeout=10)
    intercept_read(monkeypatch, pause)
    with ThreadPoolExecutor(max_workers=1) as pool:
        pending = pool.submit(consume, app, old)
        try:
            assert read.wait(timeout=10)
            response = app.test_client().post('/portal/login', data={'email':'client@example.test'})
            assert response.status_code == 200
        finally:
            release.set()
        result = pending.result(timeout=15)
    assert result == (410, False), result
    with app.app_context():
        assert db.session.get(PortalToken, old_id).used_at is None
        assert AuditLog.query.filter_by(action='portal_login').count() == 0
        assert PortalToken.query.count() == 2


def test_failed_commit_does_not_create_portal_session(app, monkeypatch):
    _, value = token(app)
    original = db.session.commit
    def fail():
        raise RuntimeError('Synthetic commit failure')
    monkeypatch.setattr(db.session, 'commit', fail)
    app.config['PROPAGATE_EXCEPTIONS'] = False
    c=app.test_client()
    response=c.get(f'/portal/auth/{value}')
    assert response.status_code == 500
    with c.session_transaction() as session:
        assert 'portal_contact_id' not in session
    monkeypatch.setattr(db.session, 'commit', original)
    with app.app_context():
        assert PortalToken.query.one().used_at is None
        assert AuditLog.query.filter_by(action='portal_login').count() == 0
