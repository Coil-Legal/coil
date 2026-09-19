"""Moving trust money between two matters of the same client.

Coil refuses to let one matter's money pay another matter's bills, which is right. But
with no transfer the only way around that refusal was a disbursement from the first
matter and a deposit to the second: two entries that hit the book balance, never clear
at the bank, and leave every later reconciliation carrying two phantom items. The
client's ledger then shows a payment out they never received. The missing feature did
not prevent the move, it only made the record of it worse.

Two rules are enforced rather than advised. The money stays inside one client, because
moving between clients is the case no consent can cure. And the transfer records who
authorised it, because an unauthorised move between matters is a setoff against the
client's money rather than a bookkeeping correction.

Run: .venv/bin/python -m pytest tests/test_trust_transfer.py -q
"""
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_trust_transfer.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_trust_transfer")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_trust_transfer")

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


def post(c, path, data):
    return c.post(path, data=dict(data, _csrf=c._csrf), follow_redirects=True)


@pytest.fixture
def two_matters(app):
    """One client, two matters, $5,000 earmarked to the first. Fresh for each test."""
    from app.extensions import db
    from app.models import Contact, Matter, TrustTransaction
    with app.app_context():
        c = Contact(first_name="Trustcheck", last_name="Client", is_client=True)
        db.session.add(c)
        db.session.flush()
        a = Matter(client_id=c.id, number=f"T-{c.id}01", name="First matter", status="open")
        b = Matter(client_id=c.id, number=f"T-{c.id}02", name="Second matter", status="open")
        db.session.add_all([a, b])
        db.session.flush()
        db.session.add(TrustTransaction(client_id=c.id, matter_id=a.id, date=date.today(), type="deposit",
                                        amount_cents=500000, description="Retainer", cleared=True))
        db.session.commit()
        return c.id, a.id, b.id


def _balances(app, cid):
    from app.blueprints.trust import allocation
    from app.models import Contact
    from app.extensions import db
    with app.app_context():
        c = db.session.get(Contact, cid)
        total, per, allocated, unallocated = allocation(c)
        return total, per


def test_the_money_moves_and_the_client_total_does_not(app, client, two_matters):
    cid, a, b = two_matters
    before_total, before_per = _balances(app, cid)
    r = post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                         "date": TODAY, "amount": "1500.00",
                                         "authorized_by": "Client by phone, this morning",
                                         "description": "Applied to the new matter"})
    assert r.status_code == 200
    after_total, after_per = _balances(app, cid)
    assert after_total == before_total, "a transfer is not a deposit or a withdrawal"
    assert after_per[a] == before_per[a] - 150000
    assert after_per[b] == before_per.get(b, 0) + 150000


def test_it_is_two_linked_rows_that_net_to_zero(app, client, two_matters):
    cid, a, b = two_matters
    post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                     "date": TODAY, "amount": "250.00", "authorized_by": "Engagement letter s 4"})
    from app.models import TrustTransaction
    with app.app_context():
        legs = TrustTransaction.query.filter(TrustTransaction.client_id == cid,
                                             TrustTransaction.transfer_group != "").all()
        assert len(legs) == 2
        assert legs[0].transfer_group == legs[1].transfer_group, "the pair must be findable from either side"
        assert sum(x.amount_cents for x in legs) == 0, "no money was created or destroyed"
        assert {x.type for x in legs} == {"transfer_out", "transfer_in"}
        assert all(x.authorized_by == "Engagement letter s 4" for x in legs)


def test_it_never_touches_the_bank_reconciliation(app, client, two_matters):
    """No money leaves the account, so neither leg may sit on the outstanding list."""
    cid, a, b = two_matters
    from app.blueprints.trust import book_total
    from app.models import TrustTransaction
    with app.app_context():
        before = book_total()
    post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                     "date": TODAY, "amount": "400.00", "authorized_by": "Client email"})
    with app.app_context():
        assert book_total() == before, "the bank balance cannot move when the bank was never involved"
        legs = TrustTransaction.query.filter(TrustTransaction.transfer_group != "",
                                             TrustTransaction.client_id == cid).all()
        assert all(x.cleared for x in legs), "an uncleared transfer would sit outstanding forever"


def test_it_refuses_to_cross_clients(app, client, two_matters):
    """The case no authorisation can cure. One client's money never funds another's matter."""
    cid, a, _ = two_matters
    from app.extensions import db
    from app.models import Contact, Matter
    with app.app_context():
        other = Contact(first_name="Someone", last_name="Else", is_client=True)
        db.session.add(other)
        db.session.flush()
        om = Matter(client_id=other.id, number=f"T-{other.id}99", name="Their matter", status="open")
        db.session.add(om)
        db.session.commit()
        om_id = om.id
    before_total, _ = _balances(app, cid)
    r = post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": om_id,
                                         "date": TODAY, "amount": "100.00", "authorized_by": "Both clients agree"})
    assert "between clients" in r.data.decode()
    assert _balances(app, cid)[0] == before_total, "nothing moved"


def test_it_will_not_overdraw_the_source_matter(app, client, two_matters):
    cid, a, b = two_matters
    r = post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                         "date": TODAY, "amount": "9000.00", "authorized_by": "Client"})
    assert "would overdraw" in r.data.decode()
    _, per = _balances(app, cid)
    assert per[a] == 500000 and per.get(b, 0) == 0


def test_it_requires_a_named_authorisation(app, client, two_matters):
    """An unauthorised move between matters is a setoff against the client's money."""
    cid, a, b = two_matters
    r = post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                         "date": TODAY, "amount": "100.00", "authorized_by": ""})
    assert "who authorised" in r.data.decode()
    _, per = _balances(app, cid)
    assert per.get(b, 0) == 0, "nothing moved without it"


def test_it_refuses_the_same_matter_twice(app, client, two_matters):
    cid, a, _ = two_matters
    r = post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": a,
                                         "date": TODAY, "amount": "100.00", "authorized_by": "Client"})
    assert "two different matters" in r.data.decode()


def test_the_audit_log_names_both_matters_and_the_authoriser(app, client, two_matters):
    cid, a, b = two_matters
    post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                     "date": TODAY, "amount": "75.00", "authorized_by": "Client, by email 19 Sep"})
    from app.models import AuditLog
    with app.app_context():
        row = AuditLog.query.filter_by(action="trust_transfer").order_by(AuditLog.id.desc()).first()
        assert row is not None
        assert "Client, by email 19 Sep" in row.detail
        assert "->" in row.detail, "an auditor should see which way the money went"


def test_both_matters_show_their_side_on_the_ledger(app, client, two_matters):
    cid, a, b = two_matters
    post(client, "/trust/transfer", {"client_id": cid, "from_matter_id": a, "to_matter_id": b,
                                     "date": TODAY, "amount": "300.00", "authorized_by": "Client"})
    page = client.get(f"/trust/ledger/{cid}").data.decode()
    assert "Transferred to another matter" in page
    assert "Transferred from another matter" in page


def test_the_transfer_types_are_not_on_the_ordinary_form(client):
    """They only ever exist as a pair, so a one-sided version must not be reachable."""
    page = client.get("/trust/new").data.decode()
    assert "transfer_out" not in page and "transfer_in" not in page
