"""Outgoing webhook delivery must not block the request that triggered it (Coil QA #93).

Grok measured marking a task done at 12.6 seconds on testfirm, which has seven webhooks
subscribed to task.completed. deliver_event() used to call attempt_delivery() once per
webhook synchronously, in the same thread as the request, so a slow or dead endpoint added
TIMEOUT_SECONDS to every task.completed, matter.closed, invoice.sent/paid and
payment.received action - enough endpoints or one slow enough and the user sees a 502 while
the change is already committed. Outside TESTING, deliver_event() now hands the HTTP
attempts to a background thread and returns immediately; this flips a test app into that
same mode to prove it.

Run: .venv/bin/python -m pytest tests/test_webhook_async_delivery.py -q
"""
import time

from tests.test_phase1_independent import app  # noqa: F401


def test_deliver_event_returns_before_a_slow_webhook_responds(app, monkeypatch):
    from app.extensions import db
    from app.models import Webhook, WebhookDelivery
    from app.blueprints import webhooks_out

    class _SlowResponse:
        status_code = 200

    def slow_post(url, data=None, headers=None, timeout=None, allow_redirects=None):
        time.sleep(1)
        return _SlowResponse()

    monkeypatch.setattr(webhooks_out.requests, "post", slow_post)

    with app.app_context():
        h = Webhook(url="https://example.test/slow-hook", events="task.completed", is_active=True)
        db.session.add(h)
        db.session.commit()
        app.testing = False  # exercise the production (off-thread) path, not the TESTING shortcut
        try:
            start = time.monotonic()
            ids = webhooks_out.deliver_event("task.completed", {"id": 1})
            elapsed = time.monotonic() - start
        finally:
            app.testing = True
        assert ids, "a delivery row should have been created"
        assert elapsed < 0.5, f"deliver_event waited {elapsed:.2f}s on a webhook that sleeps for 1s"

        d = db.session.get(WebhookDelivery, ids[0])
        assert d.status == "pending", "the HTTP attempt should not have run on the caller's thread yet"

        # db.session's own read holds a SQLite snapshot for the life of its transaction; commit
        # between polls to start a fresh one that can see the background thread's writes.
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline and d.status == "pending":
            db.session.commit()
            time.sleep(0.05)
            d = db.session.get(WebhookDelivery, ids[0])
        assert d.status == "ok" and d.attempts == 1, "the background thread should have delivered it"
