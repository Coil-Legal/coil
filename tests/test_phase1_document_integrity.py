"""Client uploads and signing must preserve the document the client actually supplied."""
import hashlib
import io
from pathlib import Path

import pytest
from tests.test_phase1_independent import app


def portal(app):
    client = app.test_client()
    with client.session_transaction() as session:
        session['portal_contact_id'] = 1
    return client


@pytest.mark.parametrize('name,body', [
    ('renamed.pdf', b'Plain text, not a PDF'),
    ('blocked.exe', b'Synthetic blocked file fixture'),
    ('empty.txt', b''),
    ('large.txt', b'01234567890123456789'),
])
def test_portal_rejects_invalid_upload_without_storing_a_document(app, monkeypatch, name, body):
    from app.blueprints import documents
    from app.models import Document
    monkeypatch.setattr(documents, 'MAX_BYTES', 10 if name == 'large.txt' else documents.MAX_BYTES)
    response = portal(app).post('/portal/upload', data={'matter_id': '1', 'file': (io.BytesIO(body), name)}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert Document.query.count() == 0, 'The portal must apply the same file checks as staff uploads'
    assert not list(Path(app.config['UPLOAD_DIR']).rglob('*.*'))


def test_portal_extracts_text_for_later_conflict_and_document_search(app):
    from app.models import Document
    body = b'Synthetic witness Rowan Example supplied this account.'
    response = portal(app).post('/portal/upload', data={'matter_id': '1', 'file': (io.BytesIO(body), 'account.txt')})
    assert response.status_code == 302
    with app.app_context():
        doc = Document.query.one()
        assert doc.extracted_text == body.decode()
        assert doc.shared_to_portal and doc.uploaded_by_client


def signature_fixture(app, problem):
    from app.extensions import db
    from app.models import DocumentSignature
    from app.blueprints.documents import store_bytes, abs_path
    with app.app_context():
        doc, error = store_bytes(1, 'agreement.txt', b'Original agreed terms', mime='text/plain')
        assert not error
        db.session.flush()
        sig = DocumentSignature(document_id=doc.id, contact_id=1, status='sent', title='QA agreement',
                                document_hash=hashlib.sha256(b'Original agreed terms').hexdigest())
        db.session.add(sig)
        db.session.commit()
        if problem == 'changed':
            Path(abs_path(doc)).write_bytes(b'Different terms that were never sent')
        elif problem == 'missing':
            Path(abs_path(doc)).unlink()
        elif problem == 'missing_hash':
            sig.document_hash = ''
            db.session.commit()
        return sig.id, sig.token


@pytest.mark.parametrize('problem', ['changed', 'missing', 'missing_hash'])
def test_signing_refuses_a_file_that_no_longer_matches_the_sent_copy(app, problem):
    from app.extensions import db
    from app.models import DocumentSignature, DocumentSignatureEvent
    sid, token = signature_fixture(app, problem)
    client = app.test_client()
    response = client.post('/sign/doc/' + token, data={'signer_name': 'QA Signer', 'agree': '1'})
    assert response.status_code == 409
    with app.app_context():
        sig = db.session.get(DocumentSignature, sid)
        assert sig.status == 'sent' and not sig.signed_at and not sig.signature_hash
        assert not DocumentSignatureEvent.query.filter_by(signature_id=sid, event='signed').first()
    assert client.get('/sign/doc/' + token).status_code == 409
    assert client.get('/sign/doc/' + token + '/file').status_code == 409


def test_unchanged_sent_document_can_still_be_signed(app):
    from app.extensions import db
    from app.models import DocumentSignature
    sid, token = signature_fixture(app, None)
    response = app.test_client().post('/sign/doc/' + token, data={'signer_name': 'QA Signer', 'agree': '1'})
    assert response.status_code == 200
    with app.app_context():
        sig = db.session.get(DocumentSignature, sid)
        assert sig.status == 'signed'
        assert sig.document_hash == hashlib.sha256(b'Original agreed terms').hexdigest()
