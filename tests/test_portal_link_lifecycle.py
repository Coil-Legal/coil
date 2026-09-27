"""Synthetic portal lifecycle checks, with outbound mail captured in memory."""
from datetime import timedelta

import pytest

from tests.test_phase1_independent import app
from app.extensions import db
from app.models import Contact, Document, Matter, PortalToken, now
from app.blueprints import portal


@pytest.fixture(autouse=True)
def capture_mail(monkeypatch):
    sent = []
    monkeypatch.setattr(portal, 'send_email', lambda *args, **kwargs: sent.append(args) or True)
    return sent


def token(app, contact_id=1, purpose='portal'):
    with app.app_context():
        t = PortalToken(contact_id=contact_id, purpose=purpose, expires_at=now()+timedelta(minutes=30))
        db.session.add(t)
        db.session.commit()
        return t.id, t.token


def request_link(app):
    r = app.test_client().post('/portal/login', data={'email': ' CLIENT@EXAMPLE.TEST '})
    assert r.status_code == 200 and b'If we have that email' in r.data
    with app.app_context():
        t = PortalToken.query.filter_by(contact_id=1, purpose='portal').order_by(PortalToken.id.desc()).first()
        return t.id, t.token


def test_replacement_link_revokes_old_links_only(app, capture_mail):
    with app.app_context():
        c = Contact(first_name='Other', email='other@example.test', is_client=True)
        db.session.add(c);db.session.commit();other_id=c.id
    old_id, old = token(app)
    card_id, card = token(app, purpose='card')
    other_token_id, other = token(app, other_id)
    _, fresh = request_link(app)
    assert len(capture_mail) == 1
    assert app.test_client().get(f'/portal/auth/{old}').status_code == 410
    assert app.test_client().get(f'/portal/auth/{card}').status_code == 410
    with app.app_context():
        old_row = db.session.get(PortalToken, old_id)
        assert old_row.used_at is None and old_row.expires_at <= now()
        assert db.session.get(PortalToken, card_id).expires_at > now()
        assert db.session.get(PortalToken, other_token_id).expires_at > now()
    client = app.test_client()
    assert client.get(f'/portal/auth/{fresh}').status_code == 302
    with client.session_transaction() as s:
        assert s['portal_contact_id'] == 1
    assert app.test_client().get(f'/portal/auth/{fresh}').status_code == 410
    assert app.test_client().get(f'/portal/auth/{other}').status_code == 302


def test_rate_limited_request_keeps_latest_link(app, capture_mail):
    links = [request_link(app)[1] for _ in range(3)]
    latest_id, latest = request_link(app)
    assert len(capture_mail) == 3 and latest == links[-1]
    with app.app_context():
        assert PortalToken.query.filter_by(contact_id=1, purpose='portal').count() == 3
    for old in links[:-1]:
        assert app.test_client().get(f'/portal/auth/{old}').status_code == 410
    assert app.test_client().get(f'/portal/auth/{latest}').status_code == 302


def test_card_tokens_do_not_exhaust_login_limit(app, capture_mail):
    for _ in range(3):
        token(app, purpose='card')
    r=app.test_client().post('/portal/login', data={'email':'client@example.test'})
    assert r.status_code == 200
    with app.app_context():
        assert PortalToken.query.filter_by(contact_id=1, purpose='portal').count() == 1
        assert PortalToken.query.filter_by(contact_id=1, purpose='card').count() == 3
    assert len(capture_mail) == 1


@pytest.mark.parametrize('delivery', ['logged', 'raises'])
def test_replacement_mail_failure_stays_neutral(app, monkeypatch, delivery):
    _, old = request_link(app)
    def fail(*args, **kwargs):
        if delivery == 'raises':
            raise RuntimeError('Synthetic relay failure')
        return False
    monkeypatch.setattr(portal, 'send_email', fail)
    _, fresh = request_link(app)
    assert fresh != old
    assert app.test_client().get(f'/portal/auth/{old}').status_code == 410
    with app.app_context():
        assert PortalToken.query.filter_by(contact_id=1, purpose='portal').count() == 2


def test_expiry_boundary_is_not_valid(app, monkeypatch):
    stamp=now()
    with app.app_context():
        t=PortalToken(contact_id=1, expires_at=stamp)
        db.session.add(t);db.session.commit();value=t.token
    monkeypatch.setattr(portal, 'now', lambda: stamp)
    c=app.test_client()
    assert c.get(f'/portal/auth/{value}').status_code == 410
    with c.session_transaction() as s:
        assert 'portal_contact_id' not in s


@pytest.mark.parametrize('first_is_client', [False, True])
def test_shared_email_selection_is_deterministic(app, first_is_client):
    with app.app_context():
        first=db.session.get(Contact,1);first.is_client=first_is_client
        second=Contact(first_name='Second',email=first.email,is_client=True)
        db.session.add(second);db.session.commit();expected=1 if first_is_client else second.id
    response=app.test_client().post('/portal/login',data={'email':'client@example.test'})
    assert response.status_code == 200
    with app.app_context():
        t=PortalToken.query.one();assert t.contact_id==expected;value=t.token
    c=app.test_client();assert c.get(f'/portal/auth/{value}').status_code==302
    with c.session_transaction() as s:
        assert s['portal_contact_id']==expected


def test_unsharing_document_revokes_existing_session_download(app, tmp_path):
    path=tmp_path/'synthetic.txt';path.write_bytes(b'Synthetic portal review only')
    with app.app_context():
        d=Document(matter_id=1,name='Synthetic.txt',path=str(path),mime='text/plain',shared_to_portal=True)
        db.session.add(d);db.session.commit();did=d.id
    _,value=token(app);c=app.test_client();assert c.get(f'/portal/auth/{value}').status_code==302
    assert c.get(f'/portal/documents/{did}/download').data==path.read_bytes()
    with app.app_context():
        db.session.get(Document,did).shared_to_portal=False;db.session.commit()
    assert c.get(f'/portal/documents/{did}/download').status_code==404


def test_closed_matter_document_remains_available_to_its_client(app, tmp_path):
    path=tmp_path/'closed.txt';path.write_bytes(b'Synthetic closed matter record')
    with app.app_context():
        db.session.get(Matter,1).status='closed'
        d=Document(matter_id=1,name='Closed record.txt',path=str(path),mime='text/plain',shared_to_portal=True)
        db.session.add(d);db.session.commit();did=d.id
    _,value=token(app);c=app.test_client();assert c.get(f'/portal/auth/{value}').status_code==302
    assert b'Closed record.txt' in c.get('/portal').data
    assert c.get(f'/portal/documents/{did}/download').data==path.read_bytes()
