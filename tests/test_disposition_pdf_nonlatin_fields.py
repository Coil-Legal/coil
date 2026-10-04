"""The disposition summary PDF must render a non-Latin prosecutor, case notes or charge text.

build_disposition_pdf only scanned the firm/matter/client caption fields for enable_unicode,
never the prosecutor, judge, court, notes or per-charge statute/description/enhancement/degree/
sentence text actually printed below the caption, so a case with a Greek prosecutor or charge
enhancement and otherwise-Latin names stayed on the core Helvetica font and every non-Latin
glyph came out as "?". Filed as Coil QA #110.
"""
import io
import os

from tests.test_phase6_r import app, client, csrf, _matter_id  # noqa: F401


def test_disposition_pdf_renders_non_latin_prosecutor_notes_and_charge_text(app, client):
    m2 = _matter_id(app, "M-1002")
    tok = csrf(client)
    r = client.post(f"/criminal/{m2}/facts", data={
        "_csrf": tok, "court": "County Court at Law No. 2", "cause_number": "C-2026-1234",
        "prosecutor": "Εισαγγελέας Κωνσταντίνου", "judge": "Judge Park", "stage": "charged",
        "notes": "Υπόθεση δοκιμής"})
    assert r.status_code == 302
    r = client.post(f"/criminal/{m2}/charges/new", data={
        "_csrf": tok, "statute": "PC 49.04", "description": "Driving while intoxicated",
        "degree": "Class B misdemeanor", "enhancement": "Παράβαση κατ' εξακολούθηση",
        "disposition": "pending"})
    assert r.status_code == 302
    r = client.post(f"/criminal/{m2}/disposition-pdf", data={"_csrf": tok})
    assert r.status_code == 302
    with app.app_context():
        from app.models import Document
        doc = Document.query.filter_by(matter_id=m2, folder="Criminal").order_by(Document.id.desc()).first()
        path = os.path.join(app.config["UPLOAD_DIR"], doc.path)
    data = open(path, "rb").read()
    assert data[:5] == b"%PDF-"
    from pypdf import PdfReader
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    assert "Εισαγγελέας Κωνσταντίνου" in text
    assert "Υπόθεση δοκιμής" in text
    assert "Παράβαση κατ'" in text and "εξακολούθηση" in text  # charge table wraps the cell onto two lines
    assert "?" not in text  # no stray question marks standing in for glyphs
