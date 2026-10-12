"""Complete firm export for offboarding (gate C08), and the check that proves it is usable.

A departing firm gets one zip holding everything Coil knows about it:

  README.txt                      plain-English guide for the firm
  manifest.json                   what is inside, with a sha256 for every file
  database/practice.db            SQLite online-backup snapshot, the complete record
  csv/<table>.csv                 every table, for Excel, minus secret-bearing columns
  customizations/customizations.json   firm settings, templates, tool switches, appearance
  documents/files/...             every stored file a record points to (uploads layout)
  documents/unlinked/...          files found in storage that no record points to
  documents/index.csv             which record each stored file belongs to
  pdf/...                         generated PDFs

`python -m app.cli export_firm [--out DIR] [--slug SLUG]` builds one (see export_firm_cli).
`python -m app.cli verify_export <zip>` checks one.

The verifier must run on a host that has no Flask and no Coil install, because
ops/export-firm.sh checks the copy it took with the host's python3:

    python3 -I app/firm_export.py verify <zip>

So this module imports only the standard library at the top. Everything that needs the app
is imported inside the functions that build an export, and the schema helpers are loaded
from the neighbouring backup_manifest.py by path when this file runs on its own.
"""
import csv
import fcntl
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:  # imported as app.firm_export
    from .backup_manifest import database_schema, schema_fingerprint
except ImportError:  # run as a file on a host without the app package
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("coil_backup_manifest", Path(__file__).with_name("backup_manifest.py"))
    _bm = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_bm)
    database_schema, schema_fingerprint = _bm.database_schema, _bm.schema_fingerprint

FORMAT = "coil-firm-export"
FORMAT_VERSION = 1
PREFIX = "coil-export-"
MANIFEST = "manifest.json"
README = "README.txt"
DB_MEMBER = "database/practice.db"
CUSTOMIZATIONS = "customizations/customizations.json"
DOC_INDEX = "documents/index.csv"
CHUNK = 1024 * 1024

# Columns that hold a credential, a secret or a bearer link. Left out of the CSVs and of
# customizations.json. The database snapshot keeps them, because it is the complete record
# and restoring it must give back a working Coil (README says so plainly).
SECRET_COLUMNS = {
    ("users", "password_hash"): "sign-in password hash",
    ("users", "voice_pin_hash"): "voice line PIN hash",
    ("users", "session_version"): "sign-in session counter",
    ("firm", "install_key"): "Coil install key",
    ("firm", "courtlistener_token"): "CourtListener API token",
    ("firm", "ai_api_key"): "AI provider API key",
    ("firm", "integration_json"): "saved integration credentials (Stripe, Twilio, email and others)",
    ("api_tokens", "token_hash"): "API token hash",
    ("oauth_clients", "client_secret_hash"): "connected app secret hash",
    ("oauth_codes", "code_hash"): "connected app authorization code hash",
    ("oauth_refresh_tokens", "token_hash"): "connected app refresh token hash",
    ("webhooks", "secret"): "webhook signing secret",
    ("portal_tokens", "token"): "client portal sign-in link",
    ("invoices", "public_token"): "client invoice and payment link",
    ("engagements", "token"): "engagement letter signing link",
    ("document_signatures", "token"): "document signing link",
    ("bookings", "token"): "booking manage and cancel link",
    ("questionnaire_responses", "token"): "questionnaire link",
}

# Safety net for columns added after this list was written: anything whose name looks like
# a secret is left out of the CSVs unless it is on the allowlist below.
SECRET_PATTERN = re.compile(r"token|secret|password|passwd|credential|hash|key", re.IGNORECASE)

# Names that match the pattern but hold ordinary records. Each one was checked.
NOT_SECRET = {
    ("engagements", "document_hash"): "fingerprint of the signed letter, part of the signing record",
    ("engagements", "signature_hash"): "fingerprint of the signature, part of the signing record",
    ("document_signatures", "document_hash"): "fingerprint of the signed file, part of the signing record",
    ("document_signatures", "signature_hash"): "fingerprint of the signature, part of the signing record",
    ("card_charge_attempts", "idempotency_key"): "Stripe retry key, not a credential",
    ("deposition_summaries", "key_testimony_json"): "testimony excerpts",
    ("oauth_clients", "token_endpoint_auth_method"): "name of a sign-in method",
    ("oauth_refresh_tokens", "access_token_id"): "row id",
}

# Columns that point at a stored file under the uploads folder, besides documents.path.
FILE_REFERENCES = [
    ("expenses", "receipt_path", "expense_receipt"),
    ("doc_templates", "path", "document_template"),
    ("firm", "invoice_logo_path", "invoice_logo"),
]

INDEX_COLUMNS = ["archive_path", "status", "record_type", "record_id", "document_id", "original_filename",
                 "matter_number", "matter_name", "contact", "uploaded_on", "size_bytes", "sha256",
                 "stored_path", "note"]

