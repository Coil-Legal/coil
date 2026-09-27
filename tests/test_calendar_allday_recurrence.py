"""All-day subscriptions should carry the same month/year dates as the UI."""
from datetime import date, datetime
import pytest
from dateutil.rrule import rrulestr
from app.blueprints.calendar import build_ics, feed_secret
from app.models import CalendarEvent
from app.extensions import db
from tests.test_phase1_independent import app, staff


def expanded_dates(body):
    lines = body.replace('\r\n ', '').splitlines()
    start = next(l.split(':', 1)[1] for l in lines if l.startswith('DTSTART;VALUE=DATE:'))
    rule = next(l.split(':', 1)[1] for l in lines if l.startswith('RRULE:'))
    return [d.date() for d in rrulestr(rule, dtstart=datetime.strptime(start, '%Y%m%d'))]


@pytest.mark.parametrize('year,day', [(2027, 29), (2027, 30), (2027, 31),
                                    (2028, 29), (2028, 30), (2028, 31), (2027, 28)])
def test_monthly_dates_match_screen(year, day):
    event = CalendarEvent(id=1, uid='qa-month-end', title='QA monthly date', all_day=True,
                          starts_at=datetime(year, 1, day), recurrence='monthly',
                          recurrence_until=date(year, 5, 31))
    screen = [d.date() for d in event.occurrences(datetime(year, 1, 1), datetime(year, 6, 1))]
    assert len(screen) == 5
    assert expanded_dates(build_ics([event], tz_name='America/Chicago')) == screen


def test_yearly_leap_date_matches_screen_through_next_leap_year():
    event = CalendarEvent(id=1, uid='qa-leap', title='QA yearly date', all_day=True,
                          starts_at=datetime(2024, 2, 29), recurrence='yearly',
                          recurrence_until=date(2028, 3, 1))
    expected = [date(2024, 2, 29), date(2025, 2, 28), date(2026, 2, 28),
                date(2027, 2, 28), date(2028, 2, 29)]
    assert [d.date() for d in event.occurrences(datetime(2024, 1, 1), datetime(2029, 1, 1))] == expected
    assert expanded_dates(build_ics([event])) == expected


@pytest.mark.parametrize('recurrence,start,until,expected', [
    ('monthly', '2027-01-31', '2027-04-30', [date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31), date(2027, 4, 30)]),
    ('yearly', '2024-02-29', '2028-03-01', [date(2024, 2, 29), date(2025, 2, 28), date(2026, 2, 28), date(2027, 2, 28), date(2028, 2, 29)]),
])
def test_saved_all_day_series_matches_firm_and_user_feeds(app, recurrence, start, until, expected):
    client, csrf = staff(app)
    r = client.post('/calendar/new', data={'_csrf': csrf, 'title': 'QA date recurrence',
        'all_day': '1', 'date': start, 'recurrence': recurrence, 'recurrence_until': until, 'user_id': '1'})
    assert r.status_code == 302
    with app.app_context():
        assert CalendarEvent.query.one().starts_at.date() == date.fromisoformat(start)
        urls = [f'/calendar/feed/{feed_secret()}.ics', f'/calendar/feed/u/1/{feed_secret(1)}.ics']
    for url in urls:
        response = app.test_client().get(url)
        assert response.status_code == 200
        assert expanded_dates(response.get_data(as_text=True)) == expected


@pytest.mark.parametrize('recurrence,expected', [('daily', 'FREQ=DAILY'), ('weekly', 'FREQ=WEEKLY'),
                                               ('biweekly', 'FREQ=WEEKLY;INTERVAL=2')])
def test_other_all_day_rules_keep_existing_shape(recurrence, expected):
    event = CalendarEvent(id=1, uid='qa-control', title='Control', all_day=True,
                          starts_at=datetime(2027, 1, 31), recurrence=recurrence)
    assert 'RRULE:'+expected+'\r\n' in build_ics([event])
