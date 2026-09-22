"""Whole statements and record/event date separation in client-update drafts."""
import json
from datetime import datetime, timedelta
from html import unescape
import pytest
from tests.test_zip_import_review import app, client


def note(app, body):
    from app.extensions import db
    from app.models import Note
    with app.app_context():
        n=Note(matter_id=1, body=body, created_at=datetime.now()-timedelta(days=2))
        db.session.add(n);db.session.commit()
        return n.created_at.strftime('%Y-%m-%d')


def capture(monkeypatch, available=True):
    from app import llm
    calls=[]
    def complete(prompt, **kw):
        calls.append(prompt)
        if not available: raise llm.LLMUnavailable('Synthetic provider unavailable')
        return json.dumps({'subject':'Synthetic update','body':'Review this draft.'})
    monkeypatch.setattr(llm,'complete',complete)
    return calls


def test_whole_note_reaches_model_after_old_clip_boundary(app,client,monkeypatch):
    body='Initial account: green signal. '+'Background. '*790+'Correction: red signal. The incident date is unknown.'
    note(app,body); calls=capture(monkeypatch)
    response=client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    assert response.status_code==200 and len(calls)==1
    assert body in calls[0] and len(calls[0])<=12000


@pytest.mark.parametrize('repeats', [940, 1150])
def test_oversized_update_uses_complete_template_without_provider(app,client,monkeypatch,repeats):
    body='Initial account: green signal. '+'Background. '*repeats+'Correction: red signal. The incident date is unknown.'
    note(app,body); calls=capture(monkeypatch)
    response=client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    assert calls==[]
    html=unescape(response.get_data(as_text=True))
    assert 'too long' in html and body in html


@pytest.mark.parametrize('lang', ['en','es'])
def test_fallback_preserves_correction_in_later_paragraph(app,client,monkeypatch,lang):
    from app.extensions import db
    from app.models import Contact
    with app.app_context():
        db.session.get(Contact,1).language=lang;db.session.commit()
    body='Initial account: green signal. '+'Background. '*25+'\nCorrection: the signal was red. Incident date unknown.'
    note(app,body);capture(monkeypatch,False)
    response=client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    html=unescape(response.get_data(as_text=True))
    draft=html.split('name="body"',1)[1].split('>',1)[1].split('</textarea>',1)[0]
    assert body in draft
    assert ('Notes from your file:' if lang=='en' else 'Notas de su expediente:') in draft
    assert 'we have:' not in draft and 'hemos realizado' not in draft


def test_record_timestamp_is_not_in_model_facts(app,client,monkeypatch):
    stamp=note(app,'Documents received. The receipt date was not recorded.')
    calls=capture(monkeypatch)
    client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    assert stamp not in calls[0]
    assert 'Today is ' not in calls[0]


def test_dated_statement_keeps_its_date_and_full_source_is_visible(app,client,monkeypatch):
    body='On September 2, 2026 a witness reported <green> & later corrected it. Incident date unknown.'
    note(app,body);calls=capture(monkeypatch)
    response=client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    html=response.get_data(as_text=True)
    assert body in calls[0] and body in unescape(html)
    assert '&lt;green&gt; &amp;' in html
    assert '8 notes' in html and '10 work entries' in html