# What customizations.json holds, in order: (table, key, what it is).
CUSTOMIZATION_TABLES = [
    ("offices", "offices", "Office locations. Users and matters can belong to one."),
    ("users", "users", "Everyone who can sign in, with role, rates and dashboard choices. No passwords."),
    ("matter_templates", "matter_templates", "Matter templates: billing defaults, milestones, tasks and custom fields applied to new matters."),
    ("stage_sets", "matter_stages", "Matter stage lists per practice area."),
    ("letter_templates", "letter_templates", "Engagement, declination and general letter templates with merge fields."),
    ("doc_templates", "document_templates", "Document templates. Uploaded .docx files are under documents/files/templates/."),
    ("questionnaires", "questionnaires", "Client questionnaires and their questions."),
    ("follow_up_sequences", "follow_up_sequences", "Intake follow-up sequences and their steps."),
    ("booking_types", "booking_types", "Online booking types and availability."),
    ("court_rule_sets", "court_rule_sets", "Court rule sets used to calculate deadlines."),
    ("court_rules", "court_rules", "Individual court rules inside each set."),
    ("holidays", "holidays", "Court holidays skipped by deadline calculations."),
    ("accounts", "chart_of_accounts", "The firm books chart of accounts."),
    ("webhooks", "webhooks", "Outgoing webhooks. Signing secrets are left out."),
    ("firm_customization", "appearance_and_workflows", "Published appearance, navigation labels and new-matter rules."),
    ("customization_revisions", "appearance_history", "Every published revision of appearance and workflows."),
]

INVOICE_TEMPLATE_FIELDS = ("invoice_logo_path", "invoice_accent", "invoice_title", "invoice_columns_json",
                           "invoice_labels_json", "invoice_show_timekeeper", "invoice_show_activity_codes",
                           "invoice_payment_instructions", "invoice_footer", "statement_footer", "invoice_prefix",
                           "next_invoice_number", "invoice_terms_days", "monthly_billing_day", "monthly_billing_send",
                           "surcharge_enabled", "surcharge_bps", "credit_note_prefix", "next_credit_note_number")

_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\.\d+)?$")
_SLUG = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,58}[a-z0-9])?$")


class ExportError(Exception):
    """An export could not be built. The message is meant for the person who asked."""


class ExportBusy(ExportError):
    """Another export is being built for this firm right now."""


# ---------------------------------------------------------------------------
# which columns leave the CSVs
# ---------------------------------------------------------------------------
def excluded_reason(table, column):
    """Why a column is left out of the CSVs and customizations.json, or None to keep it."""
    reason = SECRET_COLUMNS.get((table, column))
    if reason:
        return reason
    if (table, column) in NOT_SECRET:
        return None
    if SECRET_PATTERN.search(column):
        return "name looks like a secret (safety net)"
    return None


def split_columns(table, columns):
    """(kept columns, [{table, column, reason}]) for one table, columns in their given order."""
    kept, excluded = [], []
    for c in columns:
        why = excluded_reason(table, c)
        if why:
            excluded.append({"table": table, "column": c, "reason": why})
        else:
            kept.append(c)
    return kept, excluded


def _q(name):
    return '"' + name.replace('"', '""') + '"'


def _table_columns(conn, table):
    """[(name, declared type)] in table order."""
    return [(r[1], (r[2] or "").upper()) for r in conn.execute(f"PRAGMA table_info({_q(table)})")]


def _tables(conn):
    return sorted(r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"))


def _count(conn, table):
    return int(conn.execute(f"SELECT COUNT(*) FROM {_q(table)}").fetchone()[0])


# ---------------------------------------------------------------------------
# zip writing with a running sha256
# ---------------------------------------------------------------------------
class _Hashing(io.RawIOBase):
    """Write-through wrapper that hashes and counts what goes into a zip member."""

    def __init__(self, raw):
        self.raw, self.sha, self.size = raw, hashlib.sha256(), 0

    def writable(self):
        return True

    def write(self, b):
        b = bytes(b)
        self.sha.update(b)
        self.size += len(b)
        self.raw.write(b)
        return len(b)

    def close(self):
        if not self.closed:
            self.raw.close()
        super().close()


class _Writer:
    def __init__(self, zf):
        self.zf, self.files, self.names = zf, [], set()

    @contextmanager
    def member(self, name):
        if name in self.names:
            raise ExportError(f"duplicate archive path {name}")
        self.names.add(name)
        info = zipfile.ZipInfo(name, date_time=datetime.now(timezone.utc).timetuple()[:6])
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o600 << 16
        h = _Hashing(self.zf.open(info, "w", force_zip64=True))
        try:
            yield h
        finally:
            h.close()
        self.files.append({"path": name, "size": h.size, "sha256": h.sha.hexdigest()})

    def text(self, name, text):
        with self.member(name) as h:
            h.write(text.encode("utf-8"))

    def file(self, name, src):
        with self.member(name) as h, open(src, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK), b""):
                h.write(chunk)
        return self.files[-1]

    @contextmanager
    def csv(self, name):
        with self.member(name) as h:
            text = io.TextIOWrapper(h, encoding="utf-8", newline="", write_through=True)
            text.write("﻿")  # BOM: Excel opens UTF-8 CSVs as ANSI without one
            try:
                yield csv.writer(text)
            finally:
                text.flush()
                text.detach()


def _arc_safe(path):
    """A zip member name that encodes, for file names that are not valid UTF-8 on disk."""
    try:
        path.encode("utf-8")
        return path
    except UnicodeEncodeError:
        return path.encode("utf-8", "backslashreplace").decode("ascii")


