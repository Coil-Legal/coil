"""Complete firm export for offboarding (gate C08): a departing firm receives usable, complete
data and customizations, with no secret in the spreadsheets, and the verifier proves it.

Run: .venv/bin/python -m pytest tests/test_firm_export.py -q
"""
import csv
import hashlib
import io
import json
import os
import sqlite3
import subprocess
import sys
import threading
import zipfile
from datetime import timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.helpers import login  # noqa: E402

# Distinctive values planted in every secret-bearing column. None may reach a CSV or
# customizations.json; all of them must stay in the database snapshot.
PLANTED = {
    "install_key": "PLANTEDINSTALLKEY0001",
    "courtlistener_token": "PLANTEDCOURTLISTENER0002",
    "ai_api_key": "sk-ant-PLANTEDAIKEY0003",
    "stripe": "sk_test_PLANTEDSTRIPE0004",
    "api_token_hash": "PLANTEDAPITOKENHASH0005",
    "oauth_secret_hash": "PLANTEDOAUTHSECRET0006",
    "oauth_code_hash": "PLANTEDOAUTHCODE0007",
    "oauth_refresh_hash": "PLANTEDOAUTHREFRESH0008",
    "webhook_secret": "PLANTEDWEBHOOKSECRET0009",
    "portal_token": "PLANTEDPORTALTOKEN0010",
    "invoice_token": "PLANTEDINVOICETOKEN0011",
    "engagement_token": "PLANTEDENGAGEMENTTOKEN0012",
    "signature_token": "PLANTEDSIGNATURETOKEN0013",
    "booking_token": "PLANTEDBOOKINGTOKEN0014",
    "questionnaire_token": "PLANTEDQUESTIONNAIRE0015",
    "voice_pin_hash": "PLANTEDVOICEPINHASH0016",
}
ROLES = ("attorney", "paralegal", "billing", "readonly", "staff")
DOC_BYTES = b"%PDF-1.4 planted contract body"


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("firm_export")
    db_path, uploads, pdf, out = root / "practice.db", root / "uploads", root / "pdf", root / "exports"
    uri = f"sqlite:///{db_path}"
    seeded = subprocess.run([sys.executable, str(ROOT / "seed.py")], cwd=ROOT, capture_output=True, text=True,
                            env=dict(os.environ, DATABASE_URL=uri, STRIPE_SECRET_KEY="", SMTP_HOST=""))
    assert seeded.returncode == 0, seeded.stderr
    from app import create_app
    app = create_app({"SQLALCHEMY_DATABASE_URI": uri, "UPLOAD_DIR": str(uploads), "PDF_DIR": str(pdf),
                      "EXPORT_DIR": str(out), "TESTING": True, "SECRET_KEY": "firm-export-tests",
                      "STRIPE_SECRET_KEY": "", "SMTP_HOST": ""})
    from app.extensions import db
    from app import models as M
    with app.app_context():
        firm = M.Firm.get()
        firm.install_key = PLANTED["install_key"]
        firm.courtlistener_token = PLANTED["courtlistener_token"]
        firm.ai_api_key = PLANTED["ai_api_key"]
        firm.integration_json = json.dumps({"STRIPE_SECRET_KEY": PLANTED["stripe"], "TWILIO_AUTH_TOKEN": ""})
        firm.tool_overrides = json.dumps({"pi": False})
        owner = M.User.query.filter_by(email="owner@example.com").one()
        owner.voice_pin_hash = PLANTED["voice_pin_hash"]
        for role in ROLES:
            u = M.User(email=f"{role}@export.test", name=f"Export {role}", role=role)
            u.set_password("password123")
            db.session.add(u)
        matter = M.Matter.query.order_by(M.Matter.id).first()
        client = db.session.get(M.Contact, matter.client_id)
        accented = M.Contact(first_name="José", last_name="Núñez", is_client=True,
                             custom_fields_json=json.dumps({"Referral source": "Bar"}))
        db.session.add(accented)
        db.session.flush()
        inv = M.Invoice(number="INV-EXP-1", matter_id=matter.id, client_id=client.id, total_cents=12500,
                        public_token=PLANTED["invoice_token"])
        eng = M.Engagement(matter_id=matter.id, contact_id=client.id, token=PLANTED["engagement_token"],
                           document_hash="a" * 64)
        db.session.add_all([inv, eng])
        # A document whose file is stored, one whose file has gone, and a receipt.
        (uploads / str(matter.id)).mkdir(parents=True, exist_ok=True)
        (uploads / str(matter.id) / "abc_contract.pdf").write_bytes(DOC_BYTES)
        good = M.Document(matter_id=matter.id, name="Signed contract.pdf", path=f"{matter.id}/abc_contract.pdf",
                          size=len(DOC_BYTES), uploaded_by_id=owner.id)
        gone = M.Document(matter_id=matter.id, name="Lost scan.pdf", path=f"{matter.id}/gone_scan.pdf")
        escape = M.Document(matter_id=matter.id, name="Outside.txt", path="../../outside.txt")
        db.session.add_all([good, gone, escape])
        (root / "outside.txt").write_text("not part of the firm's storage")
        (uploads / "expenses").mkdir(parents=True, exist_ok=True)
        (uploads / "expenses" / "receipt1.png").write_bytes(b"\x89PNG receipt")
        db.session.add(M.Expense(matter_id=matter.id, amount_cents=4200, description="Filing fee",
                                 receipt_path="expenses/receipt1.png"))
        # A file in storage that no record points to.
        (uploads / "imports").mkdir(parents=True, exist_ok=True)
        (uploads / "imports" / "old-clio.csv").write_text("name\nLeftover\n")
        pdf.mkdir(parents=True, exist_ok=True)
        (pdf / "INV-EXP-1.pdf").write_bytes(b"%PDF generated invoice")
        db.session.flush()
        db.session.add(M.DocumentSignature(document_id=good.id, contact_id=client.id,
                                           token=PLANTED["signature_token"], document_hash="b" * 64))
        db.session.add(M.PortalToken(contact_id=client.id, token=PLANTED["portal_token"],
                                     expires_at=M.now() + timedelta(minutes=30)))
        db.session.add(M.ApiToken(user_id=owner.id, name="export test", token_hash=PLANTED["api_token_hash"],
                                  prefix="coil_ab"))
        oc = M.OAuthClient(client_id="export-client", client_secret_hash=PLANTED["oauth_secret_hash"])
        db.session.add(oc)
        db.session.flush()
        db.session.add(M.OAuthCode(code_hash=PLANTED["oauth_code_hash"], oauth_client_id=oc.id, user_id=owner.id))
        db.session.add(M.OAuthRefreshToken(token_hash=PLANTED["oauth_refresh_hash"], oauth_client_id=oc.id,
                                           user_id=owner.id, chain="chain-1"))
        db.session.add(M.Webhook(url="https://hooks.example.test/x", events="invoice.paid",
                                 secret=PLANTED["webhook_secret"]))
        bt = M.BookingType(name="Consult", slug="consult")
        q = M.Questionnaire(name="Intake questions", questions_json='[{"q": "What happened?"}]')
        db.session.add_all([bt, q])
        db.session.flush()
        db.session.add(M.Booking(booking_type_id=bt.id, starts_at=M.now(), token=PLANTED["booking_token"],
                                 name="Booker"))
        db.session.add(M.QuestionnaireResponse(questionnaire_id=q.id, token=PLANTED["questionnaire_token"]))
        db.session.add(M.MatterTemplate(name="Export flat fee template", practice_area="Estate Planning"))
        db.session.commit()
        ids = {"good": good.id, "gone": gone.id, "escape": escape.id, "matter": matter.number}
    return dict(app=app, db=db_path, uploads=uploads, pdf=pdf, out=out, root=root, ids=ids)


