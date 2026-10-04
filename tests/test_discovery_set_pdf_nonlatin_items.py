"""The discovery set PDF must render non-Latin request/response/flag text on its items.

build_set_pdf only scanned the firm/matter/client/party caption fields for enable_unicode,
never each item's request, response or flag text actually printed in the body, so a set with
otherwise-Latin party/matter names but a non-Latin interrogatory or answer stayed on the core
Helvetica font and every non-Latin glyph came out as "?". Flagged alongside Coil QA #110 as the
same gap in a second PDF builder.
"""
import io

from tests.test_phase5_m import app, client, S  # noqa: F401


def test_discovery_set_pdf_renders_non_latin_item_text(app, client):
    r = client.post(f"/discovery/new?matter_id={S['mid']}", data={
        "_csrf": S["tok"], "direction": "propound", "kind": "interrogatories", "party": "Defendant Holloway",
        "served_on": "2026-08-01"})
    assert r.status_code == 302
    sid = int(r.headers["Location"].rstrip("/").rsplit("/", 1)[1])
    r = client.post(f"/discovery/{sid}/save", data={
        "_csrf": S["tok"], "title": "Rogs to Holloway", "party": "Defendant Holloway",
        "served_on": "2026-08-01", "due_on": "", "status": "draft", "item_n": ["1"],
        "item_1_request": "Περιγράψτε κάθε μάρτυρα του ατυχήματος.",
        "item_1_response": "Απάντηση δοκιμής 20261004", "item_1_flag": ""})
    assert r.status_code == 302
    r = client.post(f"/discovery/{sid}/export", data={"_csrf": S["tok"]})
    assert r.status_code == 302
    with app.app_context():
        from app.models import DiscoverySet, Document
        ds = DiscoverySet.query.get(sid)
        doc = Document.query.get(ds.output_document_id)
        import os
        path = os.path.join(app.config["UPLOAD_DIR"], doc.path)
    data = open(path, "rb").read()
    assert data[:5] == b"%PDF-"
    from pypdf import PdfReader
    text = PdfReader(io.BytesIO(data)).pages[0].extract_text()
    assert "Περιγράψτε κάθε μάρτυρα του ατυχήματος." in text
    assert "Απάντηση δοκιμής 20261004" in text
    assert "?" not in text  # no stray question marks standing in for glyphs
