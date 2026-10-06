"""Issue #133 (the PDF/email side of #125): #125 fixed the HTML statement page to show a
per-currency breakdown ("EUR275.00 + GBP275.00") instead of summing cents across currencies
under one $ symbol, but render_statement_pdf() and send() still built their figures from the
old blended st["totals"] dict with a single fallback currency, so the PDF and the emailed
statement kept reproducing the original bug even after #125 shipped.

Run: .venv/bin/python -m pytest tests/test_statement_pdf_email_mixed_currency.py -q
"""
import io
import os
import shutil
import subprocess
import sys
from datetime import date, timedelta

import pytest
from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_statement_pdf_email_mixed_currency.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_statement_pdf_email_mixed_currency")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_statement_pdf_email_mixed_currency")

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
def mixed_currency_client(app):
    """Same numbers as #125/#133's own repro: one EUR invoice and one GBP invoice, 27500 cents
    each, same client, same matter, both sent and unpaid. A raw sum would be 55000 cents,
    shown as $550.00 under one currency."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        eur = Invoice(number="SPE-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="EUR")
        db.session.add(eur)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur.id, description="Services", amount_cents=27500, kind="fee"))
        db.session.flush()
        eur.recalc()

        gbp = Invoice(number="SPE-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="GBP")
        db.session.add(gbp)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=gbp.id, description="Services", amount_cents=27500, kind="fee"))
        db.session.flush()
        gbp.recalc()
        db.session.commit()
        return m.client_id


def test_statement_pdf_splits_currencies_instead_of_blending(app, mixed_currency_client):
    from app.extensions import db
    from app.blueprints.statements import build_statement, render_statement_pdf
    from app.models import Contact

    with app.app_context():
        c = db.session.get(Contact, mixed_currency_client)
        st = build_statement(c)
        data = bytes(render_statement_pdf(st).output())
    assert data[:5] == b"%PDF-"
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    # The Activity table's chronological running balance still blends currencies into one
    # figure on purpose (same as the HTML page's st.closing, left alone by #125); only the
    # summary box, the per-matter subtotal row and the final balance-due total are this
    # issue's own repro and are checked here.
    heading_line = next(l for l in text.splitlines() if "Invoiced" in l and "Paid" in l)
    idx = text.splitlines().index(heading_line)
    figures_line = text.splitlines()[idx + 1]
    assert "$" not in figures_line, figures_line
    assert figures_line.count("€275.00") == 2 and figures_line.count("£275.00") == 2, figures_line
    assert "Subtotal" in text
    assert text.count("€275.00") >= 3 and text.count("£275.00") >= 3, text
    balance_due_line = next(l for l in text.splitlines() if l.startswith("Balance due"))
    assert "$" not in balance_due_line and "€275.00" in balance_due_line and "£275.00" in balance_due_line


def test_statement_email_splits_currencies_instead_of_blending(app, client, mixed_currency_client, monkeypatch):
    from app.blueprints import statements as st_bp

    sent = {}

    def capture(to, subject, html, text=None, **kwargs):
        sent["html"] = html
        sent["text"] = text
        return True

    monkeypatch.setattr(st_bp, "send_email", capture)
    r = client.post(f"/statements/{mixed_currency_client}/send", data={"_csrf": client._csrf})
    assert r.status_code == 302, r.data[:300]
    assert "$550.00" not in sent["html"] and "$550.00" not in sent["text"]
    assert "€275.00" in sent["html"] and "£275.00" in sent["html"]
    assert "€275.00" in sent["text"] and "£275.00" in sent["text"]
