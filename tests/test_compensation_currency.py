"""QA issue #68: same defect class as #59-#64/#66/#67, at /reports/compensation. A EUR payment's
fee share was added straight into the dollar total (a 0.50 EUR fee showed as part of a $4,329.01
figure with no euro sign anywhere on the page), and the per-person working/originating/referral
totals made the same mistake when one person is credited from matters in more than one currency.

Run: .venv/bin/python -m pytest tests/test_compensation_currency.py -q
"""
import csv
import io
import os
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_compensation_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_compensation_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_compensation_currency")

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


@pytest.fixture(scope="module")
def usd_and_eur_fee_payments(app):
    """One attorney originates (and does 100% of the work on) a USD matter with a $25.01 fee payment
    and a EUR matter with a 0.50 EUR fee payment, both received today. One originator, two currencies,
    so the attorney's own working/originating totals mix currencies too, not just the grand total."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, Payment, User
    with app.app_context():
        u = User.query.first()
        base = Matter.query.first()
        usd = Matter(number="COMP-USD-1", client_id=base.client_id, name="Dollar matter", billing_type="flat",
                    currency="USD", originating_user_id=u.id, responsible_user_id=u.id)
        eur = Matter(number="COMP-EUR-1", client_id=base.client_id, name="Euro matter", billing_type="flat",
                    currency="EUR", originating_user_id=u.id, responsible_user_id=u.id)
        db.session.add_all([usd, eur])
        db.session.flush()

        usd_inv = Invoice(number="COMP-INV-1", matter_id=usd.id, client_id=usd.client_id, status="sent",
                          issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                          currency="USD")
        db.session.add(usd_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=usd_inv.id, description="Services", amount_cents=2501, kind="fee"))
        db.session.flush()
        usd_inv.recalc()

        eur_inv = Invoice(number="COMP-INV-2", matter_id=eur.id, client_id=eur.client_id, status="sent",
                          issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                          currency="EUR")
        db.session.add(eur_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur_inv.id, description="Services", amount_cents=50, kind="fee"))
        db.session.flush()
        eur_inv.recalc()
        db.session.commit()

        db.session.add(Payment(invoice_id=usd_inv.id, matter_id=usd.id, client_id=usd.client_id,
                               amount_cents=2501, method="check", account="operating", received_on=date.today()))
        db.session.add(Payment(invoice_id=eur_inv.id, matter_id=eur.id, client_id=eur.client_id,
                               amount_cents=50, method="check", account="operating", received_on=date.today()))
        db.session.commit()
        return u.id


def test_compensation_data_splits_currencies_instead_of_summing_them(app, usd_and_eur_fee_payments):
    from app.blueprints.money import compensation_data
    with app.app_context():
        matter_rows, user_rows, totals = compensation_data(date.today(), date.today())
    assert totals["fee"] == {"USD": 2501, "EUR": 50}
    row = next(r for r in user_rows if r["user"] and r["user"].id == usd_and_eur_fee_payments)
    # No working split saved for either matter, so 100% defaults to the responsible attorney.
    assert row["working"] == {"USD": 2501, "EUR": 50}
    assert row["originating"] == {"USD": 2501, "EUR": 50}
    matters = {r["matter"].number: r for r in matter_rows}
    assert matters["COMP-USD-1"]["currency"] == "USD" and matters["COMP-USD-1"]["fee"] == 2501
    assert matters["COMP-EUR-1"]["currency"] == "EUR" and matters["COMP-EUR-1"]["fee"] == 50


def test_compensation_report_card_splits_currencies_instead_of_summing_them(client, usd_and_eur_fee_payments):
    page = client.get("/reports/compensation").data.decode()
    m = re.search(r'<div class="label">Fees collected</div><div class="value">([^<]+)</div>', page)
    assert m, "could not find the Fees collected card"
    assert "€0.50 + $25.01" in m.group(1), m.group(1)
    assert "$0.50" not in page  # the euro fee must not be relabeled as fifty US cents


def test_compensation_report_matter_rows_use_their_own_currency(client, usd_and_eur_fee_payments):
    page = client.get("/reports/compensation").data.decode()
    assert "€0.50" in page, page
    assert "$25.01" in page, page


def test_compensation_csv_splits_currencies_instead_of_summing_them(client, usd_and_eur_fee_payments):
    page = client.get("/reports/compensation?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Matter", "Name", "Client", "Role", "Person", "Percent", "Currency", "Allocated",
                       "Fee collected", "Payment total", "Flag"]
    matter_rows = {(r[0], r[6]): r for r in rows if r[3] == "working" and r[0] not in ("TOTAL", "ALL")}
    assert matter_rows[("COMP-USD-1", "USD")][8] == "25.01", matter_rows[("COMP-USD-1", "USD")]
    assert matter_rows[("COMP-EUR-1", "EUR")][8] == "0.50", matter_rows[("COMP-EUR-1", "EUR")]
    all_rows = {r[6]: r for r in rows if r[0] == "ALL"}
    assert set(all_rows) == {"USD", "EUR"}, all_rows
    assert all_rows["USD"][8] == "25.01", all_rows["USD"]
    assert all_rows["EUR"][8] == "0.50", all_rows["EUR"]
