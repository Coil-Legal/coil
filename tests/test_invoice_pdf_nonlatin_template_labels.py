"""Invoice PDF must render a non-Latin template label override and payment instructions.

render_invoice_pdf's enable_unicode scan covered the client/firm/line text and the template
title, but never the label overrides a firm sets in Settings > Invoice template (label_due,
label_bill_to, etc.) or the payment instructions / firm footer text actually printed on the
page. A firm that localizes just its invoice labels (e.g. Greek "Due") got a PDF where the
label printed as a row of question marks even though every other field on the invoice
stayed ASCII. Filed as Coil QA #119.
"""
import io

from pypdf import PdfReader

from tests.test_phase1_independent import app  # noqa: F401

GREEK_DUE = "Προθεσμία"
GREEK_INSTRUCTIONS = "Πληρώστε εντός 30 ημερών."


def _invoice(app):
    from app.extensions import db
    from app.models import Firm, Matter, Invoice, InvoiceLine
    with app.app_context():
        m = Matter.query.filter_by(number="M-PHASE1").first()
        firm = Firm.get()
        firm.invoice_labels_json = '{"due": "%s"}' % GREEK_DUE
        firm.invoice_payment_instructions = GREEK_INSTRUCTIONS
        inv = Invoice(number="INV-9001", matter_id=m.id, client_id=m.client_id, status="sent",
                      subtotal_cents=10000, total_cents=10000)
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, kind="flat", description="Flat fee",
                                   quantity=1.0, amount_cents=10000))
        db.session.commit()
        return inv.id


def test_invoice_pdf_renders_non_latin_label_override_and_payment_instructions(app):
    from app.extensions import db
    from app.blueprints.invoices import build_pdf
    from app.models import Invoice

    inv_id = _invoice(app)
    with app.app_context():
        inv = db.session.get(Invoice, inv_id)
        path = build_pdf(inv)
        db.session.commit()
        data = open(path, "rb").read()
    assert data[:5] == b"%PDF-"
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    assert GREEK_DUE in text, "the Greek label override was dropped from the PDF"
    assert GREEK_INSTRUCTIONS in text, "the Greek payment instructions were dropped from the PDF"
    assert "?" not in text, "non-Latin text was flattened to question marks"
