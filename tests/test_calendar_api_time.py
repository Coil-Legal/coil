"""Calendar API timestamps must retain their intended instant after persistence."""
from datetime import datetime
import pytest
from app.extensions import db
from app.models import CalendarEvent, Firm, User
from app.blueprints.api import create_token, reset_rate_limits
from app.blueprints.calendar import feed_secret
from tests.test_phase1_independent import app, staff


def setup_api(app, zone='America/Chicago', scope='calendar:write'):
    reset_rate_limits()
    with app.app_context():
        Firm.get().timezone = zone
        _, raw = create_token(db.session.get(User, 1), 'Synthetic time review', [scope], 'full')
        db.session.commit()
    return {'Authorization': 'Bearer ' + raw}


@pytest.mark.parametrize('zone,source,wall,utc', [
    ('America/Chicago', '2026-10-05T14:00:00Z', '2026-10-05T09:00:00', '20261005T140000Z'),
    ('America/Chicago', '2026-10-05T09:00:00-05:00', '2026-10-05T09:00:00', '20261005T140000Z'),
    ('America/Chicago', '2026-10-05T00:30:00+09:00', '2026-10-04T10:30:00', '20261004T153000Z'),
    ('Asia/Tokyo', '2026-10-05T20:00:00Z', '2026-10-06T05:00:00', '20261005T200000Z'),
    ('UTC', '2026-10-05T09:00:00-05:00', '2026-10-05T14:00:00', '20261005T140000Z'),
    ('Invalid/Zone', '2026-10-05T09:00:00-05:00', '2026-10-05T14:00:00', '20261005T140000Z'),
    ('America/Chicago', '2026-11-01T01:30:00-05:00', '2026-11-01T01:30:00', '20261101T063000Z'),
    ('America/Chicago', '2026-10-05T09:00:00', '2026-10-05T09:00:00', '20261005T140000Z'),
])
def test_saved_api_time_matches_ui_and_feed(app, zone, source, wall, utc):
    headers = setup_api(app, zone)
    response = app.test_client().post('/api/v1/calendar', headers=headers,
                                    json={'title': 'QA API clock', 'starts_at': source})
    assert response.status_code == 201
    assert response.json['event']['starts_at'] == wall
    with app.app_context():
        event = CalendarEvent.query.one()
        assert event.starts_at == datetime.fromisoformat(wall)
        urls = [f'/calendar/feed/{feed_secret()}.ics', f'/calendar/feed/u/1/{feed_secret(1)}.ics']
    client, _ = staff(app)
    assert wall[:10] in client.get('/calendar/1/edit').get_data(as_text=True)
    for url in urls:
        body = app.test_client().get(url).get_data(as_text=True)
        assert 'DTSTART:' + utc + '\r\n' in body


@pytest.mark.parametrize('source', ['2026-03-08T02:30:00', '2026-03-08T01:30:00',
                                    '2026-11-01T01:30:00-06:00', '2026-11-01T07:30:00Z'])
def test_unrepresentable_clock_time_is_rejected_without_saving(app, source):
    response = app.test_client().post('/api/v1/calendar', headers=setup_api(app),
                                    json={'title': 'QA invalid clock', 'starts_at': source})
    assert response.status_code == 400
    assert response.json['error']
    with app.app_context():
        assert CalendarEvent.query.count() == 0


def test_api_read_scope_cannot_create_even_a_valid_timestamp(app):
    response = app.test_client().post('/api/v1/calendar', headers=setup_api(app, scope='calendar:read'),
                                    json={'title': 'QA scope', 'starts_at': '2026-10-05T14:00:00Z'})
    assert response.status_code == 403
    with app.app_context():
        assert CalendarEvent.query.count() == 0


@pytest.mark.parametrize('source', ['0001-01-01T00:00:00Z', '9999-12-31T23:30:00'])
def test_date_overflow_returns_json_without_saving(app, source):
    response = app.test_client().post('/api/v1/calendar', headers=setup_api(app),
                                    json={'title': 'QA date boundary', 'starts_at': source})
    assert response.status_code == 400
    assert response.json['error']
    with app.app_context():
        assert CalendarEvent.query.count() == 0
