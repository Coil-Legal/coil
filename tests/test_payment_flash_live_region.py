"""Issue #144 (QA Bot 2): a manual-payment refusal ("Enter a positive amount.", the
over-balance message) renders as a plain <div class="flash error">, with no role="alert"
or aria-live anywhere on the page, so a screen reader gives no cue that the payment was
refused. The shared flash partial in base.html is the fix point, not any one form.

Own SQLite file via tmp_path_factory, same pattern as test_module_c.py.
Run: .venv/bin/python -m pytest tests/test_payment_flash_live_region.py -q
"""
import os
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from tests.helpers import login  # noqa: E402


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("flash144")
    uri = f"sqlite:///{tmp / 'test.db'}"
    env = dict(os.environ, DATABASE_URL=uri, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="", SMTP_HOST="")
    subprocess.run([sys.executable, "seed.py"], cwd=ROOT, env=env, check=True)
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": uri, "TESTING": True, "STRIPE_SECRET_KEY": "",
                       "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": "", "UPLOAD_DIR": str(tmp / "uploads")})


@pytest.fixture(scope="module")
def client(app):
    c = app.test_client()
    login(c)
    return c


def _invoice(app, number):
    from app.extensions import db
    from app.models import Contact, Matter, Invoice, InvoiceLine
    with app.app_context():
        contact = Contact.query.filter_by(last_name="Alvarez").first()
        matter = Matter.query.filter_by(number="M-1002").first()
        inv = Invoice(number=number, matter_id=matter.id, client_id=contact.id, kind="hourly",
                      status="sent", issued_on=date.today(), due_on=date.today(),
                      subtotal_cents=10000, total_cents=10000)
        inv.lines.append(InvoiceLine(kind="flat", description="Services", quantity=1.0, unit_cents=10000,
                                     amount_cents=10000))
        db.session.add(inv)
        db.session.commit()
        return inv.id


def _csrf(client):
    client.get("/payments")
    with client.session_transaction() as s:
        return s["_csrf"]


def test_manual_payment_error_flash_is_a_live_region(app, client):
    inv_id = _invoice(app, "INV-TEST-144A")
    tok = _csrf(client)
    r = client.post("/payments/record", data={"_csrf": tok, "invoice_id": str(inv_id), "amount": "0"},
                    follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Enter a positive amount." in html
    assert 'class="flash error" role="alert"' in html


def test_manual_payment_success_flash_is_a_status_region(app, client):
    inv_id = _invoice(app, "INV-TEST-144B")
    tok = _csrf(client)
    r = client.post("/payments/record",
                    data={"_csrf": tok, "invoice_id": str(inv_id), "amount": "50.00", "method": "check"},
                    follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Recorded $50.00 check payment on" in html
    assert 'class="flash ok" role="status"' in html
