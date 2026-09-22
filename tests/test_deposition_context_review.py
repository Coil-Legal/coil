"""Deposition coverage and volume identity across model-request boundaries."""
import pytest
from tests.test_zip_import_review import app


def deposition(app):
    from app.extensions import db
    from app.models import Matter, DepositionSummary
    m = db.session.get(Matter, 1)
    m.description = 'Synthetic facts. ' * 95
    dep = DepositionSummary(matter=m, deponent='Synthetic witness')
    return dep


def test_every_transcript_word_fits_actual_provider_prompt(app, monkeypatch):
    from app import llm
    from app.blueprints import discovery
    transcript = ' '.join(f'Page {p} {p}:1 synthetic testimony token{p} ' + 'background ' * 80 for p in range(1, 25))
    pieces = []
    def complete(prompt, schema, **kw):
        assert len(prompt) <= llm.MAX_CONTEXT_CHARS, 'Provider would silently truncate transcript words'
        if kw['kind'] == 'deposition_summary':
            pieces.append(prompt.split('Transcript part ', 1)[1].split(':\n', 1)[1])
        return {'summary': 'Short part summary.', 'key_testimony': [], 'contradictions': []}
    monkeypatch.setattr(llm, 'complete_json', complete)
    with app.test_request_context(): discovery.summarize_transcript(deposition(app), transcript)
    assert ' '.join(pieces).split() == transcript.split()


def test_quote_before_new_volume_keeps_volume_from_previous_chunk(app, monkeypatch):
    from app import llm
    from app.blueprints import discovery
    pieces = ['VOLUME I Page 1 1:1 First statement.',
              'Page 2 2:1 Continuing warehouse account. VOLUME II Page 1 1:1 Office account.']
    monkeypatch.setattr(discovery, 'chunk_transcript', lambda text, **kwargs: pieces)
    def complete(prompt, schema, **kw):
        key = ([{'page':2, 'line':1, 'quote':'Continuing warehouse account.', 'topic':'Location'}]
               if 'Continuing warehouse account.' in prompt else [])
        return {'summary':'Short part.', 'key_testimony':key, 'contradictions':[]}
    monkeypatch.setattr(llm, 'complete_json', complete)
    with app.test_request_context():
        _, key, _ = discovery.summarize_transcript(deposition(app), ' '.join(pieces))
    assert key[0]['volume'] == 'I'


def test_oversized_condensation_preserves_all_part_summaries(app, monkeypatch):
    from app import llm
    from app.blueprints import discovery
    monkeypatch.setattr(discovery, 'chunk_transcript', lambda text, **kwargs: ['First testimony.', 'Last testimony.'])
    summaries = ['FIRST ' + 'a' * 7000, 'LAST ' + 'b' * 7000]
    calls = []
    def complete(prompt, schema, **kw):
        assert kw['kind'] != 'deposition_condense', 'Oversized condensation would discard later evidence'
        calls.append(prompt)
        return {'summary':summaries[len(calls)-1], 'key_testimony':[], 'contradictions':[]}
    monkeypatch.setattr(llm, 'complete_json', complete)
    with app.test_request_context(): summary, _, _ = discovery.summarize_transcript(deposition(app), 'First testimony. Last testimony.')
    assert summary == '\n\n'.join(summaries)
