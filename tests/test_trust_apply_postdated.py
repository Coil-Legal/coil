"""Regression tests for issue #143 (QA2): a client's trust money dated after today showed on
the invoice's "Apply from trust" card as spendable, then /trust/apply refused it and blamed
"earmarked to a different matter" even though nothing was earmarked elsewhere, because the card
computed available_for_matter() with no as_of while apply() correctly capped it at today.

Own SQLite file (data/test_trust_apply_postdated.db). Never touches data/practice.db.
Run: .venv/bin/python -m pytest tests/test_trust_apply_postdated.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_trust_apply_postdated.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_trust_apply_postdated")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_trust_apply_postdated")

from tests.helpers import login  # noqa: E402

FUTURE = date.today() + timedelta(days=30)


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
    login(c)
    return c


def csrf(client):
    client.get("/trust/new")
    with client.session_transaction() as s:
        return s["_csrf"]


def _models():
    from app.extensions import db
    from app import models
    return db, models


def _make_client_with_matter(app, tag):
    db, M = _models()
    with app.app_context():
        u = M.User.query.first()
        c = M.Contact(first_name="Dated", last_name=f"Client{tag}", email=f"dated{tag}@example.test",
                      is_client=True)
        db.session.add(c)
        db.session.flush()
        m = M.Matter(number=f"M-PD{tag}", client_id=c.id, name=f"TEST post-dated matter {tag}",
                     billing_type="hourly", responsible_user_id=u.id, status="open")
        db.session.add(m)
        db.session.commit()
        return c.id, m.id


def _sent_invoice(app, client_id, matter_id, cents, number):
    db, M = _models()
    with app.app_context():
        inv = M.Invoice(number=number, matter_id=matter_id, client_id=client_id, kind="hourly", status="sent",
                        issued_on=date.today(), due_on=date.today(), subtotal_cents=cents, total_cents=cents)
        inv.lines.append(M.InvoiceLine(kind="flat", description="Services", quantity=1.0, unit_cents=cents,
                                       amount_cents=cents))
        db.session.add(inv)
        db.session.commit()
        return inv.id


def _deposit(app, client_id, matter_id, cents, when, desc="Deposit"):
    db, M = _models()
    with app.app_context():
        db.session.add(M.TrustTransaction(client_id=client_id, matter_id=matter_id, date=when,
                                          type="deposit", amount_cents=cents, description=desc,
                                          created_by_id=M.User.query.first().id))
        db.session.commit()


def test_detail_card_and_apply_agree_when_all_money_is_postdated(app, client):
    """The exact #143 repro: money dated after today, nothing earmarked elsewhere."""
    db, M = _models()
    cid, mid = _make_client_with_matter(app, "1")
    _deposit(app, cid, mid, 30000, FUTURE, "Earmarked to the matter, dated later")
    _deposit(app, cid, None, 500000, FUTURE, "Unallocated, dated later")
    inv_id = _sent_invoice(app, cid, mid, 20000, "INV-PD-1")

    # The card must show what is available TODAY, not the post-dated total.
    r = client.get(f"/invoices/{inv_id}")
    assert r.status_code == 200
    body = r.data.decode()
    assert "$0.00 of Dated Client1" in body, body[:2000]
    assert "$5,300.00 more is dated after today" in body, body[:2000]
    # with nothing available today, apply() must not be offered as if it would work
    assert '<form method="post" action="/trust/apply">' not in body

    tok = csrf(client)
    r = client.post("/trust/apply", data={"_csrf": tok, "invoice_id": inv_id, "amount": "200.00"},
                    follow_redirects=True)
    assert r.status_code == 200
    refusal = r.data.decode()
    assert "Only $0.00 can be applied" in refusal, refusal[:2000]
    # the real cause is named...
    assert "$5,300.00 of this client" in refusal and "trust money is dated after today" in refusal, refusal[:2000]
    # ...and the misleading "earmarked to a different matter" story is not told, since nothing is.
    assert "earmarked to a different matter and cannot pay this one" not in refusal

    with app.app_context():
        inv = db.session.get(M.Invoice, inv_id)
        assert inv.paid_cents == 0
        assert inv.status == "sent"
        assert M.TrustTransaction.query.filter_by(invoice_id=inv_id).count() == 0


def test_refusal_still_blames_earmarking_when_nothing_is_postdated(app, client):
    """Unrelated-matter earmarking with no future-dated money keeps the original wording."""
    db, M = _models()
    cid, mid = _make_client_with_matter(app, "2")
    other = M.Matter(number="M-PD2B", client_id=cid, name="TEST other matter 2", billing_type="hourly",
                     responsible_user_id=None, status="open")
    with app.app_context():
        other.responsible_user_id = M.User.query.first().id
        db.session.add(other)
        db.session.commit()
        other_id = other.id
    _deposit(app, cid, other_id, 90000, date.today(), "Earmarked to the other matter, today")
    inv_id = _sent_invoice(app, cid, mid, 50000, "INV-PD-2")
    tok = csrf(client)

    r = client.post("/trust/apply", data={"_csrf": tok, "invoice_id": inv_id, "amount": "500.00"},
                    follow_redirects=True)
    body = r.data.decode()
    assert "Only $0.00 can be applied" in body, body[:2000]
    assert "earmarked to a different matter and cannot pay this one" in body
    assert "dated after today" not in body


def test_refusal_names_both_when_shortfall_is_mixed(app, client):
    """Some of the shortfall is post-dated, some is genuinely earmarked elsewhere."""
    db, M = _models()
    cid, mid = _make_client_with_matter(app, "3")
    other = M.Matter(number="M-PD3B", client_id=cid, name="TEST other matter 3", billing_type="hourly",
                     responsible_user_id=None, status="open")
    with app.app_context():
        other.responsible_user_id = M.User.query.first().id
        db.session.add(other)
        db.session.commit()
        other_id = other.id
    _deposit(app, cid, other_id, 90000, date.today(), "Earmarked to the other matter, today")
    _deposit(app, cid, None, 20000, FUTURE, "Unallocated, dated later")
    inv_id = _sent_invoice(app, cid, mid, 50000, "INV-PD-3")
    tok = csrf(client)

    r = client.post("/trust/apply", data={"_csrf": tok, "invoice_id": inv_id, "amount": "500.00"},
                    follow_redirects=True)
    body = r.data.decode()
    assert "Only $0.00 can be applied" in body, body[:2000]
    assert "$200.00 more is dated after today" in body, body[:2000]
    assert "the rest is earmarked to a different matter" in body


def test_apply_unaffected_when_money_is_available_today(app, client):
    """No regression: money dated today or earlier applies exactly as before."""
    db, M = _models()
    cid, mid = _make_client_with_matter(app, "4")
    _deposit(app, cid, mid, 80000, date.today(), "Retainer, today")
    inv_id = _sent_invoice(app, cid, mid, 50000, "INV-PD-4")

    r = client.get(f"/invoices/{inv_id}")
    assert r.status_code == 200
    body = r.data.decode()
    assert "$800.00 of Dated Client4" in body
    assert "dated after today" not in body

    tok = csrf(client)
    r = client.post("/trust/apply", data={"_csrf": tok, "invoice_id": inv_id, "amount": "500.00"})
    assert r.status_code == 302, r.data[:300]
    with app.app_context():
        inv = db.session.get(M.Invoice, inv_id)
        assert inv.paid_cents == 50000
        assert inv.status == "paid"
