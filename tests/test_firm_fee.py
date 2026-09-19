"""Paying the firm out of a client's trust account.

This is the transaction that ends careers, and until now Coil could not tell it apart
from a payment to a court reporter: the type was "disbursement" and the payee was free
text. An examiner reading the ledger could not find fee withdrawals at all.

So there is a type for it, and when the amount is larger than the fees Coil can see on
the matter it asks how the fee was earned and writes the answer onto the entry.

It asks rather than refuses, deliberately. A flat fee earned at a milestone, a true
retainer, and a contingency share of a recovery are all properly earned with no invoice
behind them, and a fee agreement is allowed to define when a fee is earned. An attorney
blocked from a legitimate withdrawal at seven in the evening records it as a
disbursement to "office" instead, and then the signal is gone entirely.

The hard refusals stay hard: the trust balance and the matter balance are ledger
integrity, which is a different thing from whether a fee is reasonable.

Run: .venv/bin/python -m pytest tests/test_firm_fee.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_firm_fee.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_firm_fee")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_firm_fee")

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
def funded_matter(app):
    """A client with $5,000 in trust on a matter, and nothing billed or recorded on it."""
    from app.extensions import db
    from app.models import Contact, Matter, TrustTransaction
    with app.app_context():
        n = next(_seq)
        c = Contact(first_name="Feecheck", last_name=f"Client{n}", is_client=True)
        db.session.add(c)
        db.session.flush()
        m = Matter(client_id=c.id, number=f"FF-{n:04d}", name="Fee matter", status="open")
        db.session.add(m)
        db.session.flush()
        db.session.add(TrustTransaction(client_id=c.id, matter_id=m.id, date=date.today(), type="deposit",
                                        amount_cents=500000, description="Retainer", cleared=True))
        db.session.commit()
        return c.id, m.id


def _matter_trust(app, mid):
    from app.blueprints.trust import matter_balances
    with app.app_context():
        return matter_balances().get(mid, 0)


# ------------------------------------------------------------------ the type itself
def test_paying_the_firm_is_its_own_kind_of_transaction(client):
    """An examiner scanning the ledger has to be able to find fee withdrawals."""
    page = client.get("/trust/new").data.decode()
    assert "firm_fee" in page and "Fee paid to the firm" in page


def test_it_asks_how_the_fee_was_earned_before_it_will_go_through(app, client, funded_matter):
    cid, mid = funded_matter
    before = _matter_trust(app, mid)
    r = post(client, {"type": "firm_fee", "client_id": cid, "matter_id": mid, "date": TODAY,
                      "amount": "1000.00", "description": "Fees"})
    body = r.data.decode()
    assert "How is this fee earned?" in body, "the question has to be asked on screen"
    assert "fees billed or recorded" in body
    assert _matter_trust(app, mid) == before, "and nothing moves until it is answered"


def test_the_answer_goes_onto_the_ledger_entry(app, client, funded_matter):
    """A reason captured and then thrown away is worse than no reason: it looks like diligence."""
    cid, mid = funded_matter
    r = post(client, {"type": "firm_fee", "client_id": cid, "matter_id": mid, "date": TODAY,
                      "amount": "1000.00", "description": "Fees",
                      "fee_reason": "Flat fee earned on filing, engagement letter 3 March"})
    assert r.status_code == 200
    from app.models import TrustTransaction
    with app.app_context():
        t = TrustTransaction.query.filter_by(matter_id=mid, type="firm_fee").first()
        assert t is not None
        assert t.amount_cents == -100000
        assert "Flat fee earned on filing" in t.description
        assert t.payee, "a fee withdrawal must show it was payable to the firm"


def test_the_audit_log_carries_the_reason_too(app, client, funded_matter):
    cid, mid = funded_matter
    post(client, {"type": "firm_fee", "client_id": cid, "matter_id": mid, "date": TODAY,
                  "amount": "2000.00", "description": "", "fee_reason": "Contingency share of the recovery"})
    from app.models import AuditLog
    with app.app_context():
        row = AuditLog.query.filter_by(action="trust_firm_fee").order_by(AuditLog.id.desc()).first()
        assert row is not None and "Contingency share of the recovery" in row.detail


def test_a_fee_within_what_is_billed_needs_no_explanation(app, client, funded_matter):
    """Asking on every withdrawal is how a warning becomes wallpaper."""
    cid, mid = funded_matter
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = db.session.get(Matter, mid)
        inv = Invoice(number=f"FFI-{next(_seq):04d}", matter_id=m.id, client_id=m.client_id,
                      status="sent", issued_on=date.today())
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="Work", amount_cents=300000, kind="fee"))
        db.session.flush()
        inv.recalc()
        db.session.commit()
    before = _matter_trust(app, mid)
    r = post(client, {"type": "firm_fee", "client_id": cid, "matter_id": mid, "date": TODAY,
                      "amount": "1500.00", "description": "Payment of invoice"})
    assert "How is this fee earned?" not in r.data.decode()
    assert _matter_trust(app, mid) == before - 150000, "it went through without a prompt"


# ------------------------------------------------------------------ what stays hard
def test_it_still_will_not_overdraw_the_matter(app, client, funded_matter):
    """Ledger integrity is not a matter of opinion, so no reason unlocks it."""
    cid, mid = funded_matter
    before = _matter_trust(app, mid)
    r = post(client, {"type": "firm_fee", "client_id": cid, "matter_id": mid, "date": TODAY,
                      "amount": "9000.00", "description": "Fees",
                      "fee_reason": "Earned in full, I promise"})
    assert "would overdraw" in r.data.decode()
    assert _matter_trust(app, mid) == before


def test_an_ordinary_disbursement_is_never_questioned(app, client, funded_matter):
    """Paying a court reporter is not a fee withdrawal and must not be treated as one."""
    cid, mid = funded_matter
    r = post(client, {"type": "disbursement", "client_id": cid, "matter_id": mid, "date": TODAY,
                      "amount": "1200.00", "description": "Court reporter", "payee": "Acme Reporting"})
    assert "How is this fee earned?" not in r.data.decode()
    assert _matter_trust(app, mid) == 500000 - 120000
