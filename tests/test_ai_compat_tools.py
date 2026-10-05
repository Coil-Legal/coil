"""AI-agent additions to the REST API and MCP (2026-10-05).

An assistant connected to Coil could read and log time but could not look a person up
properly, open a client or a matter, set or finish a task, run a conflict check, read a
document's text or search the firm. These cover each new endpoint and tool, that each one
keeps the UI's validation, that scopes still gate everything, that redacted tokens still
never see a name, and that the audit log records which token acted.

Own SQLite file. Run: .venv/bin/python -m pytest tests/test_ai_compat_tools.py -q
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_ai_compat_tools.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_ai_compat_tools")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_ai_compat_tools")


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(PDF_DIR, ignore_errors=True)
    env = dict(os.environ, DATABASE_URL=DB_URI, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="", SMTP_HOST="")
    for script in ("seed.py", "demo_data.py"):
        out = subprocess.run([sys.executable, os.path.join(ROOT, script)], env=env, cwd=ROOT,
                             capture_output=True, text=True)
        assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
                       "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": "",
                       "COIL_VERSION": "test"})


def _token(app, scopes, confidentiality="full", name="ai compat test"):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token, reset_rate_limits
    reset_rate_limits()
    with app.app_context():
        u = User.query.filter_by(email="owner@example.com").first()
        _, raw = create_token(u, name, scopes, confidentiality)
        db.session.commit()
    return {"Authorization": f"Bearer {raw}"}


ALL_READ = ["matters:read", "contacts:read", "time:read", "invoices:read", "tasks:read", "documents:read",
            "calendar:read", "notes:read", "leads:read", "conflicts:read"]
WRITES = ["contacts:write", "matters:write", "tasks:write", "conflicts:write"]


def _rpc(client, headers, method, params=None):
    r = client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}},
                    headers=headers)
    assert r.status_code == 200, r.data[:300]
    return r.get_json()["result"]


def _call(client, headers, name, args):
    res = _rpc(client, headers, "tools/call", {"name": name, "arguments": args})
    payload = json.loads(res["content"][0]["text"])
    assert payload == res["structuredContent"]
    return payload, res["isError"]


# ------------------------------------------------------------------ contacts
def test_create_contact_validates_like_the_form_and_get_contact_returns_matters(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES)
    r = c.post("/api/v1/contacts", json={"kind": "person"}, headers=h)
    assert r.status_code == 400 and "first_name or last_name" in r.get_json()["error"]
    r = c.post("/api/v1/contacts", json={"kind": "company"}, headers=h)
    assert r.status_code == 400 and "company_name" in r.get_json()["error"]
    r = c.post("/api/v1/contacts", json={"first_name": "Ελένη", "last_name": "AI Test 20261005",
                                         "email": "eleni-ai@example.test"}, headers=h)
    assert r.status_code == 201, r.data
    contact = r.get_json()["contact"]
    assert contact["name"] == "Ελένη AI Test 20261005" and contact["is_client"] is False
    r = c.get(f"/api/v1/contacts/{contact['id']}", headers=h)
    assert r.status_code == 200 and r.get_json()["matters"] == []
    assert c.get("/api/v1/contacts/99999999", headers=h).status_code == 404


def test_write_scope_is_needed_and_readonly_users_still_cannot_write(app):
    c = app.test_client()
    h = _token(app, ALL_READ)
    assert c.post("/api/v1/contacts", json={"first_name": "No"}, headers=h).status_code == 403
    assert c.post("/api/v1/conflicts", json={"names": ["X"]}, headers=h).status_code == 403


# ------------------------------------------------------------------ matters
def test_create_matter_needs_a_real_client_numbers_it_and_makes_the_contact_a_client(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES)
    assert c.post("/api/v1/matters", json={"name": "No client"}, headers=h).status_code == 400
    assert c.post("/api/v1/matters", json={"client_id": 99999999, "name": "X"}, headers=h).status_code == 400
    assert c.post("/api/v1/matters", json={"client_id": "abc", "name": "X"}, headers=h).status_code == 400
    who = c.post("/api/v1/contacts", json={"first_name": "Matter", "last_name": "Client 20261005"},
                 headers=h).get_json()["contact"]
    r = c.post("/api/v1/matters", json={"client_id": who["id"], "name": "AI Matter 20261005"}, headers=h)
    assert r.status_code == 201 and r.get_json()["matter"]["billing_type"] == "hourly"
    r = c.post("/api/v1/matters", json={"client_id": who["id"], "name": "AI Matter Two 20261005",
                                        "billing_type": "weekly"}, headers=h)
    assert r.status_code == 400 and "billing_type" in r.get_json()["error"]
    r = c.post("/api/v1/matters", json={"client_id": who["id"], "name": "AI Matter Three 20261005",
                                        "billing_type": "flat"}, headers=h)
    assert r.status_code == 201, r.data
    m = r.get_json()["matter"]
    assert m["number"].startswith("M-") and m["status"] == "open" and m["billing_type"] == "flat"
    back = c.get(f"/api/v1/contacts/{who['id']}", headers=h).get_json()
    assert back["is_client"] is True and any(x["id"] == m["id"] for x in back["matters"])


# ------------------------------------------------------------------ tasks
def test_create_task_and_complete_it_then_reopen(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES)
    assert c.post("/api/v1/tasks", json={}, headers=h).status_code == 400
    assert c.post("/api/v1/tasks", json={"title": "Bad date", "due_on": "2026-02-30"}, headers=h).status_code == 400
    assert c.post("/api/v1/tasks", json={"title": "Bad kind", "kind": "party"}, headers=h).status_code == 400
    r = c.post("/api/v1/tasks", json={"title": "AI task 20261005", "due_on": "2026-10-31", "priority": "high"},
               headers=h)
    assert r.status_code == 201, r.data
    t = r.get_json()["task"]
    assert t["due_on"] == "2026-10-31" and t["done"] is False
    r = c.post(f"/api/v1/tasks/{t['id']}/done", json={}, headers=h)
    assert r.get_json()["task"]["done"] is True
    r = c.post(f"/api/v1/tasks/{t['id']}/done", json={"done": False}, headers=h)
    assert r.get_json()["task"]["done"] is False
    assert c.post("/api/v1/tasks/99999999/done", json={}, headers=h).status_code == 404


# ------------------------------------------------------------------ conflicts
def test_conflict_check_runs_stores_and_reads_back(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES)
    assert c.post("/api/v1/conflicts", json={}, headers=h).status_code == 400
    assert c.post("/api/v1/conflicts", json={"names": ["..."]}, headers=h).status_code == 400
    c.post("/api/v1/contacts", json={"first_name": "Conflict", "last_name": "Person 20261005"}, headers=h)
    r = c.post("/api/v1/conflicts", json={"names": ["Conflict Person 20261005"]}, headers=h)
    assert r.status_code == 201, r.data
    chk = r.get_json()["conflict_check"]
    assert chk["hit_count"] >= 1 and chk["outcome"] == "unresolved"
    assert any(h_["found"] and "Conflict Person 20261005" in h_["found"] for h_ in chk["hits"])
    back = c.get(f"/api/v1/conflicts/{chk['id']}", headers=h).get_json()
    assert back["id"] == chk["id"] and back["hit_count"] == chk["hit_count"]


def test_redacted_conflict_check_withholds_every_name(app):
    c = app.test_client()
    full = _token(app, ALL_READ + WRITES)
    c.post("/api/v1/contacts", json={"first_name": "Secret", "last_name": "Name 20261005"}, headers=full)
    red = _token(app, ALL_READ + WRITES, "redacted")
    body = c.post("/api/v1/conflicts", json={"names": ["Secret Name 20261005"]}, headers=red).get_json()
    assert "Secret Name 20261005" not in json.dumps(body)
    assert body["conflict_check"]["hit_count"] >= 1


# ------------------------------------------------------------------ documents, invoices
def test_document_detail_returns_text_in_full_mode_only(app):
    from app.extensions import db
    from app.models import Document, Matter
    with app.app_context():
        m = Matter.query.first()
        d = Document(matter_id=m.id, name="ai-text-20261005.txt", path="ai-text-20261005.txt", size=10,
                     mime="text/plain", extracted_text="Καλημέρα. The deposition is on Friday.")
        db.session.add(d)
        db.session.commit()
        did = d.id
    c = app.test_client()
    body = c.get(f"/api/v1/documents/{did}", headers=_token(app, ["documents:read"])).get_json()
    assert body["text"] == "Καλημέρα. The deposition is on Friday." and body["text_available"] is True
    red = c.get(f"/api/v1/documents/{did}", headers=_token(app, ["documents:read"], "redacted")).get_json()
    assert "deposition" not in json.dumps(red) and red["text"] == "[redacted]"


def test_invoice_detail_has_lines(app):
    from app.models import Invoice
    with app.app_context():
        inv = Invoice.query.first()
        if inv is None:
            pytest.skip("demo data has no invoice")
        iid = inv.id
    body = app.test_client().get(f"/api/v1/invoices/{iid}", headers=_token(app, ["invoices:read"])).get_json()
    assert "lines" in body and isinstance(body["lines"], list)


# ------------------------------------------------------------------ search
def test_search_only_covers_what_the_token_may_read(app):
    c = app.test_client()
    full = _token(app, ALL_READ + WRITES)
    c.post("/api/v1/contacts", json={"first_name": "Searchable", "last_name": "Person 20261005"}, headers=full)
    body = c.get("/api/v1/search?q=Searchable", headers=_token(app, ALL_READ)).get_json()
    assert any("Searchable" in x["name"] for x in body["results"]["contacts"])
    narrow = c.get("/api/v1/search?q=Searchable", headers=_token(app, ["matters:read"])).get_json()
    assert narrow["searched"] == ["matters"] and "contacts" not in narrow["results"]
    assert c.get("/api/v1/search", headers=full).status_code == 400


def test_redacted_search_returns_no_names(app):
    c = app.test_client()
    full = _token(app, ALL_READ + WRITES)
    c.post("/api/v1/contacts", json={"first_name": "Hidden", "last_name": "Searchname 20261005"}, headers=full)
    body = c.get("/api/v1/search?q=Searchname", headers=_token(app, ALL_READ, "redacted")).get_json()
    assert "Searchname" not in json.dumps(body)
    assert len(body["results"]["contacts"]) >= 1


# ------------------------------------------------------------------ audit attribution
def test_audit_log_names_the_token_that_acted(app):
    from app.models import AuditLog
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES, name="Claude via MCP 20261005")
    cid = c.post("/api/v1/contacts", json={"first_name": "Audited", "last_name": "Contact 20261005"},
                 headers=h).get_json()["contact"]["id"]
    with app.app_context():
        row = AuditLog.query.filter_by(entity="contact", entity_id=cid, action="create").first()
        assert row is not None and 'via API token "Claude via MCP 20261005"' in row.detail


# ------------------------------------------------------------------ MCP
def test_mcp_lists_new_tools_by_scope_with_annotations(app):
    c = app.test_client()
    tools = {t["name"]: t for t in _rpc(c, _token(app, ALL_READ + WRITES), "tools/list")["tools"]}
    for name in ("search", "get_contact", "create_contact", "create_matter", "create_task", "complete_task",
                 "run_conflict_check", "get_conflict_check", "get_document", "get_invoice"):
        assert name in tools, name
    assert tools["get_contact"]["annotations"]["readOnlyHint"] is True
    assert tools["create_matter"]["annotations"]["readOnlyHint"] is False
    assert all(t["annotations"]["destructiveHint"] is False for t in tools.values())
    narrow = {t["name"] for t in _rpc(c, _token(app, ["matters:read"]), "tools/list")["tools"]}
    assert "create_contact" not in narrow and "run_conflict_check" not in narrow and "search" in narrow


def test_mcp_end_to_end_contact_matter_task_and_conflict(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES)
    who, err = _call(c, h, "create_contact", {"first_name": "Mcp", "last_name": "Client 20261005", "is_client": True})
    assert not err, who
    chk, err = _call(c, h, "run_conflict_check", {"names": ["Mcp Client 20261005", "Other Side 20261005"]})
    assert not err and chk["conflict_check"]["hit_count"] >= 1
    m, err = _call(c, h, "create_matter", {"client_id": who["contact"]["id"], "name": "Mcp Matter 20261005"})
    assert not err, m
    t, err = _call(c, h, "create_task", {"title": "Mcp task 20261005", "matter_id": m["matter"]["id"]})
    assert not err and t["task"]["matter_id"] == m["matter"]["id"]
    done, err = _call(c, h, "complete_task", {"task_id": t["task"]["id"]})
    assert not err and done["task"]["done"] is True
    found, err = _call(c, h, "search", {"query": "Mcp Client 20261005"})
    assert not err and found["results"]["contacts"]


def test_mcp_wrong_argument_type_says_so(app):
    c = app.test_client()
    payload, err = _call(c, _token(app, ALL_READ), "get_matter", {"matter_id": "abc"})
    assert err and "whole number" in payload["error"]
