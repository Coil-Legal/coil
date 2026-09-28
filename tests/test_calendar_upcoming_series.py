"""A recurring series that already started must still surface its next occurrence in Upcoming events."""
from datetime import datetime
from flask import template_rendered
from app.extensions import db
from app.models import CalendarEvent
from app.blueprints import calendar as calendar_bp
from tests.test_phase1_independent import app, staff


def _upcoming(app, client, monkeypatch, fixed_now):
    monkeypatch.setattr(calendar_bp, "now", lambda: fixed_now)
    captured = []

    def capture(sender, template, context, **extra):
        captured.append(context)

    with template_rendered.connected_to(capture, app):
        r = client.get("/calendar?month=2026-09")
        assert r.status_code == 200
    return captured[-1]["upcoming"]


def test_started_series_still_surfaces_its_next_occurrence(app, monkeypatch):
    with app.app_context():
        db.session.add(CalendarEvent(title="QA daily series", starts_at=datetime(2026, 9, 26, 9, 0),
                                     ends_at=datetime(2026, 9, 26, 10, 0), all_day=False,
                                     recurrence="daily", recurrence_until=datetime(2026, 9, 30).date(),
                                     uid="qa-upcoming-started"))
        db.session.commit()
    client, _ = staff(app)
    # 08:30 on the 28th: the 26th and 27th occurrences are past, the 28th is still an hour away.
    rows = [(r["title"], r["starts_at"]) for r in _upcoming(app, client, monkeypatch, datetime(2026, 9, 28, 8, 30))]
    assert rows.count(("QA daily series", datetime(2026, 9, 28, 9, 0))) == 1
    assert not any(title == "QA daily series" and at < datetime(2026, 9, 28, 9, 0) for title, at in rows)


def test_finished_series_is_absent_from_upcoming(app, monkeypatch):
    with app.app_context():
        db.session.add(CalendarEvent(title="QA finished series", starts_at=datetime(2026, 9, 26, 9, 0),
                                     ends_at=datetime(2026, 9, 26, 10, 0), all_day=False,
                                     recurrence="daily", recurrence_until=datetime(2026, 9, 30).date(),
                                     uid="qa-upcoming-finished"))
        db.session.commit()
    client, _ = staff(app)
    rows = _upcoming(app, client, monkeypatch, datetime(2026, 10, 5, 8, 0))
    assert not any(r["title"] == "QA finished series" for r in rows)


def test_upcoming_orders_series_occurrence_among_one_off_events(app, monkeypatch):
    with app.app_context():
        db.session.add_all([
            CalendarEvent(title="QA daily series", starts_at=datetime(2026, 9, 26, 9, 0),
                         ends_at=datetime(2026, 9, 26, 10, 0), all_day=False,
                         recurrence="daily", recurrence_until=datetime(2026, 9, 30).date(), uid="qa-upcoming-order"),
            CalendarEvent(title="QA one-off before", starts_at=datetime(2026, 9, 28, 8, 45),
                         ends_at=datetime(2026, 9, 28, 9, 15), all_day=False, recurrence="none", uid="qa-oneoff-a"),
            CalendarEvent(title="QA one-off after", starts_at=datetime(2026, 9, 28, 9, 30),
                         ends_at=datetime(2026, 9, 28, 10, 0), all_day=False, recurrence="none", uid="qa-oneoff-b"),
        ])
        db.session.commit()
    client, _ = staff(app)
    rows = [(r["title"], r["starts_at"]) for r in _upcoming(app, client, monkeypatch, datetime(2026, 9, 28, 8, 30))]
    order = [title for title, _at in sorted(rows, key=lambda r: r[1])]
    assert order.index("QA one-off before") < order.index("QA daily series") < order.index("QA one-off after")
