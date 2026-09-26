"""Two simultaneous POST /api/v1/invoices for the same matter must not turn into an unhandled 500.

Same SQLite write race already retried on the builder screen (#51): two callers can both read
Firm.next_invoice_number before either commits, so the loser's commit hits a transient lock or a
UNIQUE-constraint violation on invoices.number once the winner has landed. invoice_create() called
build_for_matter() and commit() exactly once with no retry (Coil QA #56): matter 3088, one unbilled
entry, one call landed INV-1059 and the other came back a bare 500 with no invoice created.

Run: .venv/bin/python -m pytest tests/test_api_invoice_concurrency.py -q
"""
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

from tests.test_phase1_independent import app


def invoice_client(app):
    """A token already marked as used, so `_authenticate`'s own last_used_at commit does not fire
    (and get caught by a test's flaky-commit monkeypatch) before the route under test runs."""
    from app.extensions import db
    from app.models import User, TimeEntry
    from app.blueprints.api import create_token
    from app.models import now
    with app.app_context():
        user = db.session.get(User, 1)
        tok, raw = create_token(user, "QA invoice concurrency", "invoices:write,invoices:read")
        tok.last_used_at = now()
        db.session.add(TimeEntry(matter_id=1, user_id=1, date=date(2026, 1, 2), minutes=30,
                                 rate_cents=20000, description="Synthetic review", billable=True))
        db.session.commit()
    return app.test_client(), {"Authorization": f"Bearer {raw}"}


def post_invoice(client, headers, matter_id=1):
    return client.post("/api/v1/invoices", headers=headers, json={"matter_id": matter_id})


def test_a_transient_lock_error_is_retried_not_500(app, monkeypatch):
    """The first commit attempt raises the SQLite error two concurrent writers can trigger against
    each other. The route must retry with a fresh attempt and land the invoice, not a 500."""
    from app.extensions import db
    client, headers = invoice_client(app)
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError("commit", {}, Exception("database is locked"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_invoice(client, headers)
    assert r.status_code == 201, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated lock error"

    from app.models import Invoice
    with app.app_context():
        rows = Invoice.query.filter_by(matter_id=1).all()
        assert len(rows) == 1, "the retry must not leave a duplicate invoice behind"


def test_a_number_collision_is_retried_not_500(app, monkeypatch):
    """The real-world failure mode: two calls read the same Firm.next_invoice_number before either
    commits, so the loser's commit fails a UNIQUE constraint, not a generic lock. Also retried."""
    from app.extensions import db
    client, headers = invoice_client(app)
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("commit", {}, Exception("UNIQUE constraint failed: invoices.number"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_invoice(client, headers)
    assert r.status_code == 201, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated number collision"

    from app.models import Invoice
    with app.app_context():
        rows = Invoice.query.filter_by(matter_id=1).all()
        assert len(rows) == 1, "the retry must not leave a duplicate invoice behind"


def test_retries_exhausted_is_a_clean_error_not_a_crash(app, monkeypatch):
    """When every retry loses the race, the caller gets a normal 400, never an unhandled exception,
    and no partial invoice is left behind."""
    from app.extensions import db

    def always_locked():
        raise OperationalError("commit", {}, Exception("database is locked"))

    client, headers = invoice_client(app)
    monkeypatch.setattr(db.session, "commit", always_locked)
    r = post_invoice(client, headers)
    assert r.status_code == 400
    assert "took this invoice number" in r.json["error"]

    monkeypatch.undo()
    from app.models import Invoice
    with app.app_context():
        assert Invoice.query.filter_by(matter_id=1).count() == 0
