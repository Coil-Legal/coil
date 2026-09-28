"""Rejected form boundaries must not crash or corrupt existing calendars."""
from datetime import datetime
import pytest
from app.extensions import db
from app.models import CalendarEvent, Firm
from app.blueprints.calendar import feed_secret
from tests.test_phase1_independent import app, staff

CASES = [
    ('UTC', {'starts_at': '9999-12-31T23:30'}),
    ('America/Chicago', {'starts_at': '9999-12-31T20:00', 'ends_at': '9999-12-31T21:00'}),
    ('Asia/Tokyo', {'starts_at': '0001-01-01T01:00', 'ends_at': '0001-01-01T02:00'}),
    ('UTC', {'all_day': '1', 'date': '9999-12-31'}),
    ('America/Chicago', {'starts_at': '2026-10-01T09:00', 'ends_at': '2026-10-01T10:00',
                         'recurrence': 'daily', 'recurrence_until': '9999-12-31'}),
]

@pytest.mark.parametrize('zone,fields', CASES)
@pytest.mark.parametrize('editing', [False, True])
def test_out_of_range_form_rejected_without_mutation(app, zone, fields, editing):
    with app.app_context():
        Firm.get().timezone = zone
        e = CalendarEvent(title='Original QA boundary', starts_at=datetime(2026, 10, 5, 9),
                          ends_at=datetime(2026, 10, 5, 10), recurrence='none', user_id=1)
        db.session.add(e); db.session.commit()
        original = (e.id, e.uid, e.title, e.starts_at, e.ends_at)
        urls = [f'/calendar/feed/{feed_secret()}.ics', f'/calendar/feed/u/1/{feed_secret(1)}.ics']
    client, csrf = staff(app)
    route = f'/calendar/{original[0]}/edit' if editing else '/calendar/new'
    result = client.post(route, data={'_csrf': csrf, 'title': 'Invalid QA boundary', **fields})
    if result.status_code == 302:
        # An accepted boundary must not poison either subscription.
        for url in urls:
            assert client.get(url).status_code == 200
    assert result.status_code == 200
    assert 'outside the supported calendar range' in result.get_data(as_text=True)
    with app.app_context():
        e = CalendarEvent.query.one()
        assert (e.id, e.uid, e.title, e.starts_at, e.ends_at) == original
    for url in urls:
        response = client.get(url)
        assert response.status_code == 200
        assert 'Original QA boundary' in response.get_data(as_text=True)
        assert 'Invalid QA boundary' not in response.get_data(as_text=True)

@pytest.mark.parametrize('zone', ['UTC', 'America/Chicago', 'Invalid/Timezone'])
def test_ordinary_form_default_end_still_saves(app, zone):
    with app.app_context():
        Firm.get().timezone = zone; db.session.commit()
    client, csrf = staff(app)
    r = client.post('/calendar/new', data={'_csrf': csrf, 'title': 'QA default hour',
                                          'starts_at': '2026-10-05T09:00'})
    assert r.status_code == 302
    with app.app_context():
        e = CalendarEvent.query.one()
        assert e.starts_at == datetime(2026, 10, 5, 9)
        assert e.ends_at == datetime(2026, 10, 5, 10)


def test_api_naive_conversion_overflow_returns_json(app):
    from tests.test_calendar_api_time import setup_api
    response = app.test_client().post('/api/v1/calendar', headers=setup_api(app, 'Asia/Tokyo'),
        json={'title': 'QA lower boundary', 'starts_at': '0001-01-01T01:00:00'})
    assert response.status_code == 400
    assert 'outside the supported calendar range' in response.json['error']
    with app.app_context():
        assert CalendarEvent.query.count() == 0


def test_csv_all_day_exclusive_end_overflow_is_row_error(app):
    from tests.test_calendar_import_time import upload
    from tests.test_importer import _job, _commit
    client, token = upload(app, '9999-12-31', all_day='Yes')
    result = _job(app, _commit(client, token))
    assert result['created'] == result['updated'] == 0 and result['errors'], result
    with app.app_context():
        assert CalendarEvent.query.count() == 0
