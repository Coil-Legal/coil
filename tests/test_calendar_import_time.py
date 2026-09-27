"""Synthetic CSV calendar preview/commit/re-import timestamp acceptance."""
import csv
import io
from datetime import datetime
import pytest
from app.extensions import db
from app.models import CalendarEvent, Firm
from app.blueprints.calendar import feed_secret
from tests.test_phase1_independent import app, staff
from tests.test_importer import _upload, _commit, _job


def upload(app, start, end='', all_day='No', zone='America/Chicago'):
    client, client_token = staff(app)
    client.tok = client_token
    with app.app_context():
        Firm.get().timezone = zone
        db.session.commit()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['ID', 'Title', 'Start', 'End', 'All Day'])
    writer.writerow(['qa-import-clock', 'QA CSV clock', start, end, all_day])
    token = _upload(client, 'calendar', buf.getvalue(), 'calendar.csv')
    return client, token


@pytest.mark.parametrize('zone,start,end,wall_start,wall_end,utc_start,utc_end', [
    ('America/Chicago', '2026-10-05T14:00:00Z', '2026-10-05T15:00:00Z', '2026-10-05T09:00:00', '2026-10-05T10:00:00', '20261005T140000Z', '20261005T150000Z'),
    ('America/Chicago', '2026-10-05T00:30:00+09:00', '2026-10-05T01:30:00+09:00', '2026-10-04T10:30:00', '2026-10-04T11:30:00', '20261004T153000Z', '20261004T163000Z'),
    ('Asia/Tokyo', '2026-10-05T20:00:00Z', '', '2026-10-06T05:00:00', '2026-10-06T06:00:00', '20261005T200000Z', '20261005T210000Z'),
    ('UTC', '2026-10-05 09:00:00 -0500', '', '2026-10-05T14:00:00', '2026-10-05T15:00:00', '20261005T140000Z', '20261005T150000Z'),
    ('Invalid/Zone', '2026-10-05T09:00:00-05:00', '', '2026-10-05T14:00:00', '2026-10-05T15:00:00', '20261005T140000Z', '20261005T150000Z'),
    ('America/Chicago', '10/05/2026 09:00 AM', '10/05/2026 10:00 AM', '2026-10-05T09:00:00', '2026-10-05T10:00:00', '20261005T140000Z', '20261005T150000Z'),
    ('America/Chicago', '2026-11-01T01:30:00-05:00', '', '2026-11-01T01:30:00', '2026-11-01T02:30:00', '20261101T063000Z', '20261101T083000Z'),
])
def test_import_preserves_instant_and_local_values(app, zone, start, end, wall_start, wall_end, utc_start, utc_end):
    client, token = upload(app, start, end, zone=zone)
    assert client.get('/import/preview/' + token).status_code == 200
    result = _job(app, _commit(client, token))
    assert result['created'] == 1 and not result['errors'], result
    with app.app_context():
        event = CalendarEvent.query.one()
        assert event.starts_at == datetime.fromisoformat(wall_start)
        assert event.ends_at == datetime.fromisoformat(wall_end)
        urls = [f'/calendar/feed/{feed_secret()}.ics', f'/calendar/feed/u/1/{feed_secret(1)}.ics']
    for url in urls:
        body = app.test_client().get(url).get_data(as_text=True)
        assert 'DTSTART:' + utc_start + '\r\n' in body
        assert 'DTEND:' + utc_end + '\r\n' in body


@pytest.mark.parametrize('start,end', [
    ('2026-03-08T02:30:00', ''), ('2026-03-08T01:30:00', ''),
    ('2026-03-08T00:30:00', '2026-03-08T02:30:00'),
    ('2026-11-01T01:30:00-06:00', ''),
    ('2026-11-01T00:30:00-05:00', '2026-11-01T01:30:00-06:00'),
    ('2026-10-05T09:00:00', 'not-a-date'),
])
def test_invalid_clock_row_is_reported_and_not_created(app, start, end):
    client, token = upload(app, start, end)
    result = _job(app, _commit(client, token))
    assert result['created'] == result['updated'] == 0, result
    assert result['errors'], result
    with app.app_context():
        assert CalendarEvent.query.count() == 0


def test_rejected_reimport_keeps_existing_event_and_uid(app):
    client, token = upload(app, '2026-10-05T09:00:00')
    assert _job(app, _commit(client, token))['created'] == 1
    with app.app_context():
        event = CalendarEvent.query.one()
        before = (event.id, event.uid, event.starts_at, event.ends_at, event.title)
    client, token = upload(app, '2026-03-08T02:30:00')
    result = _job(app, _commit(client, token))
    assert result['updated'] == 0 and result['errors']
    with app.app_context():
        event = CalendarEvent.query.one()
        assert (event.id, event.uid, event.starts_at, event.ends_at, event.title) == before


def test_all_day_date_stays_literal(app):
    client, token = upload(app, '2026-03-08', all_day='Yes')
    assert _job(app, _commit(client, token))['created'] == 1
    with app.app_context():
        event = CalendarEvent.query.one()
        assert event.all_day and event.starts_at == datetime(2026, 3, 8)


@pytest.mark.parametrize('start', ['05-Oct-2026', '10-05-2026', '20261005'])
def test_legacy_date_formats_are_not_mistaken_for_offsets(app, start):
    client, token = upload(app, start)
    result = _job(app, _commit(client, token))
    assert result['created'] == 1 and not result['errors']
    with app.app_context():
        assert CalendarEvent.query.one().starts_at == datetime(2026, 10, 5)


def test_legacy_time_format_with_offset_is_converted(app):
    client, token = upload(app, '10/05/2026 09:00 AM -0500', zone='UTC')
    result = _job(app, _commit(client, token))
    assert result['created'] == 1 and not result['errors']
    with app.app_context():
        assert CalendarEvent.query.one().starts_at == datetime(2026, 10, 5, 14)


@pytest.mark.parametrize('start', ['0001-01-01T00:00:00Z', '9999-12-31T23:30:00'])
def test_datetime_boundary_errors_remain_row_errors(app, start):
    client, token = upload(app, start)
    result = _job(app, _commit(client, token))
    assert result['created'] == 0 and result['errors']
