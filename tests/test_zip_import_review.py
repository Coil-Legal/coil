"""ZIP mapping and document identity regressions, using synthetic files only."""
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

from tests.test_importer import _upload, _commit, _job


@pytest.fixture()
def app(tmp_path, monkeypatch):
    uri = 'sqlite:///' + str(tmp_path / 'zip.db')
    monkeypatch.setenv('DATABASE_URL', uri)
    from app import create_app
    from app.extensions import db
    from app.models import User, Contact, Matter
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': uri,
                      'UPLOAD_DIR': str(tmp_path / 'uploads')})
    with app.app_context():
        user = User(email='owner@example.com', name='ZIP reviewer', role='owner')
        user.set_password('password123')
        contact = Contact(first_name='Synthetic', last_name='ZIP client', is_client=True)
        db.session.add_all([user, contact]); db.session.flush()
        db.session.add(Matter(number='ZIP-1', name='Synthetic ZIP matter', client_id=contact.id))
        db.session.commit()
    return app


@pytest.fixture()
def client(app):
    from tests.helpers import login
    c = app.test_client(); c.tok = login(c)
    return c


def archive(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w') as z:
        for path, content in entries:
            z.writestr(path, content)
    return stream.getvalue()


def documents(app):
    from app.models import Document
    with app.app_context():
        return [(d.name, (Path(app.config['UPLOAD_DIR']) / d.path).read_bytes())
                for d in Document.query.order_by(Document.id).all()]


def test_explicit_skip_survives_save_and_bare_commit(app, client):
    token = _upload(client, 'documents', archive([('ZIP-1/skip.txt', b'Skip this')]), 'skip.zip')
    field = 'folder_' + hashlib.md5(b'ZIP-1').hexdigest()
    saved = client.post('/import/preview/' + token,
                        data={'_csrf': client.tok, 'do': 'recheck', field: ''})
    assert saved.status_code == 200
    assert b'value="1" selected' not in saved.data
    job = _job(app, _commit(client, token))
    assert job['created'] == 0 and job['skipped'] == 1 and not job['errors'], job
    assert documents(app) == []


def test_windows_archive_paths_preserve_contents_and_reimport(app, client):
    raw = archive([(r'ZIP-1\notes\windows.txt', b'Windows content')])
    job = _job(app, _commit(client, _upload(client, 'documents', raw, 'windows.zip')))
    assert job['created'] == 1 and not job['errors'], job
    assert documents(app) == [('windows.txt', b'Windows content')]
    job = _job(app, _commit(client, _upload(client, 'documents', raw, 'windows.zip')))
    assert job['created'] == 0 and job['skipped'] == 1, job


def test_long_paths_do_not_collide_and_reimport_skips(app, client):
    prefix = 'ZIP-1/' + 'a' * 115
    raw = archive([(prefix + 'one.txt', b'First'), (prefix + 'two.txt', b'Second')])
    job = _job(app, _commit(client, _upload(client, 'documents', raw, 'long.zip')))
    assert job['created'] == 2 and not job['errors'], job
    assert [content for _, content in documents(app)] == [b'First', b'Second']
    job = _job(app, _commit(client, _upload(client, 'documents', raw, 'long.zip')))
    assert job['created'] == 0 and job['skipped'] == 2, job


@pytest.mark.parametrize('second_path', ['ZIP-1/duplicate.txt', r'ZIP-1\duplicate.txt'])
def test_ambiguous_member_names_are_reported_without_wrong_bytes(app, client, second_path):
    raw = archive([('ZIP-1/duplicate.txt', b'First version'), (second_path, b'Second version'),
                   ('ZIP-1/safe.txt', b'Safe')])
    token = _upload(client, 'documents', raw, 'ambiguous.zip')
    page = client.get('/import/preview/' + token)
    assert b'Ambiguous duplicate path' in page.data
    job = _job(app, _commit(client, token))
    assert job['created'] == 1 and job['skipped'] == 2, job
    assert documents(app) == [('safe.txt', b'Safe')]


def test_legacy_truncated_reference_requires_review(app, client):
    from app.extensions import db
    from app.models import ExternalRef
    path = 'ZIP-1/' + 'a' * 115 + 'new.txt'
    with app.app_context():
        db.session.add(ExternalRef(source='clio', entity='document', external_id=path[:120], coil_id=999))
        db.session.commit()
    job = _job(app, _commit(client, _upload(client, 'documents', archive([(path, b'New')]), 'legacy.zip')))
    assert job['created'] == 0 and len(job['errors']) == 1, job
    assert 'shortened path' in job['errors'][0]['message']
    assert documents(app) == []
