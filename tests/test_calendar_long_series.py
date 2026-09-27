"""Calendar windows must not silently truncate an established series."""
from datetime import date, datetime, timedelta

import pytest
import re
from dateutil.relativedelta import relativedelta
from app.models import CalendarEvent
from tests.test_phase1_independent import app, staff


@pytest.mark.parametrize('frequency,step', [
    ('daily', relativedelta(days=1)), ('weekly', relativedelta(weeks=1)),
    ('biweekly', relativedelta(weeks=2)), ('monthly', relativedelta(months=1)),
    ('yearly', relativedelta(years=1)),
])
def test_series_survives_past_one_thousand_occurrences(frequency, step):
    origin = datetime(2000, 1, 31, 9)
    event = CalendarEvent(starts_at=origin, recurrence=frequency)
    wanted = origin + step * 1005
    assert list(event.occurrences(wanted, wanted + timedelta(seconds=1))) == [wanted]


def test_wide_window_has_no_hidden_count_limit():
    origin = datetime(2020, 1, 1)
    event = CalendarEvent(starts_at=origin, recurrence='daily')
    actual = list(event.occurrences(origin, origin + timedelta(days=1002)))
    assert actual == [origin + timedelta(days=n) for n in range(1002)]


@pytest.mark.parametrize('start,end,expected', [
    (datetime(2027, 2, 28, 9), datetime(2027, 4, 1), [datetime(2027, 2, 28, 9), datetime(2027, 3, 31, 9)]),
    (datetime(2027, 2, 28, 9, 0, 1), datetime(2027, 3, 31, 9), []),
    (datetime(1900, 1, 1), datetime(1900, 2, 1), [datetime(1900, 1, 31, 9)]),
])
def test_old_monthly_series_preserves_anchor_and_window_boundaries(start, end, expected):
    event = CalendarEvent(starts_at=datetime(1900, 1, 31, 9), recurrence='monthly')
    assert list(event.occurrences(start, end)) == expected


def test_old_series_honors_inclusive_until():
    event = CalendarEvent(starts_at=datetime(2020, 1, 1, 9), recurrence='daily',
                          recurrence_until=date(2026, 10, 2))
    assert list(event.occurrences(datetime(2026, 10, 1), datetime(2026, 11, 1))) == [
        datetime(2026, 10, 1, 9), datetime(2026, 10, 2, 9)]


@pytest.mark.parametrize('all_day', [True, False])
def test_saved_old_daily_series_renders_every_in_month_day(app, all_day):
    client, csrf = staff(app)
    data = {'_csrf': csrf, 'title': 'QA long series', 'date': '2020-01-01',
            'starts_at': '2020-01-01T09:00', 'ends_at': '2020-01-01T10:00',
            'recurrence': 'daily', 'recurrence_until': '2026-10-31', 'user_id': '1'}
    if all_day:
        data['all_day'] = '1'
    assert client.post('/calendar/new', data=data).status_code == 302
    for view in ('all', 'mine', '1'):
        response = client.get('/calendar?month=2026-10&user=' + view)
        assert response.status_code == 200
        days = [body for classes, body in re.findall(r'<div class="day ([^"]*)">(.*?)(?=<div class="day |</div>\s*</div>\s*<p)', response.get_data(as_text=True), re.S) if 'other' not in classes]
        assert len(days) == 31
        assert all(day.count('class="it event"') == 1 for day in days)


@pytest.mark.parametrize('frequency', ['daily', 'monthly', 'yearly'])
def test_last_representable_occurrence_does_not_overflow(frequency):
    start = datetime(9999, 12, 31, 9)
    event = CalendarEvent(starts_at=start, recurrence=frequency)
    assert list(event.occurrences(start, datetime.max)) == [start]
    assert list(event.occurrences(start, start)) == []