# ---------------------------------------------------------------------------
# workspace: private, reclaimable, never shared between runs
# ---------------------------------------------------------------------------
@contextmanager
def _workspace(out_dir):
    """A private job directory inside out_dir, held by a lease until cleanup.

    Same pattern as cli._backup_workspace: the registry lock covers creation and deletion,
    and only workspaces whose lease nobody holds (a crashed run) are reclaimed. The job
    lives inside out_dir so the finished zip can be published with a hard link.
    """
    job = lease = None
    with (out_dir / ".coil-export-registry.lock").open("a+b") as registry:
        try:
            fcntl.flock(registry, fcntl.LOCK_EX)
            try:
                for old in out_dir.glob(".coil-export-job-*"):
                    if old.is_symlink() or not old.is_dir():
                        continue
                    with (old / "lease").open("a+b") as candidate:
                        try:
                            fcntl.flock(candidate, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        except BlockingIOError:
                            continue
                        shutil.rmtree(old)
                job = Path(tempfile.mkdtemp(prefix=".coil-export-job-", dir=out_dir))
                lease = (job / "lease").open("a+b")
                fcntl.flock(lease, fcntl.LOCK_EX)
            finally:
                fcntl.flock(registry, fcntl.LOCK_UN)
            yield job
        finally:
            try:
                if job is not None:
                    fcntl.flock(registry, fcntl.LOCK_EX)
                    try:
                        shutil.rmtree(job, ignore_errors=True)
                    finally:
                        fcntl.flock(registry, fcntl.LOCK_UN)
            finally:
                if lease is not None:
                    lease.close()


@contextmanager
def build_lock(out_dir):
    """Refuse a second export while one is running (the Download button, clicked twice)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / ".coil-export-build.lock").open("a+b") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ExportBusy("An export is already being built. It finishes on its own; try again in a few minutes.")
        try:
            yield
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def _snapshot(db_path, dest):
    """SQLite online backup, the same method backup() uses, so a live writer cannot tear it.

    The copy is switched to a rollback journal so it opens on its own in any SQLite tool;
    Coil switches it back to WAL the first time it connects after a restore.
    """
    src = sqlite3.connect(str(db_path))
    try:
        dst = sqlite3.connect(str(dest))
        try:
            src.backup(dst)
            dst.execute("PRAGMA journal_mode=DELETE")
        finally:
            dst.close()
    finally:
        src.close()


# ---------------------------------------------------------------------------
# customizations.json
# ---------------------------------------------------------------------------
def _decode_json_fields(row):
    out = {}
    for k, v in row.items():
        if k.endswith("_json") and isinstance(v, str):
            try:
                out[k[:-5]] = json.loads(v or "null")
                continue
            except ValueError:
                pass
        out[k] = v
    return out


def _rows(conn, table, order="id"):
    cols = [c for c, _ in _table_columns(conn, table)]
    kept, _ = split_columns(table, cols)
    if not kept:
        return []
    order_sql = f" ORDER BY {_q(order)}" if order in cols else ""
    cur = conn.execute(f"SELECT {', '.join(_q(c) for c in kept)} FROM {_q(table)}{order_sql}")
    return [_decode_json_fields(dict(zip(kept, r))) for r in cur]


def _custom_field_names(conn, table):
    names = {}
    if table not in _tables(conn):
        return names
    for (raw,) in conn.execute(f"SELECT custom_fields_json FROM {_q(table)}"):
        try:
            d = json.loads(raw or "{}")
        except ValueError:
            continue
        if isinstance(d, dict):
            for k in d:
                names[k] = names.get(k, 0) + 1
    return dict(sorted(names.items()))


def build_customizations(conn, tools=None):
    """The firm's configuration as a readable, documented dict. No secrets."""
    tables = set(_tables(conn))
    firm = {}
    if "firm" in tables:
        rows = _rows(conn, "firm")
        firm = rows[0] if rows else {}
    integration_names = []
    if "firm" in tables and "integration_json" in [c for c, _ in _table_columns(conn, "firm")]:
        raw = conn.execute("SELECT integration_json FROM firm ORDER BY id LIMIT 1").fetchone()
        try:
            saved = json.loads(raw[0] or "{}") if raw else {}
        except ValueError:
            saved = {}
        if isinstance(saved, dict):
            integration_names = sorted(k for k, v in saved.items() if v)
    invoice_template = {}
    for k in INVOICE_TEMPLATE_FIELDS:
        dk = k[:-5] if k.endswith("_json") else k
        if dk in firm:
            invoice_template[dk] = firm[dk]
    out = {
        "_about": ("Firm settings and customizations from Coil, read from the database in this export. "
                   "Sign-in credentials, API keys, webhook secrets and client links are left out. "
                   "Every list below is also a table in the csv folder, and database/practice.db holds all of it."),
        "firm_settings": {
            "_about": "Everything on Settings and Settings > Invoice template, except stored keys.",
            "values": firm,
            "integration_credentials_saved": integration_names,
            "_integration_note": ("Names of the integration credentials saved in Settings. The values are left out. "
                                  "They are in database/practice.db; revoke or rotate them with each provider."),
        },
        "invoice_template": {
            "_about": "The invoice and statement layout, numbering and payment settings, from the firm settings above.",
            "values": invoice_template,
        },
        "tools": {
            "_about": "Which tools are switched on (Settings > Tools). overrides holds only what differs from the default.",
            "overrides": firm.get("tool_overrides", {}) if isinstance(firm.get("tool_overrides"), dict) else
            _loads(firm.get("tool_overrides")),
            "effective": tools or {},
        },
        "custom_fields": {
            "_about": "Custom field names in use and how many records carry each. The values are in the csv files.",
            "contacts": _custom_field_names(conn, "contacts"),
            "matters": _custom_field_names(conn, "matters"),
        },
    }
    for table, key, about in CUSTOMIZATION_TABLES:
        if table in tables:
            out[key] = {"_about": about, "rows": _rows(conn, table)}
    return out


def _loads(raw):
    try:
        v = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return v if isinstance(v, dict) else {}


# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------
def _contact_name(kind, first, last, company):
    if kind == "company":
        return company or ""
    n = f"{first or ''} {last or ''}".strip()
    return n or company or ""


def _resolve(stored, upload_root):
    """(relative path under uploads, None) or (None, reason) for a stored path."""
    if not stored:
        return None, "no file path recorded"
    full = stored if os.path.isabs(stored) else os.path.join(str(upload_root), stored)
    real = os.path.realpath(full)
    root = os.path.realpath(str(upload_root))
    if real != root and not real.startswith(root + os.sep):
        return None, "stored path is outside the uploads folder"
    if not os.path.isfile(real):
        return None, "file not found in storage"
    return os.path.relpath(real, root).replace(os.sep, "/"), None


def _document_rows(conn, tables):
    if "documents" not in tables:
        return []
    have = {c for c, _ in _table_columns(conn, "documents")}
    if not {"id", "path"} <= have:
        return []
    matter = "matters" in tables
    contact = matter and "contacts" in tables
    sql = ("SELECT d.id, d.path, " + ("d.name" if "name" in have else "''") + ", "
           + ("d.created_at" if "created_at" in have else "''") + ", "
           + ("m.number, m.name" if matter else "'', ''") + ", "
           + ("c.kind, c.first_name, c.last_name, c.company_name" if contact else "'', '', '', ''")
           + " FROM documents d"
           + (" LEFT JOIN matters m ON m.id = d.matter_id" if matter and "matter_id" in have else "")
           + (" LEFT JOIN contacts c ON c.id = m.client_id" if contact and "matter_id" in have else "")
           + " ORDER BY d.id")
    return conn.execute(sql).fetchall()


def _write_documents(w, conn, upload_dir):
    """Add every stored file, write documents/index.csv, and return the documents summary."""
    tables = set(_tables(conn))
    upload_root = Path(upload_dir) if upload_dir else None
    index, missing, unlinked, skipped = [], [], [], []
    linked = {}  # relative path -> file entry

    def include(rel, src):
        if rel not in linked:
            linked[rel] = w.file(_arc_safe("documents/files/" + rel), src)
        return linked[rel]

    def add(record_type, record_id, stored, doc=None):
        doc = doc or {}
        rel, why = _resolve(stored, upload_root) if upload_root else (None, "no uploads folder")
        row = {"record_type": record_type, "record_id": record_id, "stored_path": stored or "", **doc}
        if rel is None:
            row.update(status="missing", archive_path="", note=why)
            missing.append({"record_type": record_type, "record_id": record_id, "stored_path": stored or "",
                            "reason": why})
        else:
            entry = include(rel, os.path.join(str(upload_root), rel))
            row.update(status="included", archive_path=entry["path"], size_bytes=entry["size"],
                       sha256=entry["sha256"])
        index.append(row)

    for (did, path, name, created, mnum, mname, kind, first, last, company) in _document_rows(conn, tables):
        add("document", did, path, {
            "document_id": did, "original_filename": name or "", "matter_number": mnum or "",
            "matter_name": mname or "", "contact": _contact_name(kind, first, last, company),
            "uploaded_on": _iso(created) or ""})
    for table, column, record_type in FILE_REFERENCES:
        if table not in tables or column not in {c for c, _ in _table_columns(conn, table)}:
            continue
        for rid, stored in conn.execute(f"SELECT id, {_q(column)} FROM {_q(table)} WHERE {_q(column)} != '' "
                                        f"AND {_q(column)} IS NOT NULL ORDER BY id"):
            add(record_type, rid, stored)

    if upload_root and upload_root.is_dir():
        root = os.path.realpath(str(upload_root))
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for d in list(dirnames):
                if os.path.islink(os.path.join(dirpath, d)):
                    dirnames.remove(d)
                    skipped.append({"stored_path": os.path.relpath(os.path.join(dirpath, d), root),
                                    "reason": "symbolic link, not followed"})
            for fn in sorted(filenames):
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, root).replace(os.sep, "/")
                if rel in linked:
                    continue
                if os.path.islink(full) or not os.path.isfile(full):
                    skipped.append({"stored_path": rel, "reason": "not a regular file, not copied"})
                    continue
                entry = w.file(_arc_safe("documents/unlinked/" + rel), full)
                unlinked.append({"stored_path": rel, "archive_path": entry["path"], "sha256": entry["sha256"],
                                 "size": entry["size"]})
                index.append({"archive_path": entry["path"], "status": "unlinked", "record_type": "",
                              "stored_path": rel, "size_bytes": entry["size"], "sha256": entry["sha256"],
                              "note": "found in storage with no record pointing to it"})

    with w.csv(DOC_INDEX) as out:
        out.writerow(INDEX_COLUMNS)
        for row in index:
            out.writerow([_cell(row.get(c, "")) for c in INDEX_COLUMNS])
    return {"index_rows": len(index), "included_files": len(linked), "missing": missing, "unlinked": unlinked,
            "skipped": skipped,
            "document_rows": sum(1 for r in index if r["record_type"] == "document")}


