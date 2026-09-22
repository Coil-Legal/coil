"""A repeated reporter page must not inherit another occurrence's case name."""
from html import unescape
import pytest
from tests.test_zip_import_review import app, client
from app.blueprints import _courtlistener as cl

CITE = '384 U.S. 436'
SOURCE = 'Miranda v. Arizona, 384 U.S. 436 (1966).\nZyx v. Qwerty, 384 U.S. 436 (1966).'


def result(offset):
    return {'citation': CITE, 'status': 200, 'start_index': offset,
            'clusters': [{'id': 1, 'case_name': 'Miranda v. Arizona', 'date_filed': '1966-06-13'}]}


def lookup(monkeypatch, text, items):
    monkeypatch.setattr(cl, '_post', lambda *a, **kw: {'ok': True, 'data': items})
    return cl.citation_lookup(text)['citations']


@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('prefix', ['', 'Synthetic Unicode note: café 😀.\n'])
def test_repeated_results_use_their_own_source_offsets(monkeypatch, reverse, prefix):
    text = prefix + SOURCE
    items = [result(text.index(CITE)), result(text.rindex(CITE))]
    if reverse:
        items.reverse()
    rows = lookup(monkeypatch, text, items)
    by_name = {r['claimed_name']: r for r in rows}
    assert by_name['Miranda v. Arizona']['resolution'] == 'resolved'
    assert by_name['Zyx v. Qwerty']['resolution'] == 'name_mismatch'
    assert not by_name['Zyx v. Qwerty']['found']


@pytest.mark.parametrize('bad_offset', [None, -1, 9999, '19', True, 19.0, 0])
def test_repeated_citation_without_valid_offset_needs_source_review(monkeypatch, bad_offset):
    row = lookup(monkeypatch, SOURCE, [result(bad_offset)])[0]
    assert row['resolution'] == 'source_uncertain'
    assert not row['found'] and row['claimed_name'] == ''


def test_single_occurrence_can_fall_back_to_exact_text(monkeypatch):
    row = lookup(monkeypatch, 'Zyx v. Qwerty, '+CITE, [result(None)])[0]
    assert row['resolution'] == 'name_mismatch'
    assert row['claimed_name'] == 'Zyx v. Qwerty'


def test_unlocatable_normalized_citation_needs_source_review(monkeypatch):
    row = lookup(monkeypatch, 'Zyx v. Qwerty, 384  U.S.  436', [result(15)])[0]
    assert row['resolution'] == 'source_uncertain'


@pytest.mark.parametrize('source,expected', [
    ('Miranda v. Arizona, '+CITE+'; Miranda v. Arizona, '+CITE, ['resolved', 'resolved']),
    (CITE+'; Zyx v. Qwerty, '+CITE, ['resolved', 'name_mismatch']),
])
def test_valid_repeats_and_nameless_first_occurrence(monkeypatch, source, expected):
    rows = lookup(monkeypatch, source, [result(source.index(CITE)), result(source.rindex(CITE))])
    assert [r['resolution'] for r in rows] == expected


@pytest.mark.parametrize('uncertain', [False, True])
def test_page_and_saved_note_preserve_each_review_outcome(app, client, monkeypatch, uncertain):
    from app.models import Note, AuditLog
    items = [result(None), result(None)] if uncertain else [result(SOURCE.index(CITE)), result(SOURCE.rindex(CITE))]
    lookup(monkeypatch, SOURCE, items)
    response = client.post('/research/cite-check', data={'_csrf': client.tok, 'text': SOURCE, 'matter_id': 1})
    assert response.status_code == 200
    html = unescape(response.get_data(as_text=True))
    with app.app_context():
        body = Note.query.one().body
        assert body.startswith('[internal]')
        if uncertain:
            assert '0 resolved' in html and '2 source occurrences needing review' in html
            assert 'source occurrence needs review' in html
            assert 'SOURCE OCCURRENCE NEEDS REVIEW' in body and '2 source occurrences needing review' in body
            assert '2 source occurrences needing review' in AuditLog.query.filter_by(entity='note').one().detail
        else:
            assert '1 resolved' in html and 'wrong case, do not file' in html
            assert 'Zyx v. Qwerty' in html
            assert '1 resolved' in body and 'Miranda v. Arizona, not Zyx v. Qwerty' in body
