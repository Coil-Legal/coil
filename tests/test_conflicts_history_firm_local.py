"""Coil QA #176: /conflicts History list's "When" column reads ConflictCheck.created_at
with the plain `dt` filter (naive UTC, default=now()) instead of `dtlocal`, the fix #173
already applied to the /conflicts/<id> detail page's Run line. Same class as
#147/#153/#155/#156/#161/#162/#163/#164/#168/#169/#170/#173.

Run: .venv/bin/python -m pytest tests/test_conflicts_history_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

# 7:41pm Central (CDT, UTC-5) on Oct 6, 2026 is 00:41 UTC Oct 7.
EVENING_UTC = datetime(2026, 10, 7, 0, 41)


def test_conflicts_history_when_column_uses_firm_local_time(app):
    from app.extensions import db
    from app.models import ConflictCheck

    c, _csrf = staff(app)
    with app.app_context():
        chk = ConflictCheck(query="QA Firm-Local Conflict", outcome="clear")
        db.session.add(chk)
        db.session.flush()
        chk.created_at = EVENING_UTC
        db.session.commit()

    body = c.get("/conflicts").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body
