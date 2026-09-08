# Sample documents

Fake files for trying Coil out, and for checking that a tool does what it claims before
you point it at a real matter.

**Everything here is invented.** The people, companies, doctors, courts, case numbers and
citations do not exist. Every file says so on its first line. Nothing here is legal
advice or a usable template, and the citations are deliberately fictional so a cite
checker has something to fail on.

Load them with `python demo_data.py`, which builds a small fake practice and files these
against the right matters. Or upload one by hand from any matter's Documents tab.

| File | Try it with |
|---|---|
| `medical-records-demo.txt` | Personal injury, Records to chronology |
| `deposition-excerpt-demo.txt` | Depositions: transcript in, summary and page-line out |
| `brief-with-citations-demo.txt` | Cite check (two citations do not resolve, on purpose) |
| `contract-demo.txt` | Documents, full-text search, conflict check |
| `settlement-demand-demo.txt` | Demand drafting, PI settlement worksheet |
| `intake-notes-demo.txt` | Intake, matter notes, the AI assistant |
| `medical-records-demo.pdf` | The same records as a PDF, so the pypdf path gets used |
| `contract-demo.docx` | The same contract as Word, so the DOCX path gets used |
| `provider-billing-demo.csv` | Lien and billing ledgers, CSV import |
| `client-email-demo.eml` | Filing an email to a matter |

The binary files are committed, so you do not need to build anything. `python
samples/build.py` regenerates them from the text versions if you change those. The mix of
formats is on purpose: Coil reads PDF, Word and plain text by three different routes, and
a sample set that is all `.txt` only ever exercises one of them.
