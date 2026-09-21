"""Synthetic matter isolation and research memo preservation checks."""
import io
import json
from datetime import datetime, timedelta

import pytest
from pypdf import PdfReader
from tests.test_zip_import_review import app, client


@pytest.mark.parametrize('message_contact_missing', [False, True])
def test_summary_uses_only_messages_filed_to_this_matter(app, client, monkeypatch, message_contact_missing):
    from app.extensions import db
    from app.models import Matter, Message
    from app import llm
    with app.app_context():
        m = db.session.get(Matter, 1)
        other = Matter(number='AI-OTHER', name='Synthetic unrelated case', client_id=m.client_id)
        db.session.add(other)
        db.session.flush()
        # Other-matter activity must neither enter the prompt nor crowd out this matter's facts.
        db.session.add(Message(matter_id=m.id, contact_id=None if message_contact_missing else m.client_id, body='TARGET: no offer received',
                               created_at=datetime(2026, 9, 1)))
        for i in range(12):
            db.session.add(Message(matter_id=other.id, contact_id=m.client_id,
                                   body='OTHER: settlement accepted for 98765.43',
                                   created_at=datetime(2026, 9, 2) + timedelta(minutes=i)))
        db.session.add(Message(contact_id=m.client_id, body='UNFILED: unknown case outcome'))
        db.session.commit()
    seen = []
    def complete(prompt, **kwargs):
        seen.append(prompt)
        return json.dumps({'summary': 'No offer received.', 'open_items': []})
    monkeypatch.setattr(llm, 'complete', complete)
    response = client.post('/ai/matter/1/summary', data={'_csrf': client.tok})
    assert response.status_code == 200
    assert len(seen) == 1
    assert 'OTHER:' not in seen[0]
    assert 'UNFILED:' not in seen[0]
    assert 'TARGET: no offer received' in seen[0]


@pytest.mark.parametrize('use_notes', [True, False])
def test_research_memo_keeps_literal_source_text(app, client, use_notes):
    from app.extensions import db
    from app.models import Matter, SavedAuthority, Document
    from pathlib import Path
    with app.app_context():
        m = db.session.get(Matter, 1)
        m.name = 'Synthetic <Review> & Matter'
        body = 'Read <the complete opinion> & compare the record. Amount <500; no holding supplied.'
        authority = SavedAuthority(matter_id=m.id, case_name='Synthetic <Party> & Co. v. Example',
                                   citation='1 QA 2', notes=body if use_notes else '',
                                   snippet='' if use_notes else body)
        db.session.add(authority)
        db.session.commit()
    response = client.post('/research/saved/export', data={'_csrf': client.tok, 'matter_id': 1})
    assert response.status_code == 302
    with app.app_context():
        doc = Document.query.filter_by(matter_id=1, folder='Research').one()
        pdf = (Path(app.config['UPLOAD_DIR']) / doc.path).read_bytes()
        text = '\n'.join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages)
        for expected in ['Synthetic <Review> & Matter', 'Synthetic <Party> & Co.',
                         '<the complete opinion> & compare', 'Amount <500']:
            assert expected in text, text
        assert not doc.shared_to_portal
