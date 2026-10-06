"""Issues #141 and #140, both in the same mixed-currency statement PDF as #133/#136/#138:
a call site that string-interpolates money without that entry's own currency.

#141: render_statement_pdf()'s Activity table drew every row's Charge and Payment/credit
figure in the statement's single blended currency (money(), closing over st["currency"])
instead of that entry's own currency (already carried on the entry dict and already used
correctly by the HTML statement page). Only the running-balance column is meant to stay
blended.

#140: the final "Balance due" total's amount cell was left at its old 22mm width when
#133 widened its content from a single blended figure ("$550.00") to a per-currency one
("EUR275.00 + GBP275.00"); fpdf right-aligns by drawing backward from the cell's right
edge, so text wider than the cell overlaps the "Balance due" label instead of extending
into blank space.

Run: .venv/bin/python -m pytest tests/test_statement_pdf_activity_currency_and_overlap.py -q
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
DB_PATH = os.path.join(ROOT, "data", "test_statement_pdf_activity_currency_and_overlap.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_statement_pdf_activity_currency_and_overlap")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_statement_pdf_activity_currency_and_overlap")

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
def mixed_currency_client(app):
    """Same repro as #133/#140/#141: one EUR invoice and one GBP invoice, 27500 cents each,
    same client, same matter, both sent and unpaid."""
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        eur = Invoice(number="SPA-0001", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="EUR")
        db.session.add(eur)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=eur.id, description="Services", amount_cents=27500, kind="fee"))
        db.session.flush()
        eur.recalc()

        gbp = Invoice(number="SPA-0002", matter_id=m.id, client_id=m.client_id, status="sent",
                     issued_on=date.today(), due_on=date.today() + timedelta(days=30), tax_cents=0,
                     currency="GBP")
        db.session.add(gbp)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=gbp.id, description="Services", amount_cents=27500, kind="fee"))
        db.session.flush()
        gbp.recalc()
        db.session.commit()
        return m.client_id


def _activity_rows(text):
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Date") and "Charge" in l)
    return lines[start + 1:start + 1 + 10]  # a handful of rows after the header is plenty


def test_activity_row_charge_uses_entrys_own_currency(app, mixed_currency_client):
    """#141: the Charge column for each invoice row must read that invoice's own currency
    symbol, not the statement's blended fallback."""
    from app.extensions import db
    from app.blueprints.statements import build_statement, render_statement_pdf
    from app.models import Contact

    with app.app_context():
        c = db.session.get(Contact, mixed_currency_client)
        st = build_statement(c)
        data = bytes(render_statement_pdf(st).output())
    assert data[:5] == b"%PDF-"
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    rows = _activity_rows(text)
    eur_row = next(l for l in rows if "SPA-0001" in l)
    gbp_row = next(l for l in rows if "SPA-0002" in l)
    # Charge column: each row's own currency, not the blended fallback.
    assert "€275.00" in eur_row, eur_row
    assert "£275.00" in gbp_row, gbp_row
    # Running-balance column stays blended by design, untouched by this fix: it still
    # reads in the firm's own currency on both rows.
    assert "$275.00" in eur_row and "$550.00" in gbp_row


def test_balance_due_total_does_not_overlap_its_label(app, mixed_currency_client):
    """#140: the bottom total line must not interleave the label and the amount. Checked
    the way the original report was: pdftotext -layout, which exposed the overlap as
    "Balance€275.00" / "due    + £275.00" when the amount cell was too narrow."""
    from app.extensions import db
    from app.blueprints.statements import build_statement, render_statement_pdf
    from app.models import Contact

    with app.app_context():
        c = db.session.get(Contact, mixed_currency_client)
        st = build_statement(c)
        pdf = render_statement_pdf(st)
        data = bytes(pdf.output())

    pdf_path = os.path.join(PDF_DIR, "balance-due-overlap.pdf")
    os.makedirs(PDF_DIR, exist_ok=True)
    with open(pdf_path, "wb") as f:
        f.write(data)
    layout = subprocess.run(["pdftotext", "-layout", pdf_path, "-"], capture_output=True, text=True, check=True).stdout
    # The summary box's column heading is also literally "Balance due" (just the label,
    # right-aligned over its own 43.5mm column with no amount on that line); only the
    # bottom total line *starts* with it.
    balance_due_lines = [l for l in layout.splitlines() if l.strip().startswith("Balance due")]
    assert balance_due_lines, layout
    line = balance_due_lines[0]
    # Pre-fix, the amount overlapped backward into the label's cell: pdftotext -layout
    # rendered the label and the figure on two separate lines instead of side by side.
    assert "€275.00" in line and "£275.00" in line, line
