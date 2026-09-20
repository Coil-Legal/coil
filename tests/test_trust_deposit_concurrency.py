"""A transient SQLite write collision on /trust/new must not turn into an unhandled 500.

Two owners (or two tabs) posting a trust deposit for the same client at nearly the same
instant can make SQLite refuse whichever commit loses the race, even in WAL mode: plain
contention (SQLITE_BUSY) or a snapshot a concurrent commit made stale mid-transaction
(SQLITE_BUSY_SNAPSHOT). Reproduced live (Coil QA #43): one request landed, the other came
back as a bare "Internal Server Error" page with no flash and no ledger row. The importer
already retries this class of error a few times before giving up; the deposit form did not.

Run: .venv/bin/python -m pytest tests/test_trust_deposit_concurrency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest
from sqlalchemy.exc import OperationalError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_trust_deposit_concurrency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_trust_deposit_concurrency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_trust_deposit_concurrency")

from tests.helpers import login  # noqa: E402

TODAY = date.today().isoformat()


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(PDF_DIR, ignore_errors=True)
    env = dict(os.environ, DATABASE_URL=DB_URI, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="", SMTP_HOST="")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
                       "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": ""})


@pytest.fixture(scope="module")
def client(app):
    c = app.test_client()
    c._csrf = login(c)
    return c


@pytest.fixture
def a_client(app):
    """One client, no matter, fresh for each test."""
    from app.extensions import db
    from app.models import Contact
    with app.app_context():
        c = Contact(first_name="Concurrency", last_name="Client", is_client=True)
        db.session.add(c)
        db.session.commit()
        return c.id


def post_deposit(client, cid, amount, reference):
    return client.post("/trust/new", data={"_csrf": client._csrf, "type": "deposit", "client_id": cid,
                                           "matter_id": "", "date": TODAY, "amount": amount,
                                           "description": "Retainer", "payee": "", "reference": reference})


def test_a_transient_lock_error_is_retried_not_500(app, client, a_client, monkeypatch):
    """Simulate the exact failure Grok hit: the first commit attempt raises the SQLite error
    two concurrent writers can trigger against each other. The route must retry with a fresh
    attempt and land the deposit, not bubble the exception up as a request failure."""
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError("commit", {}, Exception("database is locked"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_deposit(client, a_client, "10.00", "SZ-CONC-X-1")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated lock error"

    from app.models import TrustTransaction
    with app.app_context():
        rows = TrustTransaction.query.filter_by(client_id=a_client, reference="SZ-CONC-X-1").all()
        assert len(rows) == 1, "the retry must not leave a duplicate row behind"
        assert rows[0].amount_cents == 1000


def test_retries_exhausted_is_a_clean_flash_not_a_crash(app, client, a_client, monkeypatch):
    """When every retry loses the race, the user gets a normal page with a clear message,
    never an unhandled exception, and no partial row is left in the ledger."""
    from app.extensions import db

    def always_locked():
        raise OperationalError("commit", {}, Exception("database is locked"))

    monkeypatch.setattr(db.session, "commit", always_locked)
    r = post_deposit(client, a_client, "10.00", "SZ-CONC-Y-1")
    assert r.status_code == 200
    assert b"being saved at the same moment" in r.data

    monkeypatch.undo()
    from app.models import TrustTransaction
    with app.app_context():
        assert TrustTransaction.query.filter_by(client_id=a_client, reference="SZ-CONC-Y-1").count() == 0
