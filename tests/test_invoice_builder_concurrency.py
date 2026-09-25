"""A transient SQLite write collision on /invoices/new must not turn into an unhandled 500.

Two owners (or two tabs) building an invoice for the same matter at nearly the same instant can
both read Firm.next_invoice_number before either commits and mint the same number. SQLite then
refuses whichever commit loses the race: a transient lock error, or (since invoices.number is
unique) an IntegrityError once the winner's row has already landed. Reproduced live (Coil QA #51):
one request landed on INV-1042, the other came back as a bare "Internal Server Error" page with no
invoice created.

Run: .venv/bin/python -m pytest tests/test_invoice_builder_concurrency.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_invoice_builder_concurrency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_invoice_builder_concurrency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_invoice_builder_concurrency")

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
def a_matter(app):
    """One fresh matter, no time/expenses, so the builder's only line is the adjustment amount."""
    from app.extensions import db
    from app.models import Contact, Matter
    with app.app_context():
        contact = Contact(first_name="Concurrency", last_name="Client", is_client=True)
        db.session.add(contact)
        db.session.flush()
        matter = Matter(number=f"QA-INV-CONC-{contact.id}", client_id=contact.id, name="Invoice Race Matter",
                        status="open", opened_on=date.today(), billing_type="hourly")
        db.session.add(matter)
        db.session.commit()
        return matter.id


def post_builder(client, matter_id, amount, description):
    return client.post("/invoices/new", data={"_csrf": client._csrf, "matter_id": matter_id,
                                               "issued_on": TODAY, "adjustment_amount": amount,
                                               "adjustment_description": description})


def test_a_transient_lock_error_is_retried_not_500(app, client, a_matter, monkeypatch):
    """Simulate the exact class of failure Grok hit: the first commit attempt raises the SQLite
    error two concurrent writers can trigger against each other. The route must retry with a fresh
    attempt and land the invoice, not bubble the exception up as a request failure."""
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError("commit", {}, Exception("database is locked"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_builder(client, a_matter, "1.00", "QA Simultaneous Lock")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated lock error"

    from app.models import Invoice
    with app.app_context():
        rows = Invoice.query.filter_by(matter_id=a_matter).all()
        assert len(rows) == 1, "the retry must not leave a duplicate invoice behind"
        assert rows[0].total_cents == 100


def test_a_number_collision_is_retried_not_500(app, client, a_matter, monkeypatch):
    """The real-world failure mode: two builder submissions read the same Firm.next_invoice_number
    before either commits, so the loser's commit fails a UNIQUE constraint, not a generic lock. That
    must also be retried (it recomputes a fresh number, and fresh lines, on the next attempt), not
    bubbled up as a 500."""
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("commit", {}, Exception("UNIQUE constraint failed: invoices.number"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_builder(client, a_matter, "1.00", "QA Simultaneous Number")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated number collision"

    from app.models import Invoice
    with app.app_context():
        rows = Invoice.query.filter_by(matter_id=a_matter).all()
        assert len(rows) == 1, "the retry must not leave a duplicate invoice behind"


def test_retries_exhausted_is_a_clean_flash_not_a_crash(app, client, a_matter, monkeypatch):
    """When every retry loses the race, the user gets a normal page with a clear message, never an
    unhandled exception, and no partial invoice is left behind."""
    from app.extensions import db

    def always_locked():
        raise OperationalError("commit", {}, Exception("database is locked"))

    monkeypatch.setattr(db.session, "commit", always_locked)
    r = post_builder(client, a_matter, "1.00", "QA Simultaneous Exhausted")
    assert r.status_code == 400
    assert b"took this invoice number" in r.data

    monkeypatch.undo()
    from app.models import Invoice
    with app.app_context():
        assert Invoice.query.filter_by(matter_id=a_matter).count() == 0
