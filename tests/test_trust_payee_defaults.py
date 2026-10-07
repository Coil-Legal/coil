"""Issue #154: a blank Payee on /trust/new defaulted to the firm's own name for every
transaction type. On a refund to client, that reads as the firm paying itself, exactly the
signal firm_fee was built to flag; a bank fee or interest entry isn't paid to or from the
firm at all. The default now depends on the type: refund defaults to the client's own
display name, bank_fee/interest default to the trust bank name, and firm_fee (the one type
that really is paid to the firm) keeps the firm name.

Run: .venv/bin/python -m pytest tests/test_trust_payee_defaults.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_trust_payee_defaults.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_trust_payee_defaults")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_trust_payee_defaults")

from tests.helpers import login  # noqa: E402

TODAY = date.today().isoformat()
_seq = iter(range(1, 9999))


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


def post(c, data):
    return c.post("/trust/new", data=dict(data, _csrf=c._csrf), follow_redirects=True)


@pytest.fixture
def funded_client(app):
    """A client with $5,000 in trust, unallocated (no matter)."""
    from app.extensions import db
    from app.models import Contact, TrustTransaction
    with app.app_context():
        n = next(_seq)
        c = Contact(first_name="Payeecheck", last_name=f"Client{n}", is_client=True)
        db.session.add(c)
        db.session.flush()
        db.session.add(TrustTransaction(client_id=c.id, date=date.today(), type="deposit",
                                        amount_cents=500000, description="Retainer", cleared=True))
        db.session.commit()
        return c.id, c.display_name


def _last_txn(app, ttype):
    from app.models import TrustTransaction
    with app.app_context():
        return TrustTransaction.query.filter_by(type=ttype).order_by(TrustTransaction.id.desc()).first()


def test_refund_with_blank_payee_defaults_to_the_client_not_the_firm(app, client, funded_client):
    cid, name = funded_client
    r = post(client, {"type": "refund", "client_id": cid, "date": TODAY, "amount": "50.00",
                      "description": "Unused retainer", "payee": ""})
    assert r.status_code == 200
    t = _last_txn(app, "refund")
    assert t.client_id == cid
    assert t.payee == name, f"a refund's blank payee should be the client, got {t.payee!r}"


def test_bank_fee_with_blank_payee_defaults_to_the_trust_bank(app, client, funded_client):
    cid, name = funded_client
    from app.models import Firm
    with app.app_context():
        bank = Firm.get().trust_bank_name
        firm_name = Firm.get().name
    r = post(client, {"type": "bank_fee", "client_id": cid, "date": TODAY, "amount": "10.00",
                      "description": "Monthly fee", "payee": ""})
    assert r.status_code == 200
    t = _last_txn(app, "bank_fee")
    assert t.payee == bank, f"a bank fee's blank payee should be the trust bank, got {t.payee!r}"
    assert t.payee != firm_name


def test_interest_with_blank_payee_defaults_to_the_trust_bank(app, client, funded_client):
    cid, name = funded_client
    from app.models import Firm
    with app.app_context():
        bank = Firm.get().trust_bank_name
    r = post(client, {"type": "interest", "client_id": cid, "date": TODAY, "amount": "1.00",
                      "description": "Interest", "payee": ""})
    assert r.status_code == 200
    t = _last_txn(app, "interest")
    assert t.payee == bank


def test_firm_fee_with_blank_payee_still_defaults_to_the_firm(app, client, funded_client):
    cid, name = funded_client
    from app.models import Firm
    with app.app_context():
        firm_name = Firm.get().name
    r = post(client, {"type": "firm_fee", "client_id": cid, "date": TODAY, "amount": "25.00",
                      "description": "Fees", "fee_reason": "Flat fee earned on filing", "payee": ""})
    assert r.status_code == 200
    t = _last_txn(app, "firm_fee")
    assert t.payee == firm_name


def test_payee_still_overrides_the_default_when_given(app, client, funded_client):
    cid, name = funded_client
    r = post(client, {"type": "refund", "client_id": cid, "date": TODAY, "amount": "5.00",
                      "description": "Partial refund", "payee": "Someone Else"})
    assert r.status_code == 200
    t = _last_txn(app, "refund")
    assert t.payee == "Someone Else"
