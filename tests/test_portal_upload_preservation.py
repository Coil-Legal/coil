"""A second client upload must never change the bytes of an earlier document."""
import io
from pathlib import Path
from tests.test_phase1_independent import app


def test_same_name_uploads_within_one_second_preserve_both_files(app, monkeypatch):
    from app.models import Document
    import time
    monkeypatch.setattr(time, 'time', lambda: 1800000000)
    client = app.test_client()
    with client.session_transaction() as session:
        session['portal_contact_id'] = 1
    for contents in [b'first document', b'second document']:
        response = client.post('/portal/upload', data={
            'matter_id': '1', 'file': (io.BytesIO(contents), 'evidence.txt')})
        assert response.status_code == 302
    with app.app_context():
        docs = Document.query.order_by(Document.id).all()
        assert len(docs) == 2
        assert [Path(doc.path).read_bytes() for doc in docs] == [b'first document', b'second document']
        assert docs[0].path != docs[1].path