# ---------------------------------------------------------------------------
# table CSVs
# ---------------------------------------------------------------------------
def _iso(v):
    if isinstance(v, str) and _DATETIME.match(v):
        return v.replace(" ", "T", 1)
    return v


def _cell(v):
    """One CSV cell: ISO timestamps, and a formula hiding in text cannot run in Excel."""
    if v is None:
        return ""
    if isinstance(v, bytes):
        return "hex:" + v.hex()
    if isinstance(v, str):
        v = _iso(v)
        if v and v[0] in "=+@-\t\r":
            try:
                float(v)
            except ValueError:
                return "'" + v
    return v


def _write_tables(w, conn):
    tables, excluded = {}, []
    for table in _tables(conn):
        cols = _table_columns(conn, table)
        kept, ex = split_columns(table, [c for c, _ in cols])
        excluded.extend(ex)
        name = f"csv/{table}.csv"
        n = 0
        with w.csv(name) as out:
            out.writerow(kept)
            if kept:
                order = " ORDER BY rowid" if _has_rowid(conn, table) else ""
                for r in conn.execute(f"SELECT {', '.join(_q(c) for c in kept)} FROM {_q(table)}{order}"):
                    out.writerow([_cell(v) for v in r])
                    n += 1
            else:
                n = _count(conn, table)
                for _ in range(n):
                    out.writerow([])
        tables[table] = {"rows": _count(conn, table), "csv": name, "csv_rows": n, "columns": kept,
                         "excluded_columns": [e["column"] for e in ex]}
    return tables, excluded


