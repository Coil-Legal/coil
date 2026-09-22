"""Names must remain reproducible from the signature record and certificate."""
import hashlib
from pathlib import Path

import pytest
from pypdf import PdfReader
from tests.test_phase1_independent import app
from tests.test_phase1_document_integrity import signature_fixture


def signing_case(app, kind):
    from app.extensions import db
    from app.models import Engagement
    if kind == 'document':
        sid, token = signature_fixture(app, None)
        return sid, '/sign/doc/' + token
    with app.app_context():
        body = '<p>Synthetic agreement only.</p>'
        e = Engagement(matter_id=1, contact_id=1, subject='Synthetic agreement', body_html=body,
                       status='sent', document_hash=hashlib.sha256(body.encode()).hexdigest())
        db.session.add(e)
        db.session.commit()
        return e.id, '/sign/' + e.token


@pytest.mark.parametrize('kind', ['document', 'engagement'])
@pytest.mark.parametrize('length', [200, 201])
@pytest.mark.parametrize('language', ['en', 'es'])
def test_signer_name_boundary_preserves_hash_and_pdf(app, monkeypatch, kind, length, language):
    from app.extensions import db
    from app.models import DocumentSignature, Engagement, AuditLog, Contact
    from app.blueprints import signatures, engagements
    # Capture copies locally: this acceptance never sends external mail.
    calls = []
    monkeypatch.setattr(signatures, '_email_signed_copies', lambda *args: calls.append('document'))
    monkeypatch.setattr(engagements, '_email_signed_copies', lambda *args: calls.append('engagement'))
    with app.app_context():
        db.session.get(Contact, 1).language = language
        db.session.commit()
    sid, url = signing_case(app, kind)
    name = ('Alexandria ' * 21)[:length].rstrip()
    assert len(name) == length
    client = app.test_client()
    response = client.post(url, data={'signer_name': name, 'agree': '1'})
    cls = DocumentSignature if kind == 'document' else Engagement
    with app.app_context():
        row = db.session.get(cls, sid)
        if length > 200:
            expected = hashlib.sha256(f'{row.document_hash}{row.signer_name}{row.signer_ip}{row.signed_at.isoformat()}'.encode()).hexdigest() if row.signed_at else None
            assert response.status_code == 400, {'http':response.status_code,'stored_length':len(row.signer_name or ''),'submitted_length':len(name),'hash_reproducible':row.signature_hash==expected}
            assert b'200' in response.data and name.encode() in response.data
            assert ('No se ha firmado nada.' if language == 'es' else 'Nothing has been signed.').encode() in response.data
            assert row.status == 'sent' and not row.signer_name and not row.signature_hash
            assert not row.signed_at and not list(Path(app.config['PDF_DIR']).glob('*.pdf'))
            assert not calls and AuditLog.query.filter_by(action='sign').count() == 0
            return
        assert response.status_code == 200 and row.status == 'signed'
        assert row.signer_name == name
        expected = hashlib.sha256(f'{row.document_hash}{row.signer_name}{row.signer_ip}{row.signed_at.isoformat()}'.encode()).hexdigest()
        assert row.signature_hash == expected
        path = row.certificate_pdf_path if kind == 'document' else row.pdf_path
        data = Path(path).read_bytes()
        text = ' '.join(' '.join(p.extract_text().split()) for p in PdfReader(path).pages)
        assert ' '.join(name.split()) in text
        before = (row.signer_name, row.signature_hash, row.signed_at)
    assert client.post(url, data={'signer_name': 'Different Person', 'agree': '1'}).status_code == 200
    with app.app_context():
        row = db.session.get(cls, sid)
        assert (row.signer_name, row.signature_hash, row.signed_at) == before
        assert Path(path).read_bytes() == data and len(calls) == 1
