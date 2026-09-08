#!/usr/bin/env python3
"""Regenerate the binary sample documents from the plain text ones.

The .pdf and .docx files are committed, so nobody needs to run this to use the samples.
It exists because a firm's real documents arrive as PDFs and Word files, not .txt, and
Coil extracts text from each format by a different route: pypdf for PDF, a raw XML read
of the zip for DOCX, a straight decode for text. A sample set that is all .txt exercises
one of those three and quietly leaves the other two untested.

    python samples/build.py
"""
import csv
from pathlib import Path

HERE = Path(__file__).parent


def build_pdf():
    from fpdf import FPDF
    src = (HERE / "medical-records-demo.txt").read_text()
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=9)
    # Explicit width and a reset x each line: with w=0 fpdf uses the remaining width,
    # which becomes zero once the cursor has drifted to the right margin, and it then
    # raises "not enough horizontal space" rather than wrapping.
    width = pdf.w - pdf.l_margin - pdf.r_margin
    for line in src.splitlines():
        pdf.set_x(pdf.l_margin)
        # fpdf's core fonts are latin-1; the samples are plain ASCII, but be safe.
        pdf.multi_cell(width, 4.4, line.encode("latin-1", "replace").decode("latin-1") or " ")
    out = HERE / "medical-records-demo.pdf"
    pdf.output(str(out))
    return out


def build_docx():
    from docx import Document as Docx
    src = (HERE / "contract-demo.txt").read_text()
    d = Docx()
    for line in src.splitlines():
        d.add_paragraph(line)
    out = HERE / "contract-demo.docx"
    d.save(str(out))
    return out


def build_csv():
    """A provider billing ledger, the shape a firm actually receives from a lien service."""
    out = HERE / "provider-billing-demo.csv"
    rows = [
        ("date", "provider", "description", "billed", "paid", "balance"),
        ("2026-02-11", "Cedar Hollow Emergency Center", "ED visit, imaging", "8412.00", "0.00", "8412.00"),
        ("2026-02-19", "Whitfield Family Medicine", "Office visit", "310.00", "310.00", "0.00"),
        ("2026-03-04", "Lakeshore Physical Therapy", "PT evaluation", "425.00", "425.00", "0.00"),
        ("2026-03-11", "Lakeshore Physical Therapy", "PT, 6 sessions", "1275.00", "900.00", "375.00"),
        ("2026-04-02", "Whitfield Family Medicine", "Office visit, MRI referral", "630.00", "0.00", "630.00"),
        ("2026-04-15", "Northgate Imaging", "MRI cervical spine", "2150.00", "0.00", "2150.00"),
        ("2026-05-06", "Northgate Orthopaedics", "Consultation", "780.00", "0.00", "780.00"),
        ("2026-05-28", "Northgate Orthopaedics", "ESI, right C5-C6", "5300.00", "0.00", "5300.00"),
        ("2026-07-09", "Northgate Orthopaedics", "Follow-up", "750.00", "0.00", "750.00"),
        ("2026-03-25", "Lakeshore Physical Therapy", "PT, 12 sessions", "2575.00", "2575.00", "0.00"),
    ]
    with out.open("w", newline="") as f:
        csv.writer(f).writerows(rows)
    return out


def build_eml():
    """For testing email filing to a matter. Plain RFC 822, no attachments."""
    out = HERE / "client-email-demo.eml"
    out.write_text(
        "From: Rosalind Marchetti <rosalind@example.test>\n"
        "To: Demo Owner <owner@example.test>\n"
        "Subject: Re: demand letter to Continental Mutual\n"
        "Date: Mon, 8 Sep 2026 09:41:02 -0500\n"
        "Message-ID: <demo-8f21c4@example.test>\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        "SYNTHETIC TEST DATA. Invented sender and facts.\n"
        "\n"
        "Thanks for sending the draft. Two things.\n"
        "\n"
        "The adjuster called again on Friday and left a voicemail. I did not call back.\n"
        "She mentioned a figure but I did not write it down.\n"
        "\n"
        "Also, I went back to work on light duty three weeks ago, not four. I checked my\n"
        "roster. Sorry, I got that wrong when we spoke.\n"
        "\n"
        "Rosalind\n"
    )
    return out


if __name__ == "__main__":
    for fn in (build_pdf, build_docx, build_csv, build_eml):
        p = fn()
        print(f"  wrote {p.name} ({p.stat().st_size} bytes)")
