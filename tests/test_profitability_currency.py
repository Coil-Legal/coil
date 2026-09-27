"""QA issue #69: same defect class as #60-#64/#66-#68, at /reports/profitability. A EUR matter's
collected revenue was added straight into the dollar total (a 0.50 EUR payment showed as $0.50,
part of a page with no euro sign anywhere), and the same mistake would follow through to cost,
margin and margin %, which the report also renders with a bare dollar sign.

Run: .venv/bin/python -m pytest tests/test_profitability_currency.py -q
"""
import csv
import io
import os
import re
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_profitability_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_profitability_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_profitability_currency")

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
def usd_and_eur_matters(app):
    """One timekeeper logs 30 billable minutes on a USD matter with a $25.01 payment, and nothing
    but a €0.50 payment on a EUR matter, both received today. That makes revenue, cost and margin
    all differ by currency on the same page, not just the grand total."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, Payment, TimeEntry, User
    with app.app_context():
        u = User.query.first()
        u.cost_rate_cents = 3000
        base = Matter.query.first()
        usd = Matter(number="PROF-USD-1", client_id=base.client_id, name="Dollar matter", billing_type="flat",
                    currency="USD")
        eur = Matter(number="PROF-EUR-1", client_id=base.client_id, name="Euro matter", billing_type="flat",
                    currency="EUR")
        db.session.add_all([usd, eur])
        db.session.flush()

        db.session.add(TimeEntry(matter_id=usd.id, user_id=u.id, date=date.today(), minutes=30, rate_cents=30000,
                                 description="Work", billable=True))

        usd_inv = Invoice(number="PROF-INV-1", matter_id=usd.id, client_id=usd.client_id, status="sent",
                          issued_on=date.today(), due_on=date.today(), tax_cents=0, currency="USD")
        db.session.add(usd_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=usd_inv.id, description="Services", amount_cents=2501, kind="fee"))
        db.session.flush()
        usd_inv.recalc()

        eur_inv = Invoice(number="PROF-INV-2", matter_id=eur.id, client_id=eur.client_id, status="sent",
                          issued_on=date.today(), due_on=date.today(), tax_cents=0, currency="EUR")
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
        return usd.id, eur.id


def test_profitability_data_splits_currencies_instead_of_summing_them(app, usd_and_eur_matters):
    from app.blueprints.reports import profitability_data
    usd_id, eur_id = usd_and_eur_matters
    with app.app_context():
        rows, totals = profitability_data(date.today(), date.today())
    by_id = {r["matter"].id: r for r in rows}
    usd_row, eur_row = by_id[usd_id], by_id[eur_id]
    assert usd_row["currency"] == "USD" and usd_row["revenue"] == 2501 and usd_row["time_cost"] == 1500
    assert usd_row["cost"] == 1500 and usd_row["margin"] == 1001 and usd_row["margin_pct"] == 40.0
    assert eur_row["currency"] == "EUR" and eur_row["revenue"] == 50 and eur_row["cost"] == 0
    assert eur_row["margin"] == 50 and eur_row["margin_pct"] == 100.0
    assert totals["revenue"] == {"USD": 2501, "EUR": 50}
    assert totals["cost"] == {"USD": 1500, "EUR": 0}
    assert totals["margin"] == {"USD": 1001, "EUR": 50}
    assert totals["margin_pct"] == {"USD": 40.0, "EUR": 100.0}


def test_profitability_report_card_splits_currencies_instead_of_summing_them(client, usd_and_eur_matters):
    page = client.get("/reports/profitability").data.decode()
    m = re.search(r'<div class="label">Revenue collected</div><div class="value">([^<]+)</div>', page)
    assert m, "could not find the Revenue collected card"
    assert "€0.50 + $25.01" in m.group(1), m.group(1)
    assert "$0.50" not in page  # the euro payment must not be relabeled as fifty US cents


def test_profitability_report_matter_rows_use_their_own_currency(client, usd_and_eur_matters):
    page = client.get("/reports/profitability").data.decode()
    assert "€0.50" in page, page
    assert "$25.01" in page, page


def test_profitability_csv_splits_currencies_instead_of_summing_them(client, usd_and_eur_matters):
    page = client.get("/reports/profitability?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Matter", "Name", "Client", "Status", "Currency", "Revenue", "Hours", "Time cost",
                       "Non-billable expenses", "Total cost", "Margin", "Margin %", "Flag"]
    matter_rows = {r[0]: r for r in rows if r[0] not in ("TOTAL", "")}
    assert matter_rows["PROF-USD-1"][4:11] == ["USD", "25.01", "0.50", "15.00", "0.00", "15.00", "10.01"]
    assert matter_rows["PROF-EUR-1"][4:11] == ["EUR", "0.50", "0.00", "0.00", "0.00", "0.00", "0.50"]
    total_rows = {r[4]: r for r in rows if r[0] == "TOTAL"}
    assert set(total_rows) == {"USD", "EUR"}, total_rows
    assert total_rows["USD"][5] == "25.01" and total_rows["EUR"][5] == "0.50"
