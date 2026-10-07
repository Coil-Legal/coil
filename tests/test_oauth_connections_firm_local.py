"""Coil QA #164: /oauth/connections rendered a connected app's "Connected" and "Last used"
columns with the plain `d`/`dt` filters, naive UTC, instead of the firm-local `dlocal`/
`dtlocal` filters already used elsewhere for this exact class of bug (#147, #163). A
connection made or used in the evening Central time, after 7pm, has a UTC timestamp that has
already rolled to the next calendar day, so the page showed the wrong day/time.

Run: .venv/bin/python -m pytest tests/test_oauth_connections_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401


def _owner_id(app):
    with app.app_context():
        from app.models import User
        return User.query.filter_by(email="owner@example.test").one().id


def test_connected_and_last_used_render_firm_local_day(app):
    from app.extensions import db
    from app.models import ApiToken, OAuthClient

    c, _csrf = staff(app)
    uid = _owner_id(app)
    with app.app_context():
        client = OAuthClient(client_id="qa164-client", client_name="QA164 Connector")
        db.session.add(client)
        db.session.flush()
        # 7:41pm Central (CDT, UTC-5) on Oct 6, 2026 is 00:41 UTC Oct 7: the server's naive
        # timestamp has already rolled to the next calendar day while the firm's evening has not.
        t = ApiToken(user_id=uid, name="QA164 OAuth", token_hash="synthetic-hash-164", prefix="synth",
                     scopes="matters:read", oauth_client_id=client.id,
                     expires_at=datetime(2099, 1, 1))
        db.session.add(t)
        db.session.flush()
        t.created_at = datetime(2026, 10, 7, 0, 41)
        t.last_used_at = datetime(2026, 10, 7, 0, 48)
        db.session.commit()

    body = c.get("/oauth/connections").data.decode()
    assert "Oct 6, 2026" in body
    assert "Oct 7, 2026" not in body
