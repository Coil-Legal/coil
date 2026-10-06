"""Statement PDF summary box heading must not drop text it cannot render.

render_statement_pdf's summary-box heading row (`row.cell(h)`) never went through `_pdf_txt`,
the helper every other label on the page uses to fall back to "?" when the active font lacks a
glyph. DejaVu (the bundled Unicode font) covers Latin, Greek and Cyrillic but not CJK, so a CJK
`balance_due` label override printed as a blank heading cell instead of the "?" fallback every
other field gets. Filed as Coil QA #123 (QA Bot 2).
"""
import io

from pypdf import PdfReader

from tests.test_phase1_independent import app  # noqa: F401

CJK_BALANCE_DUE = "应付余额"


def _statement(app):
    from app.extensions import db
    from app.models import Firm, Matter

    with app.app_context():
        m = Matter.query.filter_by(number="M-PHASE1").first()
        firm = Firm.get()
        firm.invoice_labels_json = '{"balance_due": "%s"}' % CJK_BALANCE_DUE
        db.session.commit()
        return m.client_id


def test_statement_pdf_summary_heading_falls_back_instead_of_dropping_text(app):
    from app.extensions import db
    from app.blueprints.statements import build_statement, render_statement_pdf
    from app.models import Contact

    client_id = _statement(app)
    with app.app_context():
        client = db.session.get(Contact, client_id)
        st = build_statement(client)
        pdf = render_statement_pdf(st)
        data = bytes(pdf.output())
    assert data[:5] == b"%PDF-"
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    heading_line = next(l for l in text.splitlines() if "Invoiced" in l)
    assert "Paid or applied" in heading_line and "Credited" in heading_line
    assert "?" in heading_line, (
        "the fourth heading cell should fall back to '?' like every other unrenderable field, "
        f"not vanish entirely: {heading_line!r}"
    )
