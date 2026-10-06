"""Invoice PDF heading and footer must localize for a Spanish client.

render_invoice_pdf() printed the heading via tpl.title, which defaults to the English
DEFAULT_TITLE ("INVOICE") whenever the firm has not customised it, and the footer via a
doc_title built from a hardcoded "Invoice {number}", regardless of the client's language.
Every other label on the PDF (Bill to, Due, column headings...) already switches with the
client's language. Filed as Coil QA #135, after #130 localized the rest of the PDF.
"""
import io

from pypdf import PdfReader

from tests.test_phase1_independent import app  # noqa: F401


def _invoice(app, language):
    from app.extensions import db
    from app.models import Matter, Contact, Invoice, InvoiceLine
    with app.app_context():
        m = Matter.query.filter_by(number="M-PHASE1").first()
        c = db.session.get(Contact, m.client_id)
        c.language = language
        inv = Invoice(number="INV-9002", matter_id=m.id, client_id=m.client_id, status="sent",
                      subtotal_cents=10000, total_cents=10000)
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, kind="flat", description="Flat fee",
                                   quantity=1.0, amount_cents=10000))
        db.session.commit()
        return inv.id


def _pdf_text(app, inv_id):
    from app.extensions import db
    from app.blueprints.invoices import build_pdf
    from app.models import Invoice
    with app.app_context():
        inv = db.session.get(Invoice, inv_id)
        path = build_pdf(inv)
        db.session.commit()
        data = open(path, "rb").read()
    assert data[:5] == b"%PDF-"
    return PdfReader(io.BytesIO(data)).pages[0].extract_text()


def test_spanish_client_gets_localized_heading_and_footer(app):
    inv_id = _invoice(app, "es")
    text = _pdf_text(app, inv_id)
    assert "FACTURA" in text, "the stock heading was not localized to Spanish"
    assert "INVOICE" not in text, "the English stock heading leaked into a Spanish invoice"
    assert "Factura INV-9002" in text, "the footer document title was not localized to Spanish"
    assert "Página" in text, "the footer 'Page' word was not localized to Spanish"


def test_english_client_heading_and_footer_unchanged(app):
    inv_id = _invoice(app, "en")
    text = _pdf_text(app, inv_id)
    assert "INVOICE" in text
    assert "Invoice INV-9002" in text
    assert "Page" in text
