"""QA issue #64: same defect class as #60-#63, at /reports/wip. A EUR matter's unbilled time
and expenses displayed with a bare dollar sign, and the report's totals added the euro figure
into the dollar figure instead of keeping them separate. The CSV export also had no Currency
column, so a euro row was indistinguishable from a dollar row.

Run: .venv/bin/python -m pytest tests/test_wip_currency.py -q
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
DB_PATH = os.path.join(ROOT, "data", "test_wip_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_wip_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_wip_currency")

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
def unbilled_usd_and_eur(app):
    """A USD matter with 300.00 unbilled (2h at $150/hr) and a EUR matter with 200.00 unbilled
    (2h at 100/hr in the matter's own currency), both billable and not yet invoiced. That makes
    every currency-aware total in this database exactly these two figures."""
    from app.extensions import db
    from app.models import Expense, Matter, TimeEntry, User
    with app.app_context():
        u = User.query.first()
        usd = Matter.query.filter_by(number="M-1001").first()
        eur = Matter(number="WIP-EUR-1", client_id=usd.client_id, name="Euro matter", billing_type="hourly",
                    currency="EUR")
        db.session.add(eur)
        db.session.flush()
        # seed.py leaves M-1002 with its own unbilled time/expense; not billable here so this
        # database's WIP is exactly the two rows this fixture adds.
        for t in TimeEntry.query.all():
            t.billable = False
        for e in Expense.query.all():
            e.billable = False
        db.session.add(TimeEntry(matter_id=usd.id, user_id=u.id, date=date.today(), minutes=120,
                                 rate_cents=15000, billable=True))
        db.session.add(TimeEntry(matter_id=eur.id, user_id=u.id, date=date.today(), minutes=120,
                                 rate_cents=10000, billable=True))
        db.session.commit()
        return usd.number, eur.number


def test_wip_report_rows_use_their_own_currency(client, unbilled_usd_and_eur):
    page = client.get("/reports/wip").data.decode()
    assert "€200.00" in page, page
    assert "$300.00" in page, page
    assert "$200.00" not in page  # the euro row must not be relabeled as two hundred US dollars


def test_wip_report_footer_splits_currencies_instead_of_summing_them(client, unbilled_usd_and_eur):
    page = client.get("/reports/wip").data.decode()
    m = re.search(r'<tr><th colspan="3">Total</th>.*?</tr>', page, re.DOTALL)
    assert m, "could not find the WIP totals row"
    footer = m.group(0)
    assert "€200.00 + $300.00" in footer, footer
    assert "Matters are in more than one currency" in page


def test_wip_csv_has_a_currency_column_and_splits_totals(client, unbilled_usd_and_eur):
    page = client.get("/reports/wip?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Matter", "Name", "Client", "Billing", "Currency", "Unbilled hours", "Unbilled time",
                       "Unbilled expenses", "Total WIP", "Oldest item"]
    matter_rows = {r[0]: r for r in rows if r[0] not in ("Matter", "TOTAL")}
    assert matter_rows["M-1001"][4] == "USD", matter_rows["M-1001"]
    assert matter_rows["M-1001"][8] == "300.00", matter_rows["M-1001"]
    assert matter_rows["WIP-EUR-1"][4] == "EUR", matter_rows["WIP-EUR-1"]
    assert matter_rows["WIP-EUR-1"][8] == "200.00", matter_rows["WIP-EUR-1"]
    totals = {r[4]: r for r in rows if r[0] == "TOTAL"}
    assert set(totals) == {"USD", "EUR"}, totals
    assert totals["USD"][8] == "300.00", totals["USD"]
    assert totals["EUR"][8] == "200.00", totals["EUR"]
