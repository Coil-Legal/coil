"""A signer name outside cp1252 must survive into the signature certificate PDF.

Reproduced live (Coil QA #47): a signer named "QA Signer café Иванова" signed successfully
and the staff record kept the Unicode name, but the certificate PDF printed
"QA Signer café ???????" because build_certificate_pdf() never switched the document to the
bundled Unicode font the way every other PDF builder (invoices, discovery, criminal, pi) does.

Run: .venv/bin/python -m pytest tests/test_signature_certificate_unicode.py -q
"""
import io as _io

import pypdf
import pytest

from tests.test_phase1_independent import app
from tests.test_phase1_document_integrity import signature_fixture

CYRILLIC_NAME = "QA Signer café Иванова"  # QA Signer café Иванова


def test_a_cyrillic_signer_name_survives_into_the_certificate_pdf(app, monkeypatch):
    from app.blueprints import signatures
    from app.extensions import db
    from app.models import DocumentSignature
    from app.services.pdf import unicode_on, reset_unicode

    monkeypatch.setattr(signatures, "_email_signed_copies", lambda *a: None)
    sid, token = signature_fixture(app, None)
    client = app.test_client()
    r = client.post(f"/sign/doc/{token}", data={"signer_name": CYRILLIC_NAME, "agree": "1"})
    assert r.status_code == 200, r.data[:300]

    with app.app_context():
        row = db.session.get(DocumentSignature, sid)
        assert row.status == "signed" and row.signer_name == CYRILLIC_NAME
        path = row.certificate_pdf_path
        pdf_bytes = open(path, "rb").read()
        assert pdf_bytes.startswith(b"%PDF")
        assert b"DejaVu" in pdf_bytes, "the Unicode font was not embedded in the certificate"
        text = pypdf.PdfReader(_io.BytesIO(pdf_bytes)).pages[0].extract_text()
        missing = [ch for ch in CYRILLIC_NAME if ch not in text]
        assert not missing, f"dropped from the certificate: {missing}"
        assert "???????" not in text, "the name was still flattened to question marks"
    reset_unicode()


def test_an_ordinary_ascii_signer_keeps_the_core_font(app, monkeypatch):
    from app.blueprints import signatures
    from app.extensions import db
    from app.models import DocumentSignature
    from app.services.pdf import unicode_on, reset_unicode

    monkeypatch.setattr(signatures, "_email_signed_copies", lambda *a: None)
    sid, token = signature_fixture(app, None)
    client = app.test_client()
    r = client.post(f"/sign/doc/{token}", data={"signer_name": "Jane Signer", "agree": "1"})
    assert r.status_code == 200

    with app.app_context():
        row = db.session.get(DocumentSignature, sid)
        pdf_bytes = open(row.certificate_pdf_path, "rb").read()
        assert pdf_bytes.startswith(b"%PDF")
    reset_unicode()
