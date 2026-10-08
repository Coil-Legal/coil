"""Coil QA #180: store_bytes() saved Document.name as a tail-truncated name[:300], so a
discovery (or deposition-summary) export whose title makes the generated filename
("{title} {date}.pdf") longer than 300 chars lost its date and its .pdf extension on both the
stored document and the download's Content-Disposition, while the flash and the set's "Last
export" line still claimed the full, untruncated name.

Run: .venv/bin/python -m pytest tests/test_discovery_export_long_title_filename.py -q
"""
from app.blueprints.documents import _fit_stored_name
from tests.test_phase1_independent import app, staff  # noqa: F401


def test_fit_stored_name_keeps_extension_when_cutting():
    long_title = "Q" * 300
    name = f"{long_title} 2026-10-07.pdf"
    assert len(name) > 300
    fitted = _fit_stored_name(name)
    assert len(fitted) <= 300
    assert fitted.endswith(" 2026-10-07.pdf") or fitted.endswith(".pdf")
    assert fitted.rsplit(".", 1)[-1] == "pdf"


def test_fit_stored_name_leaves_short_names_alone():
    assert _fit_stored_name("short.pdf") == "short.pdf"


def test_discovery_export_with_long_title_keeps_date_and_extension(app):
    c, csrf = staff(app)
    with app.app_context():
        from app.models import Matter
        mid = Matter.query.first().id

    r = c.post(f"/discovery/new?matter_id={mid}", data={
        "_csrf": csrf, "direction": "propound", "kind": "interrogatories", "party": "Defendant Holloway",
        "served_on": "2026-08-01"})
    assert r.status_code == 302
    sid = int(r.headers["Location"].rstrip("/").rsplit("/", 1)[1])

    with app.app_context():
        from app.extensions import db
        from app.models import DiscoverySet

        ds = db.session.get(DiscoverySet, sid)
        ds.title = "Q" * 300
        db.session.commit()

    r = c.post(f"/discovery/{sid}/export", data={"_csrf": csrf})
    assert r.status_code == 302

    with app.app_context():
        from app.models import DiscoverySet, Document

        ds = db.session.get(DiscoverySet, sid)
        doc = db.session.get(Document, ds.output_document_id)
        assert len(doc.name) <= 300
        assert doc.name.endswith(".pdf"), "the export must keep a .pdf extension even when the title is cut"

    detail_body = c.get(f"/discovery/{sid}").data.decode()
    assert ".pdf" in detail_body[detail_body.index("Last export"):detail_body.index("Last export") + 400]

    docs_body = c.get(f"/documents?matter_id={mid}").data.decode()
    assert doc.name in docs_body