def _has_rowid(conn, table):
    try:
        conn.execute(f"SELECT rowid FROM {_q(table)} LIMIT 0")
        return True
    except sqlite3.OperationalError:
        return False


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------
def readme_text(firm_name, created_at, version, commit, summary):
    return f"""Coil export for {firm_name}
Made {created_at} (UTC) by Coil {version} (commit {commit}).

This file is everything your firm kept in Coil: every record, every uploaded document
and your settings. Keep it somewhere safe. It holds confidential client information.

WHAT IS IN EACH FOLDER

csv/
  One spreadsheet per table in the database, for example contacts.csv, matters.csv,
  time_entries.csv, invoices.csv and trust_transactions.csv. The first row of each file
  names the columns. Records point at each other by id: the client_id column in
  matters.csv is the id of a row in contacts.csv.

database/practice.db
  The complete database, exactly as Coil stores it. This is the full record. The csv
  files are copies of it made for reading.

documents/
  files/      Every file a record points to: matter documents, expense receipts,
              document templates and the invoice logo. The folders match how Coil
              stored them, so files/12/ holds the documents of the matter with id 12.
  unlinked/   Files that were in Coil's storage with no record pointing to them, such
              as import files and email attachments that were never filed. They are
              included so nothing is left behind.
  index.csv   One row per stored file: the record it belongs to, the document id, the
              original file name, the matter number and name, the client, the upload
              date and a sha256 fingerprint. A row marked missing is a record whose file
              was not in storage when this export was made.

customizations/customizations.json
  Your settings and customizations in one readable file: firm settings, the invoice
  template, which tools were switched on, matter templates, letter and document
  templates, court rules, custom field names, appearance and navigation choices, and
  the history of those choices. Any text editor opens it.

pdf/
  PDFs Coil generated, such as invoices, signed engagement letters and certificates.

manifest.json
  A list of every file in this export with its size and sha256 fingerprint, the number
  of rows in each table, and the columns left out of the csv files. Use it to check that
  nothing is missing or changed.

OPENING THE CSV FILES IN EXCEL

Double-click a csv file to open it. The files are saved as UTF-8 with a marker that
tells Excel so, which keeps accented names like Jose Nunez with their accents. If the
accents still look wrong, open a blank workbook, choose Data, then From Text/CSV, pick
the file and set File origin to 65001: Unicode (UTF-8).

Money is stored in cents, as whole numbers, so the amount columns (their names end in
_cents) read 12500 for $125.00. Divide by 100 for dollars. Dates read YYYY-MM-DD and times
read YYYY-MM-DDTHH:MM:SS in UTC. Yes and no columns read 1 for yes and 0 for no.

A text cell that starts with =, +, - or @ has an apostrophe added in front so Excel shows
it instead of running it as a formula. The database file keeps the original text.

WHAT IS LEFT OUT OF THE CSV FILES

Sign-in password hashes, voice PIN hashes, API token hashes, webhook signing secrets,
the client links used for portal sign-in, invoice payment and signing, the Coil install
key and any API keys or integration credentials saved in Settings. manifest.json lists
every column left out under excluded_columns.

PLEASE STORE THE DATABASE FILE SECURELY

database/practice.db is kept whole so it can be restored. That means it contains the
sign-in credentials of everyone at the firm in hashed form, and any API keys or
integration credentials (Stripe, Twilio, email, AI or CourtListener) saved in Settings,
in plain text. Store this export like any other confidential client file, and revoke or
rotate those keys with each provider once you stop using Coil.

RESTORING INTO SELF-HOSTED COIL

Coil is open source and runs on your own computer or server. To pick up where you left
off, install Coil (see docs/SELF-HOSTING.md in the Coil source), stop it, then build a
fresh data folder from this export:

  database/practice.db                 becomes  data/practice.db
  everything inside documents/files/   goes in  data/uploads/
  everything inside documents/unlinked/ goes in data/uploads/
  everything inside pdf/               goes in  data/pdf/

Use the Coil version named at the top of this file, or a newer one. The section
"Restore into a fresh data directory" in docs/SELF-HOSTING.md explains the checks to
make before starting it, and the section "Exporting all firm data" explains how this
file was made and checked.

THIS EXPORT

{summary}
"""


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------
def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:40].strip("-")
    return s or "firm"


