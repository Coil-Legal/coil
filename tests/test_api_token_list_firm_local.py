"""Coil QA #163: /settings/api's "All tokens in the firm" table read a token's last_used_at
with the plain `dt` filter and its revoked_at with the plain `d` filter, both naive UTC, instead
of the firm-local `dtlocal`/`dlocal` filters (#147's class, see test_firm_local_today_sweep.py).
A token used or revoked in the evening Central time, after 7pm, has a UTC timestamp that has
already rolled to the next calendar day, so the page showed the wrong day.

Run: .venv/bin/python -m pytest tests/test_api_token_list_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401


def _owner_id(app):
    with app.app_context():
        from app.models import User
        return User.query.filter_by(email="owner@example.test").one().id


def test_last_used_and_revoked_render_firm_local_day(app):
    from app.extensions import db
    from app.models import ApiToken

    c, _csrf = staff(app)
    uid = _owner_id(app)
    with app.app_context():
        # 7:41pm Central (CDT, UTC-5) on Oct 6, 2026 is 00:41 UTC Oct 7: the server's naive
        # timestamp has already rolled to the next calendar day while the firm's evening has not.
        t = ApiToken(user_id=uid, name="QA2 API", token_hash="synthetic-hash-163", prefix="synth",
                    scopes="matters:read")
        db.session.add(t)
        db.session.flush()
        t.last_used_at = datetime(2026, 10, 7, 0, 41)
        t.revoked_at = datetime(2026, 10, 7, 0, 45)
        db.session.commit()

    body = c.get("/settings/api").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body
