"""Recurrence cutoff uses an inclusive local date and DTSTART's value type."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from dateutil.rrule import rrulestr
from app.blueprints.calendar import build_ics, feed_secret
from app.models import CalendarEvent, Firm
from app.extensions import db
from tests.test_phase1_independent import app, staff


def property_value(body, prefix):
    return next(line.split(':', 1)[1] for line in body.splitlines() if line.startswith(prefix))


@pytest.mark.parametrize('all_day', [False, True])
@pytest.mark.parametrize('zone,hour', [('America/Chicago', 23), ('Asia/Tokyo', 1),
                                     ('Pacific/Kiritimati', 0), ('UTC', 12)])
def test_final_day_matches_screen_occurrences(all_day, zone, hour):
    start = datetime(2026, 10, 5, hour)
    event = CalendarEvent(id=1, uid='qa-cutoff', title='Synthetic cutoff', all_day=all_day,
                          starts_at=start, ends_at=start + timedelta(minutes=30),
                          recurrence='daily', recurrence_until=date(2026, 10, 7))
    body = build_ics([event], tz_name=zone)
    start_value = property_value(body, 'DTSTART')
    rule = property_value(body, 'RRULE:')
    until = rule.split('UNTIL=')[1]
    if all_day:
        assert until == '20261007', 'DATE DTSTART requires DATE UNTIL'
        parsed_start = datetime.strptime(start_value, '%Y%m%d')
    else:
        parsed_start = datetime.strptime(start_value, '%Y%m%dT%H%M%SZ').replace(tzinfo=ZoneInfo('UTC'))
    expanded = list(rrulestr(rule, dtstart=parsed_start))
    dates = [dt.date() if all_day else dt.astimezone(ZoneInfo(zone)).date() for dt in expanded]
    screen = [dt.date() for dt in event.occurrences(datetime(2026, 10, 1), datetime(2026, 11, 1))]
    assert dates == screen == [date(2026, 10, d) for d in (5, 6, 7)]


@pytest.mark.parametrize('all_day', [False, True])
def test_form_saved_cutoff_in_firm_and_owner_feed(app, all_day):
    client, csrf = staff(app)
    with app.app_context():
        Firm.get().timezone = 'America/Chicago'
        db.session.commit()
        urls = [f'/calendar/feed/{feed_secret()}.ics', f'/calendar/feed/u/1/{feed_secret(1)}.ics']
    data = {'_csrf': csrf, 'title': 'QA inclusive cutoff', 'starts_at': '2026-10-05T23:00',
            'ends_at': '2026-10-05T23:30', 'date': '2026-10-05', 'user_id': '1',
            'recurrence': 'daily', 'recurrence_until': '2026-10-07'}
    if all_day:
        data['all_day'] = '1'
    assert client.post('/calendar/new', data=data).status_code == 302
    for url in urls:
        response = app.test_client().get(url)
        assert response.status_code == 200
        expected = '20261007' if all_day else '20261008T045959Z'
        assert property_value(response.get_data(as_text=True), 'RRULE:') == 'FREQ=DAILY;UNTIL=' + expected


@pytest.mark.parametrize('zone', ['UTC', 'Invalid/Zone'])
def test_utc_and_invalid_zone_keep_existing_fallback(zone):
    event = CalendarEvent(id=1, uid='qa-fallback', title='Control', all_day=False,
                          starts_at=datetime(2026, 10, 5, 9), recurrence='weekly',
                          recurrence_until=date(2026, 10, 7))
    body = build_ics([event], tz_name=zone)
    assert 'RRULE:FREQ=WEEKLY;UNTIL=20261007T235959Z' in body


@pytest.mark.parametrize('recurrence', ['none', 'daily'])
def test_missing_cutoff_is_not_invented(recurrence):
    event = CalendarEvent(id=1, uid='qa-open', title='Control', all_day=False,
                          starts_at=datetime(2026, 10, 5, 9), recurrence=recurrence)
    body = build_ics([event], tz_name='America/Chicago')
    assert 'UNTIL=' not in body
    assert ('RRULE:FREQ=DAILY' in body) == (recurrence == 'daily')
