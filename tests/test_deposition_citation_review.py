"""Synthetic source checks for generated deposition testimony and all exports."""
import json
import pytest
from tests.test_zip_import_review import app, client


def run_summary(app, monkeypatch, text, items):
    from app import llm
    from app.extensions import db
    from app.models import Matter, DepositionSummary
    from app.blueprints.discovery import summarize_transcript
    monkeypatch.setattr(llm, 'complete_json', lambda *a, **kw: {
        'summary': 'Synthetic summary.', 'key_testimony': items, 'contradictions': []})
    with app.test_request_context():
        dep = DepositionSummary(matter=db.session.get(Matter, 1), deponent='Synthetic witness')
        return summarize_transcript(dep, text)[1]


def item(quote, page=1, line=1):
    return {'quote': quote, 'page': page, 'line': line, 'topic': 'Synthetic'}


def test_missing_quote_has_no_invented_citation(app, monkeypatch):
    rows = run_summary(app, monkeypatch, 'VOLUME I\nPage 1\n1:1 The car was green.\nVOLUME II\nPage 1\n1:1 The car stopped.',
                       [item('The car was blue.')])
    assert rows[0]['page'] == 0 and rows[0]['line'] == 0 and not rows[0].get('volume')
    assert 'not found' in rows[0]['citation_warning'].lower()


def test_repeated_quote_is_ambiguous_instead_of_first_volume(app, monkeypatch):
    text = 'VOLUME I\nPage 1\n1:1 I do not recall.\nVOLUME II\nPage 1\n1:1 I do not recall.'
    row = run_summary(app, monkeypatch, text, [item('I do not recall.')])[0]
    assert row['page'] == 0 and not row.get('volume')
    assert 'more than once' in row['citation_warning']


def test_wrong_model_numbers_are_replaced_by_source_markers(app, monkeypatch):
    row = run_summary(app, monkeypatch, 'VOLUME I\nPage 12\n12:6 A. The signal was green.',
                      [item('The signal was green.', 99, 88)])[0]
    assert (row['page'], row['line']) == (12, 6)


def test_time_in_testimony_is_not_a_line_marker(app, monkeypatch):
    row = run_summary(app, monkeypatch, 'Page 12\n12:6 A. At 10:30 I arrived at the office.',
                      [item('I arrived at the office.', 10, 30)])[0]
    assert (row['page'], row['line']) == (12, 6)


def test_missing_markers_do_not_keep_model_numbers(app, monkeypatch):
    row = run_summary(app, monkeypatch, 'The signal was green.', [item('The signal was green.', 22, 5)])[0]
    assert row['page'] == 0 and row['line'] == 0
    assert row['citation_warning']


def test_malformed_testimony_does_not_crash_good_summary(app, monkeypatch):
    rows = run_summary(app, monkeypatch, 'Page 1\n1:1 Exact words.',
                       [None, 'bad', 42, item('Exact words.')])
    assert len(rows) == 1 and rows[0]['page'] == 1


def test_old_unmatched_citations_warn_in_page_note_and_pdf(app, client):
    from app.extensions import db
    from app.models import DepositionSummary, Matter
    from app.blueprints.documents import store_bytes
    from app.blueprints.discovery import deposition_note_text, build_deposition_pdf
    from pypdf import PdfReader
    from io import BytesIO
    with app.app_context():
        doc, err = store_bytes(1, 'synthetic-transcript.txt', b'Page 1\n1:1 Exact words.', user_id=1)
        assert err is None
        dep = DepositionSummary(matter=db.session.get(Matter, 1), document=doc,
              deponent='Synthetic witness', summary_text='Synthetic summary.',
              key_testimony_json=json.dumps([item('Invented words.', 77, 8)]))
        db.session.add(dep); db.session.commit(); did = dep.id
        original = dep.key_testimony_json
        note = deposition_note_text(dep)
        pdf = PdfReader(BytesIO(build_deposition_pdf(dep)))
        pdf_text = '\n'.join(p.extract_text() or '' for p in pdf.pages)
        for text in (note, pdf_text):
            assert 'Quote not found' in text and '77:8' not in text
        assert dep.key_testimony_json == original
    html = client.get(f'/discovery/depositions/{did}').get_data(as_text=True)
    assert 'Quote not found' in html and '77:8' not in html
    assert 'copy-ready' not in html


def test_repeated_quote_across_chunks_stays_ambiguous(app, monkeypatch):
    from app.blueprints import discovery
    pieces = ['VOLUME I\nPage 1\n1:1 Same words.', 'VOLUME II\nPage 1\n1:1 Same words.']
    monkeypatch.setattr(discovery, 'chunk_transcript', lambda text, **kw: pieces)
    rows = run_summary(app, monkeypatch, '\n'.join(pieces), [item('Same words.')])
    assert len(rows) == 2
    assert all(not row.get('volume') and 'more than once' in row['citation_warning'] for row in rows)


def test_page_only_source_does_not_invent_line(app, monkeypatch):
    row = run_summary(app, monkeypatch, 'Page 12\nA. The signal was green.',
                      [item('The signal was green.', 99, 8)])[0]
    assert (row['page'], row['line']) == (12, 0)


def test_volume_boundary_does_not_inherit_previous_page(app, monkeypatch):
    row = run_summary(app, monkeypatch, 'VOLUME I\nPage 12\n12:6 A. Green.\nVOLUME II\nA. Blue.',
                      [item('Blue.', 12, 6)])[0]
    assert row['page'] == 0 and row['line'] == 0 and not row.get('volume')