def _export(env, out=None, **kw):
    from app.firm_export import export_firm
    with env["app"].app_context():
        return export_firm(out_dir=out, **kw)


def _live_counts(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        names = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {n: conn.execute(f'SELECT COUNT(*) FROM "{n}"').fetchone()[0] for n in names}
    finally:
        conn.close()


def _csv(zf, name):
    raw = zf.read(name)
    assert raw.startswith(b"\xef\xbb\xbf"), f"{name} has no UTF-8 BOM"
    rows = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    return rows[0], rows[1:]


@pytest.fixture(scope="module")
def good_zip(env, tmp_path_factory):
    return _export(env, tmp_path_factory.mktemp("good"))


# ---------------------------------------------------------------------------
# contents
# ---------------------------------------------------------------------------
def test_export_holds_every_table_the_database_readme_and_customizations(env, good_zip):
    counts = _live_counts(env["db"])
    assert len(counts) >= 70
    with zipfile.ZipFile(good_zip) as zf:
        names = set(zf.namelist())
        for required in ("README.txt", "manifest.json", "database/practice.db",
                         "customizations/customizations.json", "documents/index.csv"):
            assert required in names
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest["format"] == "coil-firm-export" and manifest["format_version"] == 1
        assert manifest["firm"]["name"] == "Demo Law PLLC"
        assert manifest["coil_version"] and manifest["coil_commit"] and manifest["created_at"].endswith("Z")
        assert len(manifest["schema_fingerprint"]) == 64
        assert set(manifest["tables"]) == set(counts)
        for table, n in counts.items():
            assert manifest["tables"][table]["rows"] == n, table
            header, rows = _csv(zf, f"csv/{table}.csv")
            assert len(rows) == n, table
            assert header == manifest["tables"][table]["columns"]
        listed = {f["path"] for f in manifest["files"]}
        assert listed == names - {"manifest.json"}
        readme = zf.read("README.txt").decode("utf-8")
    assert "—" not in readme and "--" not in readme
    assert "database/practice.db" in readme and "SELF-HOSTING.md" in readme
    assert "hashed form" in readme and "cents" in readme and "From Text/CSV" in readme
    assert Path(good_zip).name.startswith("coil-export-demo-law-pllc-")


def test_csv_values_are_excel_ready(env, good_zip):
    with zipfile.ZipFile(good_zip) as zf:
        header, rows = _csv(zf, "csv/contacts.csv")
        assert any("José" in r and "Núñez" in r for r in rows), "accented name lost"
        header, rows = _csv(zf, "csv/invoices.csv")
        inv = dict(zip(header, next(r for r in rows if "INV-EXP-1" in r)))
        assert inv["total_cents"] == "12500"  # money stays integer cents
        assert "T" in inv["created_at"] and " " not in inv["created_at"]  # ISO timestamps
        assert inv["issued_on"].count("-") == 2 and len(inv["issued_on"]) == 10


def test_customizations_json_is_readable_and_complete(good_zip):
    with zipfile.ZipFile(good_zip) as zf:
        c = json.loads(zf.read("customizations/customizations.json"))
    assert c["firm_settings"]["values"]["name"] == "Demo Law PLLC"
    assert c["firm_settings"]["integration_credentials_saved"] == ["STRIPE_SECRET_KEY"]
    assert c["invoice_template"]["values"]["invoice_title"] == "INVOICE"
    assert c["tools"]["overrides"] == {"pi": False}
    assert c["tools"]["effective"]["pi"]["on"] is False
    assert c["custom_fields"]["contacts"] == {"Referral source": 1}
    assert any(t["name"] == "Export flat fee template" for t in c["matter_templates"]["rows"])
    assert c["questionnaires"]["rows"][0]["questions"] == [{"q": "What happened?"}]
    for key in ("users", "offices", "letter_templates", "appearance_and_workflows", "webhooks"):
        assert "_about" in c[key]
    assert all("password_hash" not in u for u in c["users"]["rows"])


# ---------------------------------------------------------------------------
# secrets
# ---------------------------------------------------------------------------
def test_secret_values_reach_no_csv_and_no_customizations(good_zip):
    with zipfile.ZipFile(good_zip) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        readable = [n for n in zf.namelist() if n.endswith((".csv", ".json", ".txt"))
                    and not n.startswith("documents/unlinked/")]
        for name in readable:
            text = zf.read(name).decode("utf-8", "replace")
            for label, value in PLANTED.items():
                assert value not in text, f"{label} leaked into {name}"
            assert "pbkdf2:" not in text and "scrypt:" not in text, f"password hash leaked into {name}"
        # The database is the complete record and keeps them.
        db_bytes = zf.read("database/practice.db")
    for value in PLANTED.values():
        assert value.encode() in db_bytes
    excluded = {(e["table"], e["column"]) for e in manifest["excluded_columns"]}
    from app.firm_export import SECRET_COLUMNS
    assert set(SECRET_COLUMNS) <= excluded


def test_excluded_columns_are_exactly_the_reviewed_list():
    """A new column whose name looks secret is excluded by the safety net and fails here,
    so somebody decides on purpose whether it belongs in SECRET_COLUMNS or NOT_SECRET."""
    from app.backup_manifest import known_schema
    from app.firm_export import SECRET_COLUMNS, NOT_SECRET, SECRET_PATTERN, excluded_reason
    schema = known_schema()
    excluded = {(t, c) for t, cols in schema.items() for c in cols if excluded_reason(t, c)}
    assert excluded == set(SECRET_COLUMNS)
    for (t, c) in set(SECRET_COLUMNS) | set(NOT_SECRET):
        assert c in schema.get(t, []), f"{t}.{c} no longer exists; remove it from the list"
    matched = {(t, c) for t, cols in schema.items() for c in cols if SECRET_PATTERN.search(c)}
    assert matched <= set(SECRET_COLUMNS) | set(NOT_SECRET)
    # The safety net on names nobody has listed yet.
    assert excluded_reason("users", "totp_secret")
    assert excluded_reason("firm", "twilio_api_key")
    assert excluded_reason("contacts", "portal_password")
    assert excluded_reason("engagements", "document_hash") is None
    assert excluded_reason("contacts", "first_name") is None


# ---------------------------------------------------------------------------
# documents
# ---------------------------------------------------------------------------
def test_documents_index_missing_and_unlinked_files(env, good_zip):
    ids = env["ids"]
    with zipfile.ZipFile(good_zip) as zf:
        manifest = json.loads(zf.read("manifest.json"))
        header, rows = _csv(zf, "documents/index.csv")
        index = [dict(zip(header, r)) for r in rows]
        by_doc = {r["document_id"]: r for r in index if r["record_type"] == "document"}
        good = by_doc[str(ids["good"])]
        assert good["status"] == "included"
        assert good["original_filename"] == "Signed contract.pdf"
        assert good["matter_number"] == ids["matter"] and good["matter_name"] and good["contact"]
        assert good["uploaded_on"] and good["sha256"] == hashlib.sha256(DOC_BYTES).hexdigest()
        assert zf.read(good["archive_path"]) == DOC_BYTES
        assert good["archive_path"].startswith("documents/files/")
        gone = by_doc[str(ids["gone"])]
        assert gone["status"] == "missing" and gone["archive_path"] == ""
        outside = by_doc[str(ids["escape"])]
        assert outside["status"] == "missing" and "outside" in outside["note"]
        missing = {(m["record_type"], m["record_id"]) for m in manifest["documents"]["missing"]}
        assert {("document", ids["gone"]), ("document", ids["escape"])} <= missing
        assert "not part of the firm" not in json.dumps(manifest)
        unlinked = {u["stored_path"]: u for u in manifest["documents"]["unlinked"]}
        assert "imports/old-clio.csv" in unlinked
        assert zf.read("documents/unlinked/imports/old-clio.csv") == b"name\nLeftover\n"
        receipt = next(r for r in index if r["record_type"] == "expense_receipt")
        assert receipt["status"] == "included"
        assert zf.read(receipt["archive_path"]) == b"\x89PNG receipt"
        assert zf.read("pdf/INV-EXP-1.pdf") == b"%PDF generated invoice"
        assert not any(n.endswith("outside.txt") for n in zf.namelist())


# ---------------------------------------------------------------------------
# verification
# ---------------------------------------------------------------------------
def _rewrite(src, dst, changes, reseal):
    """Copy an export, replacing (bytes) or dropping (None) members. With reseal, the manifest's
    file list is updated to match, so only the deeper checks can catch the change."""
    with zipfile.ZipFile(src) as zin:
        manifest = json.loads(zin.read("manifest.json"))
        members = {n: zin.read(n) for n in zin.namelist() if n != "manifest.json"}
    for name, data in changes.items():
        if data is None:
            members.pop(name, None)
        else:
            members[name] = data
    if reseal:
        manifest["files"] = [{"path": n, "size": len(b), "sha256": hashlib.sha256(b).hexdigest()}
                             for n, b in sorted(members.items())]
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for n, b in members.items():
            zout.writestr(n, b)
        zout.writestr("manifest.json", json.dumps(manifest))
    return dst


def _problems(path):
    from app.firm_export import verify_export
    ok, problems, summary = verify_export(path)
    return ok, " | ".join(problems), summary


def test_verify_passes_on_a_good_export(good_zip):
    ok, problems, summary = _problems(good_zip)
    assert ok, problems
    assert "Demo Law PLLC" in summary and "tables" in summary


def test_verify_fails_on_a_tampered_file(good_zip, tmp_path):
    bad = _rewrite(good_zip, tmp_path / "t.zip", {"csv/contacts.csv": b"\xef\xbb\xbfid\n1\n"}, reseal=False)
    ok, problems, _ = _problems(bad)
    assert not ok and "csv/contacts.csv does not match the manifest" in problems


def test_verify_fails_on_a_removed_file(good_zip, tmp_path):
    bad = _rewrite(good_zip, tmp_path / "r.zip", {"csv/matters.csv": None}, reseal=False)
    ok, problems, _ = _problems(bad)
    assert not ok and "csv/matters.csv is listed in the manifest but missing" in problems


def test_verify_fails_on_a_truncated_database(good_zip, tmp_path):
    with zipfile.ZipFile(good_zip) as zf:
        data = zf.read("database/practice.db")
    unsealed = _rewrite(good_zip, tmp_path / "d1.zip", {"database/practice.db": data[:len(data) // 3]}, reseal=False)
    ok, problems, _ = _problems(unsealed)
    assert not ok and "database/practice.db does not match the manifest" in problems
    # Even with a manifest recomputed to match, the database itself is checked.
    corrupt = data[:4096] + b"\x00garbage" * 2000 + data[4096 + 16000:]
    sealed = _rewrite(good_zip, tmp_path / "d2.zip", {"database/practice.db": corrupt}, reseal=True)
    ok, problems, _ = _problems(sealed)
    assert not ok and "database integrity check failed" in problems, problems


def test_verify_fails_when_a_csv_row_is_removed(good_zip, tmp_path):
    with zipfile.ZipFile(good_zip) as zf:
        lines = zf.read("csv/contacts.csv").decode("utf-8-sig").splitlines(keepends=True)
    shorter = ("﻿" + "".join(lines[:-1])).encode("utf-8")
    bad = _rewrite(good_zip, tmp_path / "c.zip", {"csv/contacts.csv": shorter}, reseal=True)
    ok, problems, _ = _problems(bad)
    assert not ok and "csv/contacts.csv has" in problems and "data rows" in problems


def test_verify_fails_when_a_document_file_is_gone(env, good_zip, tmp_path):
    with zipfile.ZipFile(good_zip) as zf:
        header, rows = _csv(zf, "documents/index.csv")
    arc = next(dict(zip(header, r))["archive_path"] for r in rows if dict(zip(header, r))["status"] == "included")
    bad = _rewrite(good_zip, tmp_path / "x.zip", {arc: None}, reseal=True)
    ok, problems, _ = _problems(bad)
    assert not ok and f"document file {arc}" in problems


def test_verify_fails_on_something_that_is_not_an_export(tmp_path):
    p = tmp_path / "junk.zip"
    p.write_bytes(b"not a zip")
    ok, problems, _ = _problems(p)
    assert not ok and "cannot open" in problems


def test_verifier_runs_without_flask_or_the_app_package(good_zip, tmp_path):
    """ops/export-firm.sh runs it with the host's python3, which has no Flask."""
    probe = tmp_path / "probe.py"
    probe.write_text("import runpy, sys\n"
                     "class Block:\n"
                     "    def find_spec(self, name, path=None, target=None):\n"
                     "        if name.split('.')[0] in ('flask', 'sqlalchemy', 'flask_sqlalchemy', 'app', 'werkzeug'):\n"
                     "            raise ImportError('blocked ' + name)\n"
                     "sys.meta_path.insert(0, Block())\n"
                     f"sys.argv = ['firm_export.py', 'verify', {str(good_zip)!r}]\n"
                     f"runpy.run_path({str(ROOT / 'app' / 'firm_export.py')!r}, run_name='__main__')\n")
    r = subprocess.run([sys.executable, "-I", str(probe)], capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("OK ")


# ---------------------------------------------------------------------------
# publication and concurrency
# ---------------------------------------------------------------------------
def test_second_export_in_the_same_second_does_not_overwrite_the_first(env, tmp_path):
    from app.firm_export import build_export
    first = build_export(env["db"], tmp_path, env["uploads"], env["pdf"], stamp="20261011T000000Z")
    before = first.read_bytes()
    second = build_export(env["db"], tmp_path, env["uploads"], env["pdf"], stamp="20261011T000000Z")
    assert first != second and second.name.endswith("-2.zip")
    assert first.read_bytes() == before
    assert not list(tmp_path.glob(".coil-export-job-*"))
    assert oct(first.stat().st_mode & 0o777) == "0o600"


def test_concurrent_exports_each_publish_a_complete_file(env, tmp_path):
    from app.firm_export import build_export, verify_export
    results, errors = [], []

    def run():
        try:
            results.append(build_export(env["db"], tmp_path, env["uploads"], env["pdf"], stamp="20261011T010000Z"))
        except Exception as e:  # noqa: BLE001
            errors.append(e)
    threads = [threading.Thread(target=run) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert len({p.name for p in results}) == 3
    for p in results:
        assert verify_export(p)[0]
    assert not list(tmp_path.glob("*.partial")) and not list(tmp_path.glob(".coil-export-job-*"))


def test_crashed_workspace_is_reclaimed_but_a_live_one_is_not(env, tmp_path):
    import fcntl
    from app.firm_export import build_export
    stale = tmp_path / ".coil-export-job-stale"
    stale.mkdir()
    (stale / "lease").write_bytes(b"")
    (stale / "export.zip.partial").write_bytes(b"half")
    live = tmp_path / ".coil-export-job-live"
    live.mkdir()
    with (live / "lease").open("a+b") as lease:
        fcntl.flock(lease, fcntl.LOCK_EX)
        build_export(env["db"], tmp_path, env["uploads"], env["pdf"])
        assert not stale.exists()
        assert live.exists()


def test_build_lock_refuses_a_second_build(tmp_path):
    from app.firm_export import ExportBusy, build_lock
    with build_lock(tmp_path):
        with pytest.raises(ExportBusy):
            with build_lock(tmp_path):
                pass
    with build_lock(tmp_path):
        pass


# ---------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------
def test_cli_export_firm_and_verify_export(env, tmp_path, monkeypatch, capsys):
    import app as app_pkg
    from app import cli
    from app.models import AuditLog
    monkeypatch.setattr(app_pkg, "create_app", lambda *a, **k: env["app"])
    assert cli.main(["export_firm", "--out", str(tmp_path), "--slug", "synthetic"]) == 0
    out = capsys.readouterr().out
    line = [l for l in out.splitlines() if l.startswith("EXPORT_FILE=")][-1]
    path = Path(line.split("=", 1)[1])
    assert path.parent == tmp_path and path.name.startswith("coil-export-synthetic-")
    with env["app"].app_context():
        assert AuditLog.query.filter_by(action="firm_export").filter(
            AuditLog.detail.contains(path.name)).count() == 1
    assert cli.main(["verify_export", str(path)]) == 0
    assert capsys.readouterr().out.startswith("OK ")
    bad = _rewrite(path, tmp_path / "bad.zip", {"README.txt": b"changed"}, reseal=False)
    assert cli.main(["verify_export", str(bad)]) == 1
    assert "FAILED" in capsys.readouterr().out
    assert cli.main(["export_firm", "--slug", "Not A Slug"]) == 2
    assert cli.main(["export_firm", "--bogus"]) == 2
    assert "export_firm" in cli.COMMANDS and "verify_export" in cli.COMMANDS


# ---------------------------------------------------------------------------
# /settings/export
# ---------------------------------------------------------------------------
@pytest.fixture
def owner(env):
    c = env["app"].test_client()
    c._csrf = login(c)
    return c


def test_owner_downloads_a_zip_that_verifies_and_is_audited(env, owner, tmp_path):
    from app.models import AuditLog
    r = owner.get("/settings/export")
    assert r.status_code == 200 and b"Download all firm data" in r.data and b'name="_csrf"' in r.data
    r = owner.post("/settings/export", data={"_csrf": owner._csrf})
    assert r.status_code == 200, r.data[:400]
    assert r.mimetype == "application/zip"
    assert "attachment" in r.headers["Content-Disposition"] and "coil-export-" in r.headers["Content-Disposition"]
    assert r.headers["Cache-Control"] == "no-store"
    saved = tmp_path / "download.zip"
    saved.write_bytes(r.data)
    r.close()
    ok, problems, _ = _problems(saved)
    assert ok, problems
    with env["app"].app_context():
        entry = AuditLog.query.filter_by(action="firm_export").order_by(AuditLog.id.desc()).first()
        assert entry.user_id == 1 and "downloaded" in entry.detail
    # The server does not keep a copy of every client file after the download.
    assert not list(Path(env["out"]).glob("coil-export-*.zip"))
    page = owner.get("/settings/export")
    assert b"downloaded" in page.data


def test_settings_page_links_to_the_export(owner):
    assert b'href="/settings/export"' in owner.get("/settings").data
    assert b'href="/settings/export"' in owner.get("/exports").data


def test_post_requires_csrf(owner):
    assert owner.post("/settings/export", data={}).status_code == 400


def test_a_second_click_while_building_is_told_to_wait(env, owner):
    from app.firm_export import build_lock
    with build_lock(env["out"]):
        r = owner.post("/settings/export", data={"_csrf": owner._csrf})
    assert r.status_code == 409 and b"already being built" in r.data


@pytest.mark.parametrize("role", ROLES)
def test_every_other_role_is_refused(env, role):
    c = env["app"].test_client()
    tok = login(c, email=f"{role}@export.test")
    assert c.get("/settings/export").status_code == 403
    r = c.post("/settings/export", data={"_csrf": tok})
    assert r.status_code == 403
    assert r.mimetype != "application/zip"


def test_anonymous_is_sent_to_sign_in(env):
    r = env["app"].test_client().get("/settings/export")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_owner_exports_large_retained_text_field(env, owner, tmp_path):
    """Long retained records must not prevent the owner taking a complete export."""
    from app.extensions import db
    from app.models import Contact
    payload = "QA long retained note " * 15000
    with env["app"].app_context():
        record = Contact(first_name="QA Export Large Field", notes=payload)
        db.session.add(record)
        db.session.commit()
        record_id = record.id
    previous_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(131072)
        response = owner.post("/settings/export", data={"_csrf": owner._csrf})
        assert response.status_code == 200, response.data[:1000]
        saved = tmp_path / "large-field.zip"
        saved.write_bytes(response.data)
        from app.firm_export import verify_export
        assert verify_export(saved)[0]
        # The standalone host verifier starts with Python's default CSV limit too.
        verified = subprocess.run(
            [sys.executable, str(ROOT / "app/firm_export.py"), "verify", str(saved)],
            capture_output=True, text=True,
        )
        assert verified.returncode == 0, verified.stdout
        with zipfile.ZipFile(saved) as archive:
            assert payload.encode() in archive.read("csv/contacts.csv")
    finally:
        csv.field_size_limit(previous_limit)
        with env["app"].app_context():
            db.session.delete(db.session.get(Contact, record_id))
            db.session.commit()
