"""QA issue #66: same defect class as #59-#64, at /reports/origination. A EUR payment's cents
were added straight into the dollar total (a $0.50 payment showed as part of a $4,374.01 figure
with no euro sign anywhere on the page), and the "Share" percentage column made the same mistake
one level down by dividing a euro row's cents by a dollar total.

Run: .venv/bin/python -m pytest tests/test_origination_currency.py -q
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
DB_PATH = os.path.join(ROOT, "data", "test_origination_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_origination_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_origination_currency")

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
def usd_and_eur_originated_payments(app):
    """One attorney originates a USD matter (a $25.01 payment) and a EUR matter (a $0.50 payment on
    the matter's own invoice, i.e. a real 0.50 EUR), both received today so both land in the
    origination report's default range. Two matters, one originator, so the attorney row itself
    mixes currencies (issue #66's own Share-column bug, not just the grand total's)."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter, User
    with app.app_context():
        u = User.query.first()
        base = Matter.query.first()
        usd = Matter(number="ORIG-USD-1", client_id=base.client_id, name="Dollar matter", billing_type="flat",
                    currency="USD", originating_user_id=u.id)
        eur = Matter(number="ORIG-EUR-1", client_id=base.client_id, name="Euro matter", billing_type="flat",
                    currency="EUR", originating_user_id=u.id)
        db.session.add_all([usd, eur])
        db.session.flush()

        usd_inv = Invoice(number="ORIG-INV-1", matter_id=usd.id, client_id=usd.client_id, status="sent",
                          issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                          currency="USD")
        db.session.add(usd_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=usd_inv.id, description="Services", amount_cents=2501, kind="fee"))
        db.session.flush()
        usd_inv.recalc()

        eur_inv = Invoice(number="ORIG-INV-2", matter_id=eur.id, client_id=eur.client_id, status="sent",
                          issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                          currency="EUR")
        db.session.add(eur_inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur_inv.id, description="Services", amount_cents=50, kind="fee"))
        db.session.flush()
        eur_inv.recalc()
        db.session.commit()

        from app.models import Payment
        db.session.add(Payment(invoice_id=usd_inv.id, matter_id=usd.id, client_id=usd.client_id,
                               amount_cents=2501, method="check", account="operating", received_on=date.today()))
        db.session.add(Payment(invoice_id=eur_inv.id, matter_id=eur.id, client_id=eur.client_id,
                               amount_cents=50, method="check", account="operating", received_on=date.today()))
        db.session.commit()
        return u.id


def test_origination_data_splits_currencies_instead_of_summing_them(app, usd_and_eur_originated_payments):
    from app.blueprints.reports import origination_data
    with app.app_context():
        rows, totals = origination_data(date.today(), date.today())
    assert totals["by_currency"] == {"USD": 2501, "EUR": 50}
    row = next(r for r in rows if r["user"] and r["user"].id == usd_and_eur_originated_payments)
    assert row["by_currency"] == {"USD": 2501, "EUR": 50}
    matters = {m["matter"].number: m for m in row["matters"] if m["matter"]}
    assert matters["ORIG-USD-1"]["by_currency"] == {"USD": 2501}
    assert matters["ORIG-EUR-1"]["by_currency"] == {"EUR": 50}
    # Share must not divide the euro row's cents by the dollar total or vice versa.
    assert row["share"] == "100.0% EUR + 100.0% USD"


def test_origination_report_card_splits_currencies_instead_of_summing_them(client, usd_and_eur_originated_payments):
    page = client.get("/reports/origination").data.decode()
    m = re.search(r'<div class="label">Collected into operating</div><div class="value">([^<]+)</div>', page)
    assert m, "could not find the Collected into operating card"
    assert "€0.50 + $25.01" in m.group(1), m.group(1)
    assert "$0.50" not in page  # the euro payment must not be relabeled as fifty US cents


def test_origination_report_matter_rows_use_their_own_currency(client, usd_and_eur_originated_payments):
    page = client.get("/reports/origination").data.decode()
    assert "€0.50" in page, page
    assert "$25.01" in page, page


def test_origination_csv_splits_currencies_instead_of_summing_them(client, usd_and_eur_originated_payments):
    page = client.get("/reports/origination?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Attorney", "Matter", "Name", "Client", "Payments", "Currency", "Collected", "Flag"]
    matter_rows = {(r[1], r[5]): r for r in rows if r[1] not in ("TOTAL",) and r[0] != "ALL"}
    assert matter_rows[("ORIG-USD-1", "USD")][6] == "25.01"
    assert matter_rows[("ORIG-EUR-1", "EUR")][6] == "0.50"
    totals = {r[5]: r for r in rows if r[0] == "ALL"}
    assert set(totals) == {"USD", "EUR"}, totals
    assert totals["USD"][6] == "25.01", totals["USD"]
    assert totals["EUR"][6] == "0.50", totals["EUR"]
