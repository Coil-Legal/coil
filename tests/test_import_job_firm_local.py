"""Coil QA #168: /import's job history "When" column and /import/jobs/<id>'s "Run" line read
ImportJob.created_at with the plain `dt` filter (naive UTC), the same class as #147/#153/#155/
#156/#161/#162/#163/#164. A job run in the evening Central time, after 7pm, has a UTC
created_at that has already rolled to the next calendar day, so both pages read a day ahead of
the firm's own evening.

Run: .venv/bin/python -m pytest tests/test_import_job_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401


def test_import_job_history_and_detail_use_firm_local_time(app):
    from app.extensions import db
    from app.models import ImportJob

    c, _csrf = staff(app)
    with app.app_context():
        # 8:09pm Central (CDT, UTC-5) on Oct 6, 2026 is 01:09 UTC Oct 7: the server's naive
        # created_at has already rolled to the next day while the firm's evening has not.
        j = ImportJob(source="generic", entity="contacts", filename="qa.csv", rows=1,
                      created=1, updated=0, skipped=0, status="committed")
        db.session.add(j)
        db.session.flush()
        j.created_at = datetime(2026, 10, 7, 1, 9)
        db.session.commit()
        jid = j.id

    listing = c.get("/import").data.decode()
    assert "Oct 6, 2026" in listing
    assert "Oct 7, 2026" not in listing

    detail = c.get(f"/import/jobs/{jid}").data.decode()
    assert "Oct 6, 2026" in detail
    assert "Oct 7, 2026" not in detail
