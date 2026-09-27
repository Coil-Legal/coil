"""QA issues #60 and #61: a firm with invoices in more than one currency saw its totals added
into a single dollar figure, on both the invoice list (tab badges + footer row) and the
dashboard's Outstanding A/R card. Each row already showed its own currency; the aggregates
did not. A disclosure sentence describing that flaw is not a fix (see issue #60's comment on
the prior attempt) — the totals themselves must be split by currency instead.

Run: .venv/bin/python -m pytest tests/test_mixed_currency_totals.py -q
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
DB_PATH = os.path.join(ROOT, "data", "test_mixed_currency_totals.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_mixed_currency_totals")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_mixed_currency_totals")

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
def eur_sent_invoice(app):
    """seed.py creates matters and contacts but no invoices, so this fixture creates the only
    two invoices in the database: one USD 300.00 and one EUR 200.00, both sent and unpaid.
    That makes every currency-aware total in this database exactly these two figures."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        usd = Invoice(number="MCT-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="USD")
        db.session.add(usd)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=usd.id, description="Services", amount_cents=30000, kind="fee"))
        db.session.flush()
        usd.recalc()

        eur = Invoice(number="MCT-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="EUR")
        db.session.add(eur)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur.id, description="Services", amount_cents=20000, kind="fee"))
        db.session.flush()
        eur.recalc()
        db.session.commit()
        return eur.number


@pytest.fixture(scope="module")
def eur_and_usd_payments(app, eur_sent_invoice):
    """Issue #63's own numbers: a $25.01 check against the USD invoice and a $0.50 (50-cent) check
    against the EUR invoice, both received today so both land in the revenue report's default range."""
    from app.extensions import db
    from app.models import Invoice, Payment
    with app.app_context():
        usd = Invoice.query.filter_by(number="MCT-0001").first()
        eur = Invoice.query.filter_by(number="MCT-0002").first()
        db.session.add(Payment(invoice_id=usd.id, matter_id=usd.matter_id, client_id=usd.client_id,
                               amount_cents=2501, method="check", account="operating",
                               received_on=date.today()))
        db.session.add(Payment(invoice_id=eur.id, matter_id=eur.matter_id, client_id=eur.client_id,
                               amount_cents=50, method="check", account="operating",
                               received_on=date.today()))
        db.session.commit()


def test_invoice_list_tab_badge_splits_currencies_instead_of_summing_them(client, eur_sent_invoice):
    page = client.get("/invoices?status=sent").data.decode()
    assert "Invoices are in more than one currency" in page
    m = re.search(r'href="/invoices\?status=sent">Sent <span[^>]*>([^<]+)</span>', page)
    assert m, "could not find the Sent tab badge"
    badge = m.group(1)
    assert "€200.00 + $300.00" in badge, badge


def test_invoice_list_footer_splits_currencies_instead_of_summing_them(client, eur_sent_invoice):
    page = client.get("/invoices?status=sent").data.decode()
    m = re.search(r'<th colspan="7">[^<]*</th><th class="num">([^<]+)</th>.*?<th class="num">([^<]+)</th></tr>',
                  page)
    assert m, "could not find the invoice list totals row"
    total_cell, balance_cell = m.group(1), m.group(2)
    assert "€200.00 + $300.00" in total_cell, total_cell
    assert "€200.00 + $300.00" in balance_cell, balance_cell


def test_dashboard_outstanding_ar_splits_currencies_instead_of_summing_them(client, eur_sent_invoice):
    page = client.get("/").data.decode()
    m = re.search(r'data-card="ar">.*?<div class="value">([^<]+)</div>', page, re.DOTALL)
    assert m, "could not find the Outstanding A/R card"
    value = m.group(1)
    assert "€200.00 + $300.00" in value, value


def test_ar_aging_footer_splits_currencies_instead_of_summing_them(client, eur_sent_invoice):
    """Issue #62: same defect as #60/#61, at the /reports/ar-aging call site. Both invoices in
    eur_sent_invoice share one client and land in the 'current' bucket (due 30 days out), so the
    fix must key aging rows by (client, currency), not just client, or one of the two figures
    gets silently dropped instead of summed with the wrong symbol."""
    page = client.get("/reports/ar-aging").data.decode()
    assert "Balances are in more than one currency" in page
    m = re.search(r'<tr><th>Total</th>.*?</tr>', page, re.DOTALL)
    assert m, "could not find the A/R aging totals row"
    footer = m.group(0)
    assert "€200.00 + $300.00" in footer, footer


def test_ar_aging_csv_splits_currencies_instead_of_summing_them(client, eur_sent_invoice):
    page = client.get("/reports/ar-aging?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Client", "Currency", "Current", "1-30", "31-60", "61-90", "90+", "Total"]
    totals = {r[1]: r for r in rows if r[0] == "TOTAL"}
    assert set(totals) == {"USD", "EUR"}, totals
    assert totals["USD"][-1] == "300.00", totals["USD"]
    assert totals["EUR"][-1] == "200.00", totals["EUR"]


def test_revenue_report_top_card_splits_currencies_instead_of_summing_them(client, eur_and_usd_payments):
    """Issue #63: same defect as #60/#61/#62, at /reports/revenue. A raw sum of a $25.01 USD check
    and a $0.50 EUR check must not become one dollar figure."""
    page = client.get("/reports/revenue").data.decode()
    m = re.search(r'<div class="label">Received into operating</div><div class="value">([^<]+)</div>', page)
    assert m, "could not find the Received into operating card"
    assert "€0.50 + $25.01" in m.group(1), m.group(1)


def test_revenue_report_matter_rows_use_their_own_currency(client, eur_and_usd_payments):
    page = client.get("/reports/revenue").data.decode()
    assert "€0.50" in page, page
    assert "$25.01" in page, page
    assert "$0.50" not in page  # the euro check must not be relabeled as fifty US cents


def test_revenue_report_csv_splits_currencies_instead_of_summing_them(client, eur_and_usd_payments):
    page = client.get("/reports/revenue?format=csv").data.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(page)))
    assert rows[0] == ["Group", "Key", "Name", "Currency", "Payments", "Amount", "Surcharge", "Processor fees"]
    totals = {r[3]: r for r in rows if r[0] == "total"}
    assert set(totals) == {"USD", "EUR"}, totals
    assert totals["USD"][5] == "25.01", totals["USD"]
    assert totals["EUR"][5] == "0.50", totals["EUR"]
