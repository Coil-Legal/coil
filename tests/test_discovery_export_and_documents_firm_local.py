"""Coil QA #178: the discovery set "Last export" flash/detail line and the /documents "Uploaded"
column both read Document.created_at (naive UTC, default=now()) with the plain `dt` filter
instead of `dtlocal`, same class as #163/#164/#168/#169/#170/#173/#176.

Run: .venv/bin/python -m pytest tests/test_discovery_export_and_documents_firm_local.py -q
"""
from datetime import datetime

from tests.test_phase1_independent import app, staff  # noqa: F401

# 7:41pm Central (CDT, UTC-5) on Oct 6, 2026 is 00:41 UTC Oct 7.
EVENING_UTC = datetime(2026, 10, 7, 0, 41)


def test_discovery_last_export_and_documents_uploaded_use_firm_local_time(app):
    c, csrf = staff(app)
    with app.app_context():
        from app.models import Matter
        mid = Matter.query.first().id

    r = c.post(f"/discovery/new?matter_id={mid}", data={
        "_csrf": csrf, "direction": "propound", "kind": "interrogatories", "party": "Defendant Holloway",
        "served_on": "2026-08-01"})
    assert r.status_code == 302
    sid = int(r.headers["Location"].rstrip("/").rsplit("/", 1)[1])
    r = c.post(f"/discovery/{sid}/export", data={"_csrf": csrf})
    assert r.status_code == 302

    with app.app_context():
        from app.extensions import db
        from app.models import DiscoverySet, Document

        ds = db.session.get(DiscoverySet, sid)
        doc = db.session.get(Document, ds.output_document_id)
        doc.created_at = EVENING_UTC
        doc_name = doc.name
        db.session.commit()

    detail_body = c.get(f"/discovery/{sid}").data.decode()
    assert "Oct 6, 2026" in detail_body
    assert "Oct 7, 2026" not in detail_body

    docs_body = c.get(f"/documents?matter_id={mid}").data.decode()
    start = docs_body.index(doc_name)
    row = docs_body[start:start + 600]
    assert "Oct 6, 2026" in row
    assert "Oct 7, 2026" not in row
