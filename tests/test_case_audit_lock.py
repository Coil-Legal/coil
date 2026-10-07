"""Coil QA #171: POST /audit/run returned HTTP 500 ("database is locked") when a second run
started shortly after a prior one finished. A full run walks every open matter with an LLM call
per PI matter and commits per matter, tens of seconds to minutes; a second run started before the
first's writes are all done (a double click, or the nightly `app.cli case_audit` cron landing on
top of a manual run) raced the first one's open SQLite transactions. run_case_audit() now takes a
process-wide flock (app/blueprints/caseaudit.py) so a second run is refused with a clear message
instead of crashing.

Run: .venv/bin/python -m pytest tests/test_case_audit_lock.py -q
"""
import fcntl

from tests.test_phase1_independent import app, staff  # noqa: F401


def test_second_run_while_locked_is_refused_not_a_crash(app):
    from app.blueprints.caseaudit import _LOCK_PATH

    c, tok = staff(app)
    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    held = _LOCK_PATH.open("a+b")
    try:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        r = c.post("/audit/run", data={"_csrf": tok})
        assert r.status_code == 302
        r = c.get(r.headers["Location"])
        assert r.status_code == 200
        assert "already running" in r.data.decode()
    finally:
        fcntl.flock(held, fcntl.LOCK_UN)
        held.close()


def test_run_case_audit_raises_when_lock_held(app):
    from app.blueprints.caseaudit import AuditAlreadyRunning, _LOCK_PATH, run_case_audit

    _LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    held = _LOCK_PATH.open("a+b")
    try:
        fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with app.app_context():
            import pytest
            with pytest.raises(AuditAlreadyRunning):
                run_case_audit()
    finally:
        fcntl.flock(held, fcntl.LOCK_UN)
        held.close()


def test_run_case_audit_still_works_once_unlocked(app):
    from app.blueprints.caseaudit import run_case_audit

    with app.app_context():
        r = run_case_audit()
        assert r["matters"] == 1
