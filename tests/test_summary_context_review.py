"""A summary must not receive a partial statement that loses its correction."""
import json
from html import unescape

import pytest
from tests.test_zip_import_review import app, client


def _capture(monkeypatch):
    from app import llm
    seen = []
    def complete(prompt, **kwargs):
        seen.append(prompt)
        return json.dumps({'summary': 'Synthetic review.', 'open_items': []})
    monkeypatch.setattr(llm, 'complete', complete)
    return seen


def test_message_correction_after_first_300_characters_reaches_summary(app, client, monkeypatch):
    from app.extensions import db
    from app.models import Matter, Message
    body = ('Earlier account: the client had a green light. ' + 'Background detail. ' * 20
            + 'Correction: the witness later reported red, not green. Incident date remains unknown.')
    with app.app_context():
        m = db.session.get(Matter, 1)
        db.session.add(Message(matter_id=m.id, contact_id=m.client_id, body=body))
        db.session.commit()
    seen = _capture(monkeypatch)
    response = client.post('/ai/matter/1/summary', data={'_csrf': client.tok})
    assert response.status_code == 200
    assert body in seen[0]
    # Staff can compare the generated text with the same complete source supplied to the model.
    assert body in unescape(response.get_data(as_text=True))


@pytest.mark.parametrize('body_length', [11000, 14000])
def test_summary_refuses_source_or_prompt_overflow_without_calling_model(app, client, monkeypatch, body_length):
    from app.extensions import db
    from app.models import Note
    with app.app_context():
        db.session.add(Note(matter_id=1, body='A' * body_length + '\nCorrection: the incident date is unknown.'))
        db.session.commit()
    seen = _capture(monkeypatch)
    response = client.post('/ai/matter/1/summary', data={'_csrf': client.tok})
    assert response.status_code == 200
    assert seen == [], 'A shortened record must not reach the model'
    assert b'too long' in response.data
    assert b'Save as a note' not in response.data


def test_summary_shows_literal_source_and_declares_history_limits(app, client, monkeypatch):
    from app.extensions import db
    from app.models import Message, Matter
    with app.app_context():
        m = db.session.get(Matter, 1)
        db.session.add(Message(matter_id=1, contact_id=m.client_id,
                               body='Synthetic <Party> & Co. said "no date". <script>source only</script>'))
        db.session.commit()
    seen = _capture(monkeypatch)
    response = client.post('/ai/matter/1/summary', data={'_csrf': client.tok})
    assert len(seen) == 1
    assert len(seen[0]) <= 12000
    assert b'&lt;Party&gt; &amp; Co.' in response.data
    assert b'<script>source only</script>' not in response.data
    assert b'10 notes' in response.data and b'10 messages' in response.data
