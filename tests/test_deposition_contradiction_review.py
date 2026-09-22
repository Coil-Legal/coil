"""Synthetic source checks for generated deposition contradictions.

Mirrors tests/test_deposition_citation_review.py: an internal contradiction's "source" is a
page:line the model guessed for its own "conflicts_with" quote, not a location it looked up,
and short answers like "I am not sure" recur across a transcript (or across volumes, where page
numbers restart), so the guess can point at the wrong passage.
"""
import json
import pytest
from tests.test_zip_import_review import app, client


def run_contradictions(app, monkeypatch, text, contradictions):
    from app import llm
    from app.extensions import db
    from app.models import Matter, DepositionSummary
    from app.blueprints.discovery import summarize_transcript
    monkeypatch.setattr(llm, 'complete_json', lambda *a, **kw: {
        'summary': 'Synthetic summary.', 'key_testimony': [], 'contradictions': contradictions})
    with app.test_request_context():
        dep = DepositionSummary(matter=db.session.get(Matter, 1), deponent='Synthetic witness')
        return summarize_transcript(dep, text)[2]


def contra(testimony, conflicts_with, source='p1:2', kind='internal'):
    return {'testimony': testimony, 'conflicts_with': conflicts_with, 'source': source, 'kind': kind}


def test_repeated_conflicts_with_is_ambiguous_instead_of_guessed_line(app, monkeypatch):
    text = ('VOLUME I\nPage 1\n1:1 Q. What color was the warehouse door?\n1:2 A. The warehouse door was scarlet.\n'
            '1:3 Q. Do you remember the badge number?\n1:4 A. I am not sure.\n'
            'VOLUME II\nPage 1\n1:1 Q. What color was the warehouse door when you left?\n1:2 A. I am not sure.')
    rows = run_contradictions(app, monkeypatch, text,
        [contra('The warehouse door was scarlet.', 'I am not sure.', source='p1:2')])
    assert 'more than once' in rows[0]['source']
    assert 'p1:2' not in rows[0]['source']


def test_unique_conflicts_with_resolves_to_transcript_marker(app, monkeypatch):
    text = 'VOLUME I\nPage 1\n1:1 A. The signal was green.\nVOLUME II\nPage 3\n3:5 A. The signal was red.'
    rows = run_contradictions(app, monkeypatch, text,
        [contra('The signal was green.', 'The signal was red.', source='p1:2')])
    assert rows[0]['source'] == 'Vol. II, Depo. Tr. 3:5'


def test_missing_conflicts_with_warns_instead_of_guessed_line(app, monkeypatch):
    rows = run_contradictions(app, monkeypatch, 'Page 1\n1:1 A. The signal was green.',
        [contra('The signal was green.', 'The signal was blue.', source='p1:9')])
    assert 'not found' in rows[0]['source'].lower()


def test_external_contradiction_source_is_left_alone(app, monkeypatch):
    rows = run_contradictions(app, monkeypatch, 'Page 1\n1:1 A. I arrived at 9pm.',
        [contra('I arrived at 9pm.', 'the incident report says 7pm', source='chronology 2024-01-01 report',
                kind='external')])
    assert rows[0]['source'] == 'chronology 2024-01-01 report'


def test_old_ambiguous_contradiction_source_warns_in_note_and_pdf(app, client):
    from app.extensions import db
    from app.models import DepositionSummary, Matter
    from app.blueprints.documents import store_bytes
    from app.blueprints.discovery import deposition_note_text, build_deposition_pdf
    from pypdf import PdfReader
    from io import BytesIO
    text = b'VOLUME I\nPage 1\n1:1 A. I am not sure.\nVOLUME II\nPage 1\n1:1 A. I am not sure.'
    with app.app_context():
        doc, err = store_bytes(1, 'synthetic-transcript.txt', text, user_id=1)
        assert err is None
        dep = DepositionSummary(matter=db.session.get(Matter, 1), document=doc,
              deponent='Synthetic witness', summary_text='Synthetic summary.',
              contradictions_json=json.dumps([contra('Confident answer.', 'I am not sure.', source='p1:1')]))
        db.session.add(dep); db.session.commit(); did = dep.id
        original = dep.contradictions_json
        note = deposition_note_text(dep)
        pdf = PdfReader(BytesIO(build_deposition_pdf(dep)))
        pdf_text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
        for output in (note, pdf_text):
            assert 'more than once' in output
        assert dep.contradictions_json == original
    html = client.get(f'/discovery/depositions/{did}').get_data(as_text=True)
    assert 'more than once' in html
