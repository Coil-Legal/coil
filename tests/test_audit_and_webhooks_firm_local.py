"""Coil QA #170 and #169: two more naive-UTC-via-plain-`dt`-filter reads, same class as
#147/#153/#155/#156/#161/#162/#163/#164/#168. #170: /audit and /audit/<matter> "Last run" read
AuditLog.created_at with `dt`. #169: /settings/webhooks' "Recent deliveries" When column reads
WebhookDelivery.last_at/created_at with `dt`. Both columns are naive UTC (default=now()); a
timestamp after 7pm Central has already rolled to the next calendar day in UTC.

Run: .venv/bin/python -m pytest tests/test_audit_and_webhooks_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

# 7:41pm Central (CDT, UTC-5) on Oct 6, 2026 is 00:41 UTC Oct 7.
EVENING_UTC = datetime(2026, 10, 7, 0, 41)


def test_audit_index_last_run_uses_firm_local_time(app):
    from app.extensions import db
    from app.models import AuditLog

    c, _csrf = staff(app)
    with app.app_context():
        log = AuditLog(action="case_audit_run", entity="case_audit", detail="1 matter")
        db.session.add(log)
        db.session.flush()
        log.created_at = EVENING_UTC
        db.session.commit()

    body = c.get("/audit").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body


def test_audit_matter_last_run_uses_firm_local_time(app):
    from app.extensions import db
    from app.models import AuditLog, Matter

    c, _csrf = staff(app)
    with app.app_context():
        log = AuditLog(action="case_audit_run", entity="case_audit", detail="1 matter")
        db.session.add(log)
        db.session.flush()
        log.created_at = EVENING_UTC
        db.session.commit()
        mid = Matter.query.first().id

    body = c.get(f"/audit/{mid}").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body


def test_webhook_delivery_when_column_uses_firm_local_time(app):
    from app.extensions import db
    from app.models import Webhook, WebhookDelivery

    c, _csrf = staff(app)
    with app.app_context():
        hook = Webhook(url="https://example.test/hook", events="matter.created")
        db.session.add(hook)
        db.session.flush()
        d = WebhookDelivery(webhook_id=hook.id, event="matter.created", status="ok", attempts=1)
        db.session.add(d)
        db.session.flush()
        d.created_at = EVENING_UTC
        d.last_at = EVENING_UTC
        db.session.commit()

    body = c.get("/settings/webhooks").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body
