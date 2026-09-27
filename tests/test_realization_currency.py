"""QA issue #70: same defect class as #60-#64/#66-#69, at /reports/realization. A matter has exactly
one currency, so matter rows stay scalar. But an attorney who logs time on matters in more than one
currency had their worked/billed/collected/write-downs (and the report totals) summed straight into
one dollar figure with no currency indicator, the same mistake already fixed for compensation (#68).

Run: .venv/bin/python -m pytest tests/test_realization_currency.py -q
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
DB_PATH = os.path.join(ROOT, "data", "test_realization_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_realization_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_realization_currency")

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
def one_attorney_two_currencies(app):
    """One timekeeper logs 60 billable minutes at $100/hr on a USD matter and 60 billable minutes at
    EUR1/hr on a EUR matter, both fully invoiced and fully paid today. Worked, billed and collected all
    differ by currency for this attorney and for the report totals, not just per matter."""
    from app.blueprints.invoices import build_for_matter
    from app.extensions import db
    from app.models import Matter, Payment, TimeEntry, User
    with app.app_context():
        u = User.query.first()
        base = Matter.query.first()
        usd = Matter(number="REAL-USD-1", client_id=base.client_id, name="Dollar matter", billing_type="hourly",
                    currency="USD")
        eur = Matter(number="REAL-EUR-1", client_id=base.client_id, name="Euro matter", billing_type="hourly",
                    currency="EUR")
        db.session.add_all([usd, eur])
        db.session.flush()

        db.session.add(TimeEntry(matter_id=usd.id, user_id=u.id, date=date.today(), minutes=60, rate_cents=10000,
                                 description="USD work", billable=True))
        db.session.add(TimeEntry(matter_id=eur.id, user_id=u.id, date=date.today(), minutes=60, rate_cents=100,
                                 description="EUR work", billable=True))
        db.session.commit()

        usd_invoices = build_for_matter(usd, u, date.today(), date.today())
        eur_invoices = build_for_matter(eur, u, date.today(), date.today())
        for inv in usd_invoices + eur_invoices:
            inv.status = "sent"
        db.session.commit()

        for inv in usd_invoices:
            db.session.add(Payment(invoice_id=inv.id, matter_id=usd.id, client_id=inv.client_id,
                                   amount_cents=inv.total_cents, account="operating", method="check",
                                   received_on=date.today()))
        for inv in eur_invoices:
            db.session.add(Payment(invoice_id=inv.id, matter_id=eur.id, client_id=inv.client_id,
                                   amount_cents=inv.total_cents, account="operating", method="check",
                                   received_on=date.today()))
        db.session.commit()
        return u.id, usd.id, eur.id


def test_realization_data_splits_matter_rows_by_their_own_currency(app, one_attorney_two_currencies):
    from app.blueprints.reports import realization_data
    _, usd_id, eur_id = one_attorney_two_currencies
    with app.app_context():
        user_rows, matter_rows, totals = realization_data(date.today(), date.today())
    by_matter = {r["matter"].id: r for r in matter_rows}
    usd_row, eur_row = by_matter[usd_id], by_matter[eur_id]
    assert usd_row["currency"] == "USD" and usd_row["worked"] == 10000 and usd_row["billed"] == 10000
    assert eur_row["currency"] == "EUR" and eur_row["worked"] == 100 and eur_row["billed"] == 100


def test_realization_data_splits_user_rows_and_totals_by_currency(app, one_attorney_two_currencies):
    from app.blueprints.reports import realization_data
    user_id, usd_id, eur_id = one_attorney_two_currencies
    with app.app_context():
        user_rows, matter_rows, totals = realization_data(date.today(), date.today())
    ann = next(r for r in user_rows if r["user"] and r["user"].id == user_id)
    assert ann["worked"] == {"USD": 10000, "EUR": 100}
    assert ann["billed"] == {"USD": 10000, "EUR": 100}
    assert ann["collected"] == {"USD": 10000, "EUR": 100}
    assert ann["billing_pct"] == {"USD": 100.0, "EUR": 100.0}
    assert totals["worked"] == {"USD": 10000, "EUR": 100}
    assert totals["billed"] == {"USD": 10000, "EUR": 100}
    assert totals["collected"] == {"USD": 10000, "EUR": 100}


def _today_range():
    t = date.today().isoformat()
    return {"from": t, "to": t}


def test_realization_report_card_splits_currencies_instead_of_summing_them(client, one_attorney_two_currencies):
    page = client.get("/reports/realization", query_string=_today_range()).data.decode()
    m = re.search(r'<div class="label">Worked</div><div class="value">([^<]+)</div>', page)
    assert m, "could not find the Worked card"
    assert "€1.00 + $100.00" in m.group(1), m.group(1)
    assert "$1.00" not in page  # the euro entry must not be relabeled as one US dollar


def test_realization_report_matter_rows_use_their_own_currency(client, one_attorney_two_currencies):
    page = client.get("/reports/realization", query_string=_today_range()).data.decode()
    assert "€1.00" in page, page
    assert "$100.00" in page, page


def test_realization_csv_splits_currencies_instead_of_summing_them(client, one_attorney_two_currencies):
    page = client.get("/reports/realization", query_string=dict(_today_range(), format="csv")).data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Group", "Key", "Name", "Currency", "Hours", "Worked", "Billed", "Collected",
                       "Billing realization %", "Collection realization %", "Write-downs", "Flag"]
    matter_rows = {r[1]: r for r in rows if r[0] == "matter"}
    assert matter_rows["REAL-USD-1"][3:8] == ["USD", "1.00", "100.00", "100.00", "100.00"]
    assert matter_rows["REAL-EUR-1"][3:8] == ["EUR", "1.00", "1.00", "1.00", "1.00"]
    total_rows = {r[3]: r for r in rows if r[0] == "total"}
    assert set(total_rows) == {"USD", "EUR"}, total_rows
    assert total_rows["USD"][5] == "100.00" and total_rows["EUR"][5] == "1.00"
