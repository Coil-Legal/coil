"""QA issue #71: same defect class as #60-#64/#66-#68/#70, at /reports/productivity. A timekeeper
who logged billable time against a EUR matter had that time's dollar value folded into the
report's plain USD total, both in the stat card and the per-user total, with no euro sign and no
Currency column in the CSV.

Run: .venv/bin/python -m pytest tests/test_productivity_currency.py -q
"""
import csv
import io
import os
import shutil
import subprocess
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_productivity_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_productivity_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_productivity_currency")

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
def billable_usd_and_eur(app):
    """One user with 2h billable at $150/hr on a USD matter (300.00) and 2h billable at 100/hr on
    a EUR matter (200.00), both in the current month, both unbilled. Every other seeded entry is
    marked non-billable so this database's billable total is exactly these two figures."""
    from app.extensions import db
    from app.models import Matter, TimeEntry, User
    with app.app_context():
        u = User.query.first()
        usd = Matter.query.filter_by(number="M-1001").first()
        eur = Matter(number="PROD-EUR-1", client_id=usd.client_id, name="Euro matter", billing_type="hourly",
                    currency="EUR")
        db.session.add(eur)
        db.session.flush()
        for t in TimeEntry.query.all():
            t.billable = False
        db.session.add(TimeEntry(matter_id=usd.id, user_id=u.id, date=date.today(), minutes=120,
                                 rate_cents=15000, billable=True))
        db.session.add(TimeEntry(matter_id=eur.id, user_id=u.id, date=date.today(), minutes=120,
                                 rate_cents=10000, billable=True))
        db.session.commit()
        return u.name, usd.number, eur.number


def test_productivity_stat_card_splits_currencies_instead_of_summing_them(client, billable_usd_and_eur):
    _, usd_number, eur_number = billable_usd_and_eur
    page = client.get("/reports/productivity").data.decode()
    assert "€200.00 + $300.00" in page, page
    assert "$500.00" not in page  # the euro figure must not be folded into the dollar total


def test_productivity_user_total_splits_currencies(client, billable_usd_and_eur):
    user_name, _, _ = billable_usd_and_eur
    page = client.get("/reports/productivity").data.decode()
    idx = page.index(user_name)
    row = page[idx:idx + 2000]
    assert "€200.00 + $300.00" in row, row


def test_productivity_csv_has_a_currency_column_and_splits_totals(client, billable_usd_and_eur):
    user_name, _, _ = billable_usd_and_eur
    page = client.get("/reports/productivity?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["User", "Month", "Billable hours", "Non-billable hours", "Total hours", "Billed hours",
                       "Currency", "Billable value"]
    month = date.today().strftime("%Y-%m")
    month_rows = {r[6]: r for r in rows if r[0] == user_name and r[1] == month}
    assert month_rows["USD"][7] == "300.00", month_rows
    assert month_rows["EUR"][7] == "200.00", month_rows
    total_rows = {r[6]: r for r in rows if r[0] == user_name and r[1] == "TOTAL"}
    assert total_rows["USD"][7] == "300.00", total_rows
    assert total_rows["EUR"][7] == "200.00", total_rows
    # hours are currency-neutral: both TOTAL rows for this user carry the same combined hours.
    assert total_rows["USD"][2] == "4.00", total_rows
    assert total_rows["EUR"][2] == "4.00", total_rows
