"""Calendar wall times must survive a UTC round trip without moving."""
from datetime import datetime

import pytest

from tests.test_phase1_independent import app, staff
from app.extensions import db
from app.models import CalendarEvent, Firm
from app.blueprints.calendar import feed_secret


def zone(app, name):
    with app.app_context():
        Firm.get().timezone = name
        db.session.commit()


@pytest.mark.parametrize('editing', [False, True])
@pytest.mark.parametrize('tz,start,end,field', [
    ('America/Chicago', '2026-03-08T02:30', '2026-03-08T03:30', 'start'),
    ('America/Chicago', '2026-03-08T01:30', '2026-03-08T02:30', 'end'),
    ('America/Chicago', '2026-03-08T01:30', '', 'end'),
    ('Australia/Lord_Howe', '2026-10-04T02:15', '2026-10-04T03:15', 'start'),
])
def test_gap_rejected_without_persistence(app, editing, tz, start, end, field):
    zone(app, tz)
    client, csrf = staff(app)
    path = '/calendar/new'
    event_id = None
    if editing:
        with app.app_context():
            e = CalendarEvent(title='Original synthetic event', starts_at=datetime(2026, 1, 8, 9),
                              ends_at=datetime(2026, 1, 8, 10), recurrence='none')
            db.session.add(e)
            db.session.commit()
            event_id = e.id
            path = f'/calendar/{e.id}/edit'
    response = client.post(path, data={'_csrf': csrf, 'title': 'QA DST gap',
                                     'starts_at': start, 'ends_at': end,
                                     'notes': 'Preserve this draft', 'recurrence': 'none'})
    assert response.status_code == 200, response.location
    html = response.get_data(as_text=True)
    assert f'The {field} time does not exist in {tz}' in html
    assert 'QA DST gap' in html and 'Preserve this draft' in html and start in html
    with app.app_context():
        assert CalendarEvent.query.count() == int(editing)
        if editing:
            e = db.session.get(CalendarEvent, event_id)
            assert (e.title, e.starts_at, e.ends_at) == (
                'Original synthetic event', datetime(2026, 1, 8, 9), datetime(2026, 1, 8, 10))
    # Correcting the same form succeeds, with no duplicate from the rejected attempt.
    response = client.post(path, data={'_csrf': csrf, 'title': 'QA DST corrected',
                                     'starts_at': '2026-03-09T09:00', 'ends_at': '2026-03-09T10:00'})
    assert response.status_code == 302
    with app.app_context():
        assert CalendarEvent.query.count() == 1


@pytest.mark.parametrize('tz,start,end,utc_start,utc_end', [
    ('America/Chicago', '2026-03-08T01:30', '2026-03-08T03:30', '20260308T073000Z', '20260308T083000Z'),
    ('America/Chicago', '2026-03-08T03:00', '2026-03-08T04:00', '20260308T080000Z', '20260308T090000Z'),
    ('America/Chicago', '2026-11-01T01:30', '2026-11-01T02:30', '20261101T063000Z', '20261101T083000Z'),
    ('America/Phoenix', '2026-03-08T02:30', '2026-03-08T03:30', '20260308T093000Z', '20260308T103000Z'),
    ('UTC', '2026-03-08T02:30', '2026-03-08T03:30', '20260308T023000Z', '20260308T033000Z'),
])
def test_valid_wall_times_and_feed(app, tz, start, end, utc_start, utc_end):
    zone(app, tz)
    client, csrf = staff(app)
    response = client.post('/calendar/new', data={'_csrf': csrf, 'title': 'QA valid wall time',
                                                 'starts_at': start, 'ends_at': end})
    assert response.status_code == 302
    with app.app_context():
        e = CalendarEvent.query.one()
        assert e.starts_at == datetime.fromisoformat(start)
        secret = feed_secret()
    feed = client.get(f'/calendar/feed/{secret}.ics').get_data(as_text=True)
    assert f'DTSTART:{utc_start}' in feed and f'DTEND:{utc_end}' in feed


def test_all_day_transition_date_unchanged(app):
    zone(app, 'America/Chicago')
    client, csrf = staff(app)
    response = client.post('/calendar/new', data={'_csrf': csrf, 'title': 'QA all day',
                                                 'all_day': '1', 'date': '2026-03-08'})
    assert response.status_code == 302
    with app.app_context():
        e = CalendarEvent.query.one()
        assert e.all_day and e.starts_at == datetime(2026, 3, 8) and e.ends_at is None


def test_invalid_edit_missing_start_keeps_original(app):
    client, csrf = staff(app)
    with app.app_context():
        e = CalendarEvent(title='Original', starts_at=datetime(2026, 1, 8, 9), recurrence='none')
        db.session.add(e)
        db.session.commit()
        event_id = e.id
    response = client.post(f'/calendar/{event_id}/edit', data={'_csrf': csrf, 'title': 'Draft', 'starts_at': ''})
    assert response.status_code == 200
    assert 'A title and a start date are required.' in response.get_data(as_text=True)
    with app.app_context():
        assert db.session.get(CalendarEvent, event_id).title == 'Original'
