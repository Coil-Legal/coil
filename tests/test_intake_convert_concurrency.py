"""A transient SQLite write collision on /intake/<id>/convert must not turn into an unhandled 500.

Two owners (or two tabs) converting a lead, or simply opening two matters at the same instant, can
both read Firm.next_matter_number before either commits and mint the same matter number. SQLite then
refuses whichever commit loses the race: a transient lock error, or (since matters.number is unique)
an IntegrityError once the winner's row has already landed. Reproduced live (Coil QA #50): one
request landed on a new matter, the other came back as a bare "Internal Server Error" page.

Run: .venv/bin/python -m pytest tests/test_intake_convert_concurrency.py -q
"""
import os
import shutil
import subprocess
import sys

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_intake_convert_concurrency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_intake_convert_concurrency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_intake_convert_concurrency")

from tests.helpers import login  # noqa: E402


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
def a_lead(app):
    """One fresh, unconverted intake lead per test."""
    from app.extensions import db
    from app.models import IntakeLead
    with app.app_context():
        lead = IntakeLead(name="Concurrency Test Lead", email="concurrency@example.test",
                          phone="555-0100", matter_type="Other", description="Race condition QA fixture.",
                          status="new", stage="new", source="test")
        db.session.add(lead)
        db.session.commit()
        return lead.id


def post_convert(client, lead_id, matter_name):
    # Unique first/last name per call: the conflict search runs before the matter is created, and a
    # fuzzy match against a name reused from an earlier test in this module would return before
    # db.session.commit() is ever reached, which would make these tests measure the wrong thing.
    slug = matter_name.replace(" ", "")
    return client.post(f"/intake/{lead_id}/convert", data={
        "_csrf": client._csrf, "contact_mode": "new", "first_name": slug, "last_name": "Litigant",
        "email": f"race-{slug}@example.test", "phone": "555-0101", "adverse_party": "",
        "matter_name": matter_name, "practice_area": "Other", "billing_type": "flat", "flat_fee": "0",
        "conflict_ack": "1", "conflict_reason": "QA fixture, no real conflict.",
    })


def test_a_transient_lock_error_is_retried_not_500(app, client, a_lead, monkeypatch):
    """Simulate the exact class of failure Grok hit: the first commit attempt raises the SQLite
    error two concurrent writers can trigger against each other. The route must retry with a fresh
    attempt and land the conversion, not bubble the exception up as a request failure."""
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError("commit", {}, Exception("database is locked"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_convert(client, a_lead, "Race Lock Matter")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated lock error"

    from app.models import Matter, IntakeLead
    with app.app_context():
        rows = Matter.query.filter_by(name="Race Lock Matter").all()
        assert len(rows) == 1, "the retry must not leave a duplicate matter behind"
        lead = db.session.get(IntakeLead, a_lead)
        assert lead.status == "converted" and lead.matter_id == rows[0].id


def test_a_matter_number_collision_is_retried_not_500(app, client, a_lead, monkeypatch):
    """The real-world failure mode: two conversions read the same Firm.next_matter_number before
    either commits, so the loser's commit fails a UNIQUE constraint, not a generic lock. That must
    also be retried (it recomputes a fresh number on the next attempt), not bubbled up as a 500."""
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("commit", {}, Exception("UNIQUE constraint failed: matters.number"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_convert(client, a_lead, "Race Number Matter")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated number collision"

    from app.models import Matter
    with app.app_context():
        rows = Matter.query.filter_by(name="Race Number Matter").all()
        assert len(rows) == 1, "the retry must not leave a duplicate matter behind"


def test_retries_exhausted_is_a_clean_flash_not_a_crash(app, client, a_lead, monkeypatch):
    """When every retry loses the race, the user gets a normal page with a clear message, never an
    unhandled exception, and no partial matter or converted lead is left behind."""
    from app.extensions import db

    def always_locked():
        raise OperationalError("commit", {}, Exception("database is locked"))

    monkeypatch.setattr(db.session, "commit", always_locked)
    r = post_convert(client, a_lead, "Race Exhausted Matter")
    assert r.status_code == 302
    r2 = client.get(r.headers["Location"])
    assert r2.status_code == 200 and b"took this matter number" in r2.data

    monkeypatch.undo()
    from app.models import Matter, IntakeLead
    with app.app_context():
        assert Matter.query.filter_by(name="Race Exhausted Matter").count() == 0
        assert db.session.get(IntakeLead, a_lead).status == "new"


def test_replay_against_an_already_converted_lead_does_not_double_convert(app, client, a_lead):
    """A retried/replayed request against a lead someone else already converted must not create a
    second matter; it should recognize the lead is done and say so."""
    r1 = post_convert(client, a_lead, "Race First Matter")
    assert r1.status_code == 302

    r2 = post_convert(client, a_lead, "Race Second Matter")
    assert r2.status_code == 302
    r2_page = client.get(r2.headers["Location"])
    assert r2_page.status_code == 200

    from app.models import Matter
    from app.extensions import db
    with app.app_context():
        assert Matter.query.filter_by(name="Race First Matter").count() == 1
        assert Matter.query.filter_by(name="Race Second Matter").count() == 0
