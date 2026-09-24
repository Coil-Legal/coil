"""A transient SQLite write collision on /sign/doc/<token> must not turn into an unhandled 500.

Two tabs (or a double-click) posting the same signature at nearly the same instant can make
SQLite refuse whichever commit loses the race, even in WAL mode. Reproduced live (Coil QA #48):
one request returned a bare "Internal Server Error", the other completed normally, and exactly
one signature was stored. The trust deposit form already retries this class of error; the sign
route did not.

Run: .venv/bin/python -m pytest tests/test_signature_sign_concurrency.py -q
"""
import pytest
from sqlalchemy.exc import OperationalError

from tests.test_phase1_independent import app
from tests.test_phase1_document_integrity import signature_fixture


def test_a_transient_lock_error_is_retried_not_500(app, monkeypatch):
    from app.extensions import db
    sid, token = signature_fixture(app, None)
    client = app.test_client()

    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError("commit", {}, Exception("database is locked"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    monkeypatch.setattr("app.blueprints.signatures._email_signed_copies", lambda *a: None)
    r = client.post(f"/sign/doc/{token}", data={"signer_name": "Concurrent Signer", "agree": "1"})
    assert r.status_code == 200, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated lock error"

    from app.models import DocumentSignature
    with app.app_context():
        row = db.session.get(DocumentSignature, sid)
        assert row.status == "signed"
        assert row.signer_name == "Concurrent Signer"


def test_retries_exhausted_is_a_clean_error_not_a_crash(app, monkeypatch):
    from app.extensions import db
    sid, token = signature_fixture(app, None)
    client = app.test_client()

    def always_locked():
        raise OperationalError("commit", {}, Exception("database is locked"))

    monkeypatch.setattr(db.session, "commit", always_locked)
    r = client.post(f"/sign/doc/{token}", data={"signer_name": "Concurrent Signer", "agree": "1"})
    assert r.status_code == 409
    assert b"try again" in r.data.lower()

    monkeypatch.undo()
    from app.models import DocumentSignature
    with app.app_context():
        row = db.session.get(DocumentSignature, sid)
        assert row.status == "sent" and not row.signer_name and not row.signature_hash
