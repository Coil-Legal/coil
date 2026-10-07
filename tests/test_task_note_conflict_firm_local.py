"""Coil QA #173: three more naive-UTC-via-plain-`dt`-filter reads, same class as
#147/#153/#155/#156/#161/#162/#163/#164/#168/#170/#169. Task detail's Created/Completed
rows, a matter's Notes card timeline, and /conflicts/<id>'s "Run" line all read naive-UTC
`created_at`/`done_at` columns with `dt` instead of `dtlocal`; a timestamp after 7pm
Central has already rolled to the next calendar day in UTC.

Run: .venv/bin/python -m pytest tests/test_task_note_conflict_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

# 7:41pm Central (CDT, UTC-5) on Oct 6, 2026 is 00:41 UTC Oct 7.
EVENING_UTC = datetime(2026, 10, 7, 0, 41)


def test_task_detail_created_and_completed_use_firm_local_time(app):
    from app.extensions import db
    from app.models import Task

    c, _csrf = staff(app)
    with app.app_context():
        t = Task(title="QA firm-local task", kind="task", done=True)
        db.session.add(t)
        db.session.flush()
        t.created_at = EVENING_UTC
        t.done_at = EVENING_UTC
        db.session.commit()
        tid = t.id

    body = c.get(f"/tasks/{tid}").data.decode()
    assert body.count("Oct 6, 2026") == 2
    assert "Oct 7, 2026" not in body


def test_matter_notes_card_uses_firm_local_time(app):
    from app.extensions import db
    from app.models import Note

    c, _csrf = staff(app)
    with app.app_context():
        n = Note(matter_id=1, body="QA firm-local note")
        db.session.add(n)
        db.session.flush()
        n.created_at = EVENING_UTC
        db.session.commit()

    body = c.get("/matters/1").data.decode()
    note_entry = body[body.index("QA firm-local note") - 200:body.index("QA firm-local note")]
    assert "Oct 6, 2026" in note_entry
    assert "Oct 7, 2026" not in note_entry


def test_conflict_check_detail_run_line_uses_firm_local_time(app):
    from app.extensions import db
    from app.models import ConflictCheck

    c, _csrf = staff(app)
    with app.app_context():
        chk = ConflictCheck(query="QA firm-local conflict")
        db.session.add(chk)
        db.session.flush()
        chk.created_at = EVENING_UTC
        db.session.commit()
        chk_id = chk.id

    body = c.get(f"/conflicts/{chk_id}").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body