def valid_slug(slug):
    return bool(slug) and bool(_SLUG.match(slug))


def build_export(db_path, out_dir, upload_dir=None, pdf_dir=None, *, slug=None, version="dev", commit="unknown",
                 producer="cli", tools=None, stamp=None):
    """Build one export zip and return its published path.

    The zip is written inside a private workspace in out_dir and published with a hard
    link only once it is complete, so no reader ever sees a torn file and an existing
    export is never replaced. Two runs in the same second get distinct names.
    """
    db_path = Path(db_path)
    if not db_path.is_file():
        raise ExportError(f"no SQLite database at {db_path}")
    if slug is not None and not valid_slug(slug):
        raise ExportError("slug must be lowercase letters, digits and inner hyphens only")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    stamp = stamp or created.strftime("%Y%m%dT%H%M%SZ")
    created_at = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    with _workspace(out_dir) as job:
        snap = job / "practice.db"
        _snapshot(db_path, snap)
        conn = sqlite3.connect(snap.resolve().as_uri() + "?mode=ro", uri=True)
        try:
            row = conn.execute("SELECT name FROM firm ORDER BY id LIMIT 1").fetchone() \
                if "firm" in _tables(conn) else None
            firm_name = (row[0] if row else "") or "Coil firm"
            slug = slug or slugify(firm_name)
            schema = database_schema(conn)
            partial = job / "export.zip.partial"
            with zipfile.ZipFile(partial, "x", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
                w = _Writer(zf)
                tables, excluded = _write_tables(w, conn)
                w.file(DB_MEMBER, snap)
                w.text(CUSTOMIZATIONS, json.dumps(build_customizations(conn, tools), indent=2, sort_keys=False,
                                                  ensure_ascii=False, default=str) + "\n")
                docs = _write_documents(w, conn, upload_dir)
                pdf_files = 0
                if pdf_dir and Path(pdf_dir).is_dir():
                    root = os.path.realpath(str(pdf_dir))
                    for dirpath, dirnames, filenames in os.walk(root):
                        dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(dirpath, d)))
                        for fn in sorted(filenames):
                            full = os.path.join(dirpath, fn)
                            if os.path.islink(full) or not os.path.isfile(full):
                                continue
                            w.file(_arc_safe("pdf/" + os.path.relpath(full, root).replace(os.sep, "/")), full)
                            pdf_files += 1
                total_rows = sum(t["rows"] for t in tables.values())
                summary = (f"{len(tables)} tables, {total_rows} rows in all. {docs['included_files']} stored files "
                           f"for {docs['document_rows']} document records, {len(docs['missing'])} records whose file "
                           f"was missing, {len(docs['unlinked'])} unlinked files, {pdf_files} generated PDFs.")
                w.text(README, readme_text(firm_name, created_at, version or "dev", commit or "unknown", summary))
                manifest = {
                    "format": FORMAT, "format_version": FORMAT_VERSION, "producer": producer,
                    "coil_version": version or "dev", "coil_commit": commit or "unknown", "created_at": created_at,
                    "firm": {"name": firm_name, "slug": slug},
                    "schema": schema, "schema_fingerprint": schema_fingerprint(schema),
                    "tables": tables, "excluded_columns": excluded,
                    "documents": docs, "pdf_files": pdf_files, "summary": summary,
                    "files": sorted(w.files, key=lambda f: f["path"]),
                }
                info = zipfile.ZipInfo(MANIFEST, date_time=created.timetuple()[:6])
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o600 << 16
                zf.writestr(info, json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        finally:
            conn.close()
        os.chmod(partial, 0o600)
        base = f"{PREFIX}{slug}-{stamp}"
        for n in range(1, 1000):
            target = out_dir / (f"{base}.zip" if n == 1 else f"{base}-{n}.zip")
            try:
                os.link(partial, target)
            except FileExistsError:
                continue
            return target
        raise ExportError("could not find a free export file name")


def _app_settings():
    """(db_path, upload_dir, pdf_dir, out_dir, version, commit, tools) from the running app."""
    from flask import current_app
    from .config import DATA_DIR
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:"):
        raise ExportError("the full export needs a SQLite database")
    db_path = Path(uri.split("sqlite:///", 1)[-1])
    out_dir = Path(current_app.config.get("EXPORT_DIR") or os.path.join(DATA_DIR, "exports"))
    return (db_path, current_app.config.get("UPLOAD_DIR"), current_app.config.get("PDF_DIR"), out_dir,
            current_app.config.get("COIL_VERSION"), current_app.config.get("COIL_COMMIT"))


def export_dir():
    """Where exports of the running app are written: EXPORT_DIR, or data/exports."""
    return _app_settings()[3]


def _tool_states(db_path):
    """{tool: {label, on, default_on}} from the tool switches saved in the database."""
    from types import SimpleNamespace
    from .tools import TOOLS, enabled_map
    conn = sqlite3.connect(Path(db_path).resolve().as_uri() + "?mode=ro", uri=True)
    try:
        row = conn.execute("SELECT tool_overrides FROM firm ORDER BY id LIMIT 1").fetchone()
    except sqlite3.Error:
        row = None
    finally:
        conn.close()
    on = enabled_map(SimpleNamespace(tool_overrides=row[0] if row else "{}"))
    return {k: {"label": t.label, "on": bool(on.get(k)), "default_on": t.default_on} for k, t in TOOLS.items()}


def export_firm(out_dir=None, slug=None, producer="cli"):
    """Build an export of the running app's firm. Call inside an app context."""
    db_path, upload_dir, pdf_dir, default_out, version, commit = _app_settings()
    return build_export(db_path, Path(out_dir) if out_dir else default_out, upload_dir, pdf_dir, slug=slug,
                        version=version, commit=commit, producer=producer, tools=_tool_states(db_path))


def export_firm_cli(args):
    """`python -m app.cli export_firm [--out DIR] [--slug SLUG]`. Prints EXPORT_FILE=<path> last."""
    out_dir = slug = None
    it = iter(args)
    for a in it:
        if a == "--out":
            out_dir = next(it, None)
            if not out_dir:
                print("export_firm: --out needs a directory")
                return 2
        elif a == "--slug":
            slug = next(it, None)
            if not valid_slug(slug or ""):
                print("export_firm: slug must be lowercase letters, digits and inner hyphens only")
                return 2
        else:
            print(f"export_firm: unknown option {a}")
            print("usage: python -m app.cli export_firm [--out DIR] [--slug SLUG]")
            return 2
    from .extensions import db
    from .models import audit
    try:
        path = export_firm(out_dir=out_dir, slug=slug)
    except ExportError as e:
        print(f"export_firm: FAILED, {e}")
        return 1
    ok, problems, summary = verify_export(path)
    if not ok:
        print(f"export_firm: built {path} but it FAILED verification:")
        for p in problems:
            print(f"  {p}")
        return 1
    audit("firm_export", "firm", 1, f"full firm export {path.name} ({path.stat().st_size} bytes, command line)")
    db.session.commit()
    print(f"export_firm: {summary}")
    print(f"Verified. Stored in {path.parent}, which is inside the data folder; copy it off this machine.")
    print("It contains client data and hashed sign-in credentials. Store it securely.")
    print(f"EXPORT_FILE={path}")
    return 0


# ---------------------------------------------------------------------------
# verify (standard library only: runs on a host without Coil)
# ---------------------------------------------------------------------------
def _sha_member(zf, name):
    h, size = hashlib.sha256(), 0
    with zf.open(name) as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def _csv_rows(zf, name):
    # SQLite text can exceed csv's default 128 KiB field limit. All export
    # readers use the same ceiling without restoring a smaller global limit
    # underneath another thread. Accommodate platforms with a narrower C long.
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            break
        except OverflowError:
            limit //= 10
    with zf.open(name) as raw:
        text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
        reader = csv.reader(text)
        header = next(reader, None)
        rows = [r for r in reader]
    return header, rows


def verify_export(path):
    """(ok, problems, summary). Proves the export is complete and usable:

    every manifest file is present with a matching sha256 and nothing unlisted is present;
    the database passes PRAGMA integrity_check, its schema matches the manifest, and its row
    counts match the manifest and each table CSV; every file in documents/index.csv is in
    the zip with the sha256 recorded there.
    """
    problems = []
    path = Path(path)
    try:
        zf = zipfile.ZipFile(path)
    except (OSError, zipfile.BadZipFile) as e:
        return False, [f"cannot open {path.name} as a zip file: {e}"], ""
    with zf, tempfile.TemporaryDirectory(prefix="coil-verify-") as tmp:
        # No separate testzip() pass: reading each member for its sha256 below also checks its
        # CRC (zipfile raises at the end of a damaged member), and an export can be gigabytes.
        names = set(zf.namelist())
        if MANIFEST not in names:
            return False, problems + ["manifest.json is missing"], ""
        try:
            manifest = json.loads(zf.read(MANIFEST).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            return False, problems + [f"manifest.json is not readable JSON: {e}"], ""
        if manifest.get("format") != FORMAT or manifest.get("format_version") != FORMAT_VERSION:
            return False, problems + ["manifest.json is not a Coil firm export this code understands"], ""
        listed = {f["path"]: f for f in manifest.get("files", [])}
        for required in (README, DB_MEMBER, CUSTOMIZATIONS, DOC_INDEX):
            if required not in listed:
                problems.append(f"{required} is not listed in the manifest")
        for name, f in sorted(listed.items()):
            if name not in names:
                problems.append(f"{name} is listed in the manifest but missing from the zip")
                continue
            try:
                sha, size = _sha_member(zf, name)
            except Exception as e:  # noqa: BLE001
                problems.append(f"{name} cannot be read: {e}")
                continue
            if sha != f.get("sha256") or size != f.get("size"):
                problems.append(f"{name} does not match the manifest (sha256 or size differs)")
        for name in sorted(names - set(listed) - {MANIFEST}):
            problems.append(f"{name} is in the zip but not in the manifest")

        # database
        tables = manifest.get("tables", {})
        db_counts = {}
        if DB_MEMBER in names:
            db_file = Path(tmp) / "practice.db"
            try:
                with zf.open(DB_MEMBER) as src, open(db_file, "wb") as dst:
                    shutil.copyfileobj(src, dst, CHUNK)
                conn = sqlite3.connect(str(db_file))
                try:
                    result = [r[0] for r in conn.execute("PRAGMA integrity_check")]
                    if result != ["ok"]:
                        problems.append("database integrity check failed: " + "; ".join(result[:5]))
                    else:
                        schema = database_schema(conn)
                        if schema_fingerprint(schema) != manifest.get("schema_fingerprint"):
                            problems.append("database schema does not match the manifest")
                        for t in _tables(conn):
                            db_counts[t] = _count(conn, t)
                finally:
                    conn.close()
            except (sqlite3.Error, OSError, zipfile.BadZipFile) as e:
                problems.append(f"database integrity check failed: {e}")
        if db_counts:
            for t in sorted(set(db_counts) | set(tables)):
                if t not in tables:
                    problems.append(f"table {t} is in the database but not in the manifest")
                elif t not in db_counts:
                    problems.append(f"table {t} is in the manifest but not in the database")
                elif db_counts[t] != tables[t].get("rows"):
                    problems.append(f"table {t}: database has {db_counts[t]} rows, manifest says {tables[t].get('rows')}")

        # table CSVs
        for t, info in sorted(tables.items()):
            name = info.get("csv") or f"csv/{t}.csv"
            if name not in names:
                problems.append(f"{name} is missing")
                continue
            try:
                header, rows = _csv_rows(zf, name)
            except Exception as e:  # noqa: BLE001
                problems.append(f"{name} cannot be read: {e}")
                continue
            if header is None or (header != info.get("columns") and not (header == [] and not info.get("columns"))):
                problems.append(f"{name} header does not match the manifest columns")
            if len(rows) != info.get("rows"):
                problems.append(f"{name} has {len(rows)} data rows, the manifest says {info.get('rows')}")
            elif t in db_counts and len(rows) != db_counts[t]:
                problems.append(f"{name} has {len(rows)} data rows, the database has {db_counts[t]}")
            leaked = set(header or []) & set(info.get("excluded_columns") or [])
            if leaked:
                problems.append(f"{name} contains excluded columns: {', '.join(sorted(leaked))}")

        # documents
        docs = manifest.get("documents", {})
        if DOC_INDEX in names:
            try:
                header, rows = _csv_rows(zf, DOC_INDEX)
            except Exception as e:  # noqa: BLE001
                header, rows = None, []
                problems.append(f"{DOC_INDEX} cannot be read: {e}")
            if header is not None:
                if header != INDEX_COLUMNS:
                    problems.append(f"{DOC_INDEX} has unexpected columns")
                else:
                    missing_rows = 0
                    doc_rows = 0
                    for r in rows:
                        row = dict(zip(header, r))
                        if row["record_type"] == "document":
                            doc_rows += 1
                        if row["status"] == "missing":
                            missing_rows += 1
                            continue
                        arc = row["archive_path"]
                        if arc not in names:
                            problems.append(f"document file {arc or '(blank)'} from {DOC_INDEX} is not in the zip")
                        elif listed.get(arc, {}).get("sha256") != row["sha256"]:
                            problems.append(f"document file {arc} does not match its sha256 in {DOC_INDEX}")
                    if missing_rows != len(docs.get("missing", [])):
                        problems.append(f"{DOC_INDEX} marks {missing_rows} files missing, the manifest lists "
                                        f"{len(docs.get('missing', []))}")
                    if "documents" in db_counts and doc_rows != db_counts["documents"]:
                        problems.append(f"{DOC_INDEX} covers {doc_rows} documents, the database has "
                                        f"{db_counts['documents']}")

    summary = ""
    if not problems:
        firm = manifest.get("firm", {}).get("name", "")
        summary = (f"{path.name}: {firm}, {len(tables)} tables, {sum(db_counts.values())} rows, "
                   f"{len(listed)} files checked, {docs.get('included_files', 0)} stored files, "
                   f"{len(docs.get('missing', []))} missing, {len(docs.get('unlinked', []))} unlinked. "
                   f"Made by Coil {manifest.get('coil_version')} ({manifest.get('coil_commit')}) "
                   f"at {manifest.get('created_at')}.")
    return not problems, problems, summary


def verify_main(args):
    """`verify_export <zip>`: prints OK and a summary, or every problem; exit 1 on failure."""
    if len(args) != 1:
        print("usage: verify_export <export.zip>")
        return 2
    ok, problems, summary = verify_export(args[0])
    if ok:
        print(f"OK {summary}")
        return 0
    print(f"FAILED: {args[0]} is not a complete, usable export.")
    for p in problems:
        print(f"  {p}")
    return 1


if __name__ == "__main__":
    argv = sys.argv[1:]
    if argv and argv[0] == "verify":
        sys.exit(verify_main(argv[1:]))
    print("usage: python3 firm_export.py verify <export.zip>")
    sys.exit(2)
