"""Client-update source exclusions must apply before selection, for every record type."""
from datetime import date, datetime, timedelta
from html import unescape
import json

import pytest
from tests.test_zip_import_review import app, client


LIMITS = {'work': 10, 'done': 8, 'upcoming': 8, 'events': 6}
EXCLUDED = ['  [InTeRnAl] Cobalt strategy review', 'Invoice balance $450', 'Reviewed for 2 hours']


def add_record(kind, text, offset=0):
    from app.models import TimeEntry, Task, CalendarEvent
    stamp = datetime.combine(date.today(), datetime.min.time())
    if kind == 'work':
        return TimeEntry(matter_id=1, user_id=1, date=date.today()-timedelta(days=offset), description=text)
    if kind == 'done':
        return Task(matter_id=1, title=text, done=True, done_at=stamp-timedelta(minutes=offset))
    if kind == 'upcoming':
        return Task(matter_id=1, title=text, kind='deadline', due_on=date.today()+timedelta(days=offset))
    return CalendarEvent(matter_id=1, title=text, starts_at=stamp+timedelta(minutes=offset))


@pytest.mark.parametrize('kind', LIMITS)
@pytest.mark.parametrize('available', [True, False])
def test_excluded_text_never_enters_prompt_or_fallback(app, client, monkeypatch, kind, available):
    from app import llm
    from app.extensions import db
    with app.app_context():
        records=[add_record(kind, text) for text in EXCLUDED + ['Reviewed witness statement']]
        db.session.add_all(records); db.session.commit()
        ids=[r.id for r in records]
        model=type(records[0])
    prompts=[]
    def complete(prompt, **kwargs):
        prompts.append(prompt)
        if not available:
            raise llm.LLMUnavailable('Synthetic unavailable provider')
        return json.dumps({'subject':'Review', 'body':'Reviewed witness statement'})
    monkeypatch.setattr(llm, 'complete', complete)
    response=client.post('/ai/matter/1/update-email', data={'_csrf':client.tok})
    assert response.status_code == 200 and len(prompts) == 1
    output=prompts[0] + unescape(response.get_data(as_text=True))
    for text in EXCLUDED:
        assert text.strip() not in output
    assert 'Reviewed witness statement' in output
    with app.app_context():
        original=[db.session.get(model, ident) for ident in ids]
        assert [(r.description if kind == 'work' else r.title) for r in original] == EXCLUDED + ['Reviewed witness statement']


@pytest.mark.parametrize('kind,limit', LIMITS.items())
def test_exclusions_do_not_crowd_out_eligible_records(app, kind, limit):
    from app.extensions import db
    from app.models import Matter
    from app.blueprints.ai import update_facts
    with app.app_context():
        for i in range(limit+2):
            db.session.add(add_record(kind, f'[internal] Cobalt {i}', offset=0))
        for i in range(limit+1):
            db.session.add(add_record(kind, f'Witness statement {i}', offset=i+1))
        db.session.commit()
        rows=update_facts(db.session.get(Matter,1))[kind]
        assert len(rows) == limit
        assert [(r.description if kind == 'work' else r.title) for r in rows] == [f'Witness statement {i}' for i in range(limit)]
