"""Do not insert unsupported completeness claims into client-update drafts."""
import json
from html import unescape
import pytest
from tests.test_zip_import_review import app, client
from tests.test_client_update_context import note


def fields(response):
    from html.parser import HTMLParser
    class Fields(HTMLParser):
        def __init__(self):
            super().__init__(); self.subject=''; self.body=''; self.capture=False; self.scripts=0
        def handle_starttag(self,tag,attrs):
            attrs=dict(attrs)
            if tag=='input' and attrs.get('name')=='subject': self.subject=attrs.get('value','')
            if tag=='textarea' and attrs.get('name')=='body': self.capture=True
            if tag=='script': self.scripts+=1
        def handle_endtag(self,tag):
            if tag=='textarea': self.capture=False
        def handle_data(self,data):
            if self.capture: self.body+=data
    result=Fields(); result.feed(response.get_data(as_text=True))
    result.text=unescape(response.get_data(as_text=True))
    return result,result.subject,result.body


@pytest.mark.parametrize('claim,lang', [
    ('There are no new developments to report at this time.', 'en'),
    ('There have been no other updates.', 'en'),
    ('Nothing else has happened on your matter.', 'en'),
    ('There are no immediate next steps.', 'en'),
    ('No upcoming deadlines are scheduled.', 'en'),
    ('No hay novedades que comunicar en este momento.', 'es'),
    ('No se han producido otros avances.', 'es'),
])
def test_model_completeness_claim_is_held_not_saved(app,client,monkeypatch,claim,lang):
    from app import llm
    from app.extensions import db
    from app.models import Contact, Message, Note
    with app.app_context():
        db.session.get(Contact,1).language=lang;db.session.commit()
    original='Documents received. Receipt date unknown. Correction: one attachment is still missing.'
    note(app,original)
    note(app,'[internal] Private strategy must not reach client draft.')
    calls=[]
    def complete(prompt,**kwargs):
        calls.append(prompt)
        return json.dumps({'subject':'Matter update','body':claim+'\n<script>alert(1)</script>'})
    monkeypatch.setattr(llm,'complete',complete)
    response=client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    soup,subject,body=fields(response)
    assert response.status_code==200 and len(calls)==1
    assert claim not in body and original in body
    assert 'Private strategy' not in body and 'Private strategy' not in calls[0]
    assert 'AI proposal held for review' in soup.text and claim in soup.text
    assert '<script>alert(1)</script>' not in response.get_data(as_text=True)
    assert '&lt;script&gt;alert(1)&lt;/script&gt;' in response.get_data(as_text=True)
    assert 'AI was not available' not in soup.text
    with app.app_context():
        assert Message.query.count()==0
        before=[n.body for n in Note.query.order_by(Note.id)]
    saved=client.post('/ai/matter/1/update-email/draft',data={'_csrf':client.tok,'subject':subject,'body':body})
    assert saved.status_code==302
    with app.app_context():
        msg=Message.query.one();assert msg.status=='draft' and msg.body==body
        assert [n.body for n in Note.query.order_by(Note.id)]==before


def test_subject_claim_is_also_held(app,client,monkeypatch):
    from app import llm
    note(app,'Documents received.')
    monkeypatch.setattr(llm,'complete',lambda *a,**kw:json.dumps({'subject':'No new developments','body':'Documents received.'}))
    soup,subject,body=fields(client.post('/ai/matter/1/update-email',data={'_csrf':client.tok}))
    assert subject!='No new developments' and 'AI proposal held for review' in soup.text


@pytest.mark.parametrize('claim,lang', [
    ('Recently, a note was added to the file regarding the incident.', 'en'),
    ('We recently received an update on your matter.', 'en'),
    ('Recientemente se agrego una nota al expediente.', 'es'),
])
def test_model_recency_claim_is_held_not_saved(app,client,monkeypatch,claim,lang):
    from app import llm
    from app.extensions import db
    from app.models import Contact
    with app.app_context():
        db.session.get(Contact,1).language=lang;db.session.commit()
    note(app,'Initial account: the signal was green. Correction: the witness later reported a red signal, not green. The incident date remains unknown.')
    monkeypatch.setattr(llm,'complete',lambda *a,**kw:json.dumps({'subject':'Matter update','body':claim}))
    response=client.post('/ai/matter/1/update-email',data={'_csrf':client.tok})
    soup,subject,body=fields(response)
    assert claim not in body
    assert 'AI proposal held for review' in soup.text and claim in soup.text


def test_supported_simple_draft_still_uses_model(app,client,monkeypatch):
    from app import llm
    note(app,'Documents received. Receipt date unknown.')
    model='Your file records receipt of documents. The receipt date is not recorded.'
    monkeypatch.setattr(llm,'complete',lambda *a,**kw:json.dumps({'subject':'Documents received','body':model}))
    soup,subject,body=fields(client.post('/ai/matter/1/update-email',data={'_csrf':client.tok}))
    assert body==model and 'AI proposal held for review' not in soup.text


def test_explicit_note_is_preserved_in_attributed_template(app,client,monkeypatch):
    from app import llm
    original='As of September 1, the client reported no new developments. This does not describe later events.'
    note(app,original)
    monkeypatch.setattr(llm,'complete',lambda *a,**kw:json.dumps({'subject':'Update','body':'There are no new developments.'}))
    soup,subject,body=fields(client.post('/ai/matter/1/update-email',data={'_csrf':client.tok}))
    assert original in body and 'Notes from your file:' in body
    assert body!='There are no new developments.'
