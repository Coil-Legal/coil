"""Generated dates must represent real local start times in the month grid."""
from datetime import datetime, date, timedelta, timezone
from flask import template_rendered
import pytest
from app.extensions import db
from app.models import CalendarEvent, Firm
from tests.test_phase1_independent import app, staff
from tests.test_calendar_timed_recurrence import expand
from app.blueprints.calendar import build_ics


@pytest.mark.parametrize('zone,origin,recurrence,missing', [
    ('America/Chicago', '2026-03-07T02:30', 'daily', '2026-03-08'),
    ('America/Chicago', '2026-03-01T02:30', 'weekly', '2026-03-08'),
    ('America/Chicago', '2026-02-22T02:30', 'biweekly', '2026-03-08'),
    ('America/Chicago', '2026-02-08T02:30', 'monthly', '2026-03-08'),
    ('America/Chicago', '2025-03-08T02:30', 'yearly', '2026-03-08'),
    ('Australia/Lord_Howe', '2026-10-03T02:15', 'daily', '2026-10-04'),
    ('Pacific/Apia', '2011-12-29T09:00', 'daily', '2011-12-30'),
])
def test_grid_omits_generated_nonexistent_start(app, zone, origin, recurrence, missing):
    start = datetime.fromisoformat(origin)
    absent = date.fromisoformat(missing)
    cutoff = absent + timedelta(days=370)
    with app.app_context():
        Firm.get().timezone = zone
        event = CalendarEvent(title='QA generated gap', starts_at=start,
                              ends_at=start + timedelta(hours=1), all_day=False,
                              recurrence=recurrence, recurrence_until=cutoff, uid='qa-gap')
        db.session.add(event); db.session.commit()
        body = build_ics([event], tz_name=zone)
        # dateutil emits imaginary candidates. The specified missing date is
        # an independent fixture fact; RFC 5545 3.3.10 excludes that instance.
        valid = {value.date() for value in expand(body) if value.date() != absent}
    client, _ = staff(app)
    captured = []
    def capture(sender, template, context, **extra):
        captured.append(context)
    with template_rendered.connected_to(capture, app):
        assert client.get('/calendar?month=' + missing[:7]).status_code == 200
    actual = {day for day, items in captured[-1]['items'].items()
              if any(item['kind'] == 'event' for item in items)}
    assert absent not in actual
    grid = {d for week in captured[-1]['weeks'] for d in week}
    assert actual == valid & grid
    with app.app_context():
        saved = CalendarEvent.query.one()
        assert (saved.starts_at, saved.ends_at, saved.uid) == (start, start + timedelta(hours=1), 'qa-gap')


@pytest.mark.parametrize('zone,all_day,origin,expected', [
    ('America/Chicago', False, '2026-10-31T01:30', ['2026-10-31', '2026-11-01', '2026-11-02']),
    ('America/Chicago', True, '2026-03-07T00:00', ['2026-03-07', '2026-03-08', '2026-03-09']),
    ('UTC', False, '2026-03-07T02:30', ['2026-03-07', '2026-03-08', '2026-03-09']),
    ('Invalid/Zone', False, '2026-03-07T02:30', ['2026-03-07', '2026-03-08', '2026-03-09']),
    ('America/Chicago', False, '2026-03-07T01:30', ['2026-03-07', '2026-03-08', '2026-03-09']),
])
def test_grid_retains_real_start_and_all_day_controls(app, zone, all_day, origin, expected):
    start = datetime.fromisoformat(origin)
    with app.app_context():
        Firm.get().timezone = zone
        db.session.add(CalendarEvent(title='QA control', starts_at=start,
          ends_at=start + timedelta(hours=1), all_day=all_day,
          recurrence='daily', recurrence_until=date.fromisoformat(expected[-1])))
        db.session.commit()
    client, _ = staff(app)
    contexts = []
    def capture(sender, template, context, **extra): contexts.append(context)
    with template_rendered.connected_to(capture, app):
        assert client.get('/calendar?month=' + expected[1][:7]).status_code == 200
    actual = [str(day) for day, items in contexts[-1]['items'].items()
              if any(item['kind'] == 'event' for item in items)]
    grid = {str(d) for week in contexts[-1]["weeks"] for d in week}
    assert actual == [day for day in expected if day in grid]
