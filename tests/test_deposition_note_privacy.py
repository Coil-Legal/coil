"""Attorney deposition analysis must not become source material for client updates."""
import json
from html import unescape

import pytest
from tests.test_zip_import_review import app, client

SENTINEL = 'Synthetic strategy: hold the impeachment exhibit until cross examination.'


def seed_analysis(app, legacy, note_kind):
    from app.extensions import db
    from app.models import DepositionSummary, Note, PiCase
    with app.app_context():
        db.session.add(Note(matter_id=1, body='Routine progress: documents received.'))
        dep = DepositionSummary(matter_id=1, deponent='Synthetic witness', summary_text=SENTINEL)
        db.session.add(dep); db.session.flush()
        did = dep.id
        if note_kind == 'overview':
            db.session.add(PiCase(matter_id=1, overview_text=SENTINEL))
        if legacy:
            db.session.add(Note(matter_id=1, body=('Deposition summary: Synthetic witness\n\n'
                                + SENTINEL + '\n\nAI draft for attorney review.' if note_kind == 'deposition'
                                else 'Case overview (Sep 22, 2026). This is a draft for attorney review and may contain errors.\n\n' + SENTINEL)))
        db.session.commit()
    return did


@pytest.mark.parametrize('note_kind', ['deposition', 'overview'])
@pytest.mark.parametrize('legacy', [False, True])
@pytest.mark.parametrize('provider_available', [False, True])
def test_deposition_analysis_excluded_from_client_drafts(app, client, monkeypatch, legacy, provider_available, note_kind):
    from app import llm
    from app.extensions import db
    from app.models import Note, Matter
    from app.blueprints.ai import update_facts
    did = seed_analysis(app, legacy, note_kind)
    if not legacy:
        url = f'/discovery/depositions/{did}/note' if note_kind == 'deposition' else '/records/1/overview/note'
        saved = client.post(url, data={'_csrf': client.tok})
        assert saved.status_code == 302
    seen = []
    def complete(prompt, **kwargs):
        seen.append(prompt)
        if not provider_available:
            raise llm.LLMUnavailable('Synthetic unavailable provider')
        return json.dumps({'subject': 'Routine update', 'body': 'Documents received.'})
    monkeypatch.setattr(llm, 'complete', complete)
    response = client.post('/ai/matter/1/update-email', data={'_csrf': client.tok})
    assert response.status_code == 200
    assert len(seen) == 1
    assert SENTINEL not in seen[0]
    assert 'Routine progress: documents received.' in seen[0]
    assert 'Deposition summary:' not in unescape(response.get_data(as_text=True))
    assert 'Case overview (' not in unescape(response.get_data(as_text=True))
    with app.app_context():
        note = Note.query.filter(Note.body.contains(SENTINEL)).one()
        # Preserve attorney access to the saved content, including historical notes.
        assert SENTINEL in note.body
        if not legacy:
            assert note.body.startswith('[internal] ')
        safe = update_facts(db.session.get(Matter, 1))['notes']
        assert note.id not in [n.id for n in safe]


def test_ordinary_deposition_progress_note_stays_eligible(app):
    from app.extensions import db
    from app.models import Note, Matter
    from app.blueprints.ai import update_facts
    with app.app_context():
        note = Note(matter_id=1, body='Deposition summary: transcript received and review completed.')
        db.session.add(note); db.session.commit()
        assert note.id in [n.id for n in update_facts(db.session.get(Matter, 1))['notes']]
