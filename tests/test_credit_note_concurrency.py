"""Two simultaneous credit requests against the same invoice must not turn into an unhandled 500.

Same SQLite write race already retried for invoices (#51/#56), matter numbers (#50) and
signatures (#48): two callers can both read a Firm counter (here, next_credit_note_number) and
the invoice's balance_cents before either commits. The loser's commit then either hits a
transient lock, or a UNIQUE-constraint violation on credit_notes.number once the winner's row
has landed -- and by then the winner's credit has already reduced the balance the loser checked
against. Reproduced live (Coil QA #58): two $0.50 credits against a $0.75 balance, one landed as
CN-1015, the other came back a bare "Internal Server Error" instead of the expected "would take
it below zero" flash.

Run: .venv/bin/python -m pytest tests/test_credit_note_concurrency.py -q
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
DB_PATH = os.path.join(ROOT, "data", "test_credit_note_concurrency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_credit_note_concurrency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_credit_note_concurrency")

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


_seq = iter(range(1, 9999))


def _sent_invoice(app, total_cents):
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number=f"CNC-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today(), tax_cents=0)
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Services", amount_cents=total_cents, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
        return inv.id


@pytest.fixture
def sent_invoice(app):
    """A sent $10.00 invoice with nothing paid on it."""
    return _sent_invoice(app, 1000)


def post_credit(c, inv_id, amount):
    return c.post(f"/invoices/{inv_id}/credit", data={"_csrf": c._csrf, "amount": amount, "reason": "other"})


def test_a_transient_lock_error_is_retried_not_500(app, client, sent_invoice, monkeypatch):
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise OperationalError("commit", {}, Exception("database is locked"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_credit(client, sent_invoice, "1.00")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated lock error"

    from app.models import CreditNote
    with app.app_context():
        rows = CreditNote.query.filter_by(invoice_id=sent_invoice).all()
        assert len(rows) == 1, "the retry must not leave a duplicate credit note behind"


def test_a_number_collision_is_retried_not_500(app, client, sent_invoice, monkeypatch):
    """The real-world failure mode: two credits read the same Firm.next_credit_note_number before
    either commits, so the loser's commit fails a UNIQUE constraint, not a generic lock."""
    from app.extensions import db
    real_commit = db.session.commit
    calls = {"n": 0}

    def flaky_commit():
        calls["n"] += 1
        if calls["n"] == 1:
            raise IntegrityError("commit", {}, Exception("UNIQUE constraint failed: credit_notes.number"))
        return real_commit()

    monkeypatch.setattr(db.session, "commit", flaky_commit)
    r = post_credit(client, sent_invoice, "1.00")
    assert r.status_code == 302, r.data[:300]
    assert calls["n"] == 2, "expected exactly one retry after the simulated number collision"

    from app.models import CreditNote
    with app.app_context():
        rows = CreditNote.query.filter_by(invoice_id=sent_invoice).all()
        assert len(rows) == 1, "the retry must not leave a duplicate credit note behind"


def test_retries_exhausted_is_a_clean_flash_not_a_crash(app, client, sent_invoice, monkeypatch):
    from app.extensions import db

    def always_locked():
        raise OperationalError("commit", {}, Exception("database is locked"))

    monkeypatch.setattr(db.session, "commit", always_locked)
    r = client.post(f"/invoices/{sent_invoice}/credit",
                    data={"_csrf": client._csrf, "amount": "1.00", "reason": "other"}, follow_redirects=True)
    assert r.status_code == 200
    assert b"took this credit note number" in r.data
    monkeypatch.undo()

    from app.models import CreditNote
    with app.app_context():
        assert CreditNote.query.filter_by(invoice_id=sent_invoice).count() == 0


def test_a_number_collision_after_the_balance_already_changed_is_a_flash_not_a_500(app, client, monkeypatch):
    """Coil QA #58's actual failure mode: the second of two racing credits doesn't just lose the
    credit-note-number race, it loses it after the winner's own credit (or a payment, same effect
    on balance_cents) has already landed in a separate transaction. A retry that mints a fresh
    number but never rereads the balance would still overshoot it; this simulates that landed
    change with a direct write on a second connection, between this request's first flush attempt
    and its retry, and checks the retry's own db.session.refresh(inv) picks it up."""
    import sqlite3
    from app.extensions import db

    inv_id = _sent_invoice(app, 1000)  # $10.00 balance, nothing paid
    real_flush = db.session.flush
    calls = {"n": 0}

    def flaky_flush():
        calls["n"] += 1
        if calls["n"] == 1:
            conn = sqlite3.connect(DB_PATH)
            conn.execute("UPDATE invoices SET paid_cents = 700 WHERE id = ?", (inv_id,))
            conn.commit()
            conn.close()
            raise IntegrityError("flush", {}, Exception("UNIQUE constraint failed: credit_notes.number"))
        return real_flush()

    monkeypatch.setattr(db.session, "flush", flaky_flush)
    r = post_credit(client, inv_id, "6.00")
    assert r.status_code == 302, r.data[:300]
    monkeypatch.undo()

    from app.models import CreditNote, Invoice
    with app.app_context():
        assert CreditNote.query.filter_by(invoice_id=inv_id).count() == 0, (
            "the $6.00 credit must not have been issued against a $3.00 balance")
        assert db.session.get(Invoice, inv_id).balance_cents == 300
