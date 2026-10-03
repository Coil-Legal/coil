"""Webhook delivery must never hold a database lock while an HTTP call is in flight (Coil QA #94).

The #93 fix moved delivery onto a background thread but kept one Session open across every
attempt. The second get() autoflushed the first attempt's result, opening a SQLite write
transaction that stayed open through each remaining HTTP call, so for several seconds after a
task was marked done every other save on testfirm failed with "database is locked". This holds
the second webhook's HTTP call open and proves a write on another connection goes straight
through, then that both delivery results are still recorded.

Run: .venv/bin/python -m pytest tests/test_webhook_delivery_no_lock.py -q
"""
import threading
import time

from tests.test_phase1_independent import app  # noqa: F401


def test_a_save_is_not_blocked_while_a_webhook_call_is_in_flight(app, monkeypatch):
    from app.extensions import db
    from app.models import Contact, Webhook, WebhookDelivery
    from app.blueprints import webhooks_out

    second_call_started = threading.Event()
    release = threading.Event()
    calls = []

    class _Ok:
        status_code = 200

    def post(url, data=None, headers=None, timeout=None, allow_redirects=None):
        calls.append(url)
        if len(calls) == 2:
            second_call_started.set()
            release.wait(10)
        return _Ok()

    monkeypatch.setattr(webhooks_out.requests, "post", post)

    with app.app_context():
        for n in (1, 2):
            db.session.add(Webhook(url=f"https://example.test/hook-{n}", events="task.completed", is_active=True))
        db.session.commit()
        app.testing = False  # the production path: attempts run on a background thread
        try:
            ids = webhooks_out.deliver_event("task.completed", {"id": 1})
        finally:
            app.testing = True
        assert len(ids) == 2

        assert second_call_started.wait(5), "the second webhook call never started"
        try:
            start = time.monotonic()
            db.session.add(Contact(kind="person", first_name="QA", last_name="Nolock 94"))
            db.session.commit()
            elapsed = time.monotonic() - start
        finally:
            release.set()
        assert elapsed < 1, f"a save waited {elapsed:.2f}s behind an in-flight webhook call"

        deadline = time.monotonic() + 5
        statuses = []
        while time.monotonic() < deadline:
            db.session.commit()  # fresh snapshot each poll
            statuses = [db.session.get(WebhookDelivery, i).status for i in ids]
            if statuses == ["ok", "ok"]:
                break
            time.sleep(0.05)
        assert statuses == ["ok", "ok"], f"both deliveries should be recorded, got {statuses}"
