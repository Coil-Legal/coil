"""MCP over HTTP at /mcp: the same tools as mcp/coil_mcp.py, for clients on the network.

What matters here is that the HTTP layer cannot widen anything. A token with no
time:write scope must not see log_time in tools/list, and calling it anyway must come back
as the API's own refusal, because every tool is dispatched through the REST API in-process
and the REST API is where the scopes live.

Own SQLite file. Run: .venv/bin/python -m pytest tests/test_mcp_http.py -q
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_mcp_http.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_mcp_http")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_mcp_http")


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(PDF_DIR, ignore_errors=True)
    env = dict(os.environ, DATABASE_URL=DB_URI, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="", SMTP_HOST="")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    out = subprocess.run([sys.executable, os.path.join(ROOT, "demo_data.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
                       "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": "",
                       "COIL_VERSION": "test"})


def _token(app, scopes, confidentiality="full"):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token, reset_rate_limits
    reset_rate_limits()
    with app.app_context():
        u = User.query.filter_by(email="owner@example.com").first()
        _, raw = create_token(u, "mcp test", scopes, confidentiality)
        db.session.commit()
    return {"Authorization": f"Bearer {raw}"}


def rpc(client, headers, method, params=None, id_=1):
    msg = {"jsonrpc": "2.0", "method": method}
    if id_ is not None:
        msg["id"] = id_
    if params is not None:
        msg["params"] = params
    return client.post("/mcp", json=msg, headers=headers)


def result(r):
    assert r.status_code == 200, r.data[:300]
    body = r.get_json()
    assert "error" not in body, body
    return body["result"]


def tool_payload(r):
    """The structured payload a tool call returned, plus whether it was flagged an error."""
    res = result(r)
    assert res["content"][0]["type"] == "text"
    assert json.loads(res["content"][0]["text"]) == res["structuredContent"], "text and structured must agree"
    return res["structuredContent"], res["isError"]


# --- the handshake --------------------------------------------------------------------------

def test_no_token_is_a_401_that_says_how_to_get_one(app):
    r = app.test_client().post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert r.status_code == 401
    assert "WWW-Authenticate" in r.headers
    assert "Settings, API tokens" in r.get_json()["error"]["message"]


def test_a_revoked_or_made_up_token_is_refused_the_same_way(app):
    r = app.test_client().post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"},
                               headers={"Authorization": "Bearer coil_not_a_real_token"})
    assert r.status_code == 401


def test_rate_limited_token_gets_429_not_401(app):
    """A valid token that has already spent its budget must not be told to send a token.

    _me() calls /api/v1/me to authenticate the MCP request itself; if that internal call
    comes back 429 because the token's own rate limit is already spent, the MCP layer once
    folded every non-200 status into a generic 401 "send an Authorization header", which is
    both the wrong status for a retryable condition and actively misleading (the token was
    fine, it was just out of budget).
    """
    import time
    from collections import deque
    from app.blueprints.api import _rate, _rate_lock, _effective_limit, hash_token
    from app.models import ApiToken
    h = _token(app, ["matters:read"])
    raw = h["Authorization"].split(" ", 1)[1]
    with app.app_context():
        tid = ApiToken.query.filter_by(token_hash=hash_token(raw)).first().id
        limit = _effective_limit()
    with _rate_lock:
        dq = _rate.setdefault(tid, deque())
        for _ in range(limit):
            dq.append(time.monotonic())
    r = app.test_client().post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}, headers=h)
    assert r.status_code == 429
    assert r.headers.get("Retry-After") == "60"
    assert "error" in r.get_json()


def test_initialize_announces_tools_and_tells_the_model_which_mode_it_is_in(app):
    h = _token(app, ["matters:read"], "redacted")
    res = result(rpc(app.test_client(), h, "initialize",
                     {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}))
    assert res["protocolVersion"] == "2025-06-18"
    assert "tools" in res["capabilities"]
    assert res["serverInfo"]["name"] == "coil"
    assert "WITHHELD mode" in res["instructions"], "a redacted token must be told so up front"


def test_an_unknown_protocol_version_gets_our_newest_not_an_error(app):
    h = _token(app, ["matters:read"])
    res = result(rpc(app.test_client(), h, "initialize", {"protocolVersion": "2099-01-01"}))
    assert res["protocolVersion"] == "2025-06-18"


def test_initialized_notification_is_accepted_silently(app):
    h = _token(app, ["matters:read"])
    r = rpc(app.test_client(), h, "notifications/initialized", id_=None)
    assert r.status_code == 202
    assert r.data == b""


def test_ping_and_unknown_method(app):
    h = _token(app, ["matters:read"])
    assert result(rpc(app.test_client(), h, "ping")) == {}
    r = rpc(app.test_client(), h, "no/such/method")
    assert r.get_json()["error"]["code"] == -32601


# --- scopes decide what a token can even see ------------------------------------------------

def test_tools_list_is_filtered_by_scope(app):
    c = app.test_client()
    read_only = {t["name"] for t in result(rpc(c, _token(app, ["matters:read", "time:read"]), "tools/list"))["tools"]}
    assert "list_matters" in read_only and "list_time" in read_only and "coil_status" in read_only
    assert "log_time" not in read_only, "a read-only token must not be shown a tool that writes"
    assert "list_invoices" not in read_only

    writer = {t["name"] for t in result(rpc(c, _token(app, ["time:read", "time:write"]), "tools/list"))["tools"]}
    assert "log_time" in writer and "start_timer" in writer


def test_calling_a_tool_the_token_cannot_see_is_refused_in_words(app):
    h = _token(app, ["matters:read"])
    payload, is_error = tool_payload(rpc(app.test_client(), h, "tools/call",
                                         {"name": "log_time", "arguments": {"matter_id": 1, "minutes": 6, "description": "x"}}))
    assert is_error
    assert "not allowed" in payload["error"]


def test_tool_schemas_are_valid_json_schema_objects(app):
    h = _token(app, ["matters:read", "time:write"])
    for t in result(rpc(app.test_client(), h, "tools/list"))["tools"]:
        s = t["inputSchema"]
        assert s["type"] == "object" and isinstance(s["properties"], dict)
        for req in s.get("required", []):
            assert req in s["properties"], f"{t['name']}: required {req} not in properties"


# --- the tools go through the REST API, redaction included ----------------------------------

def test_list_matters_returns_the_demo_practice(app):
    h = _token(app, ["matters:read"])
    payload, is_error = tool_payload(rpc(app.test_client(), h, "tools/call",
                                         {"name": "list_matters", "arguments": {"status": "all"}}))
    assert not is_error
    rows = payload.get("matters") or payload.get("items") or payload.get("results") or []
    assert any("Marchetti" in json.dumps(m) for m in rows), "the demo PI matter should be here"


def test_redacted_token_never_sees_a_client_name(app):
    h = _token(app, ["matters:read", "contacts:read"], "redacted")
    payload, _ = tool_payload(rpc(app.test_client(), h, "tools/call", {"name": "list_matters", "arguments": {"status": "all"}}))
    text = json.dumps(payload)
    assert "Marchetti" not in text and "Nordvale" not in text, "redaction is the API's job and must survive the transport"
    status, _ = tool_payload(rpc(app.test_client(), h, "tools/call", {"name": "coil_status", "arguments": {}}))
    assert status["client_details_withheld"] is True
    assert status["transport"] == "streamable-http"


def test_log_time_writes_through_the_api_and_reads_back(app):
    from app.extensions import db
    from app.models import Matter, TimeEntry
    h = _token(app, ["matters:read", "time:read", "time:write"])
    with app.app_context():
        mid = Matter.query.filter(Matter.name.like("%Marchetti%")).first().id
        before = TimeEntry.query.filter_by(matter_id=mid).count()
    payload, is_error = tool_payload(rpc(app.test_client(), h, "tools/call",
                                         {"name": "log_time", "arguments": {"matter_id": mid, "minutes": 12,
                                                                            "description": "TEST via mcp http"}}))
    assert not is_error, payload
    with app.app_context():
        assert TimeEntry.query.filter_by(matter_id=mid).count() == before + 1
        assert TimeEntry.query.filter_by(matter_id=mid).order_by(TimeEntry.id.desc()).first().minutes == 12


def test_missing_required_argument_is_a_tool_error_not_a_crash(app):
    h = _token(app, ["time:write"])
    payload, is_error = tool_payload(rpc(app.test_client(), h, "tools/call", {"name": "log_time", "arguments": {"minutes": 6}}))
    assert is_error and "matter_id" in payload["error"]


def test_readonly_user_cannot_write_even_with_a_write_scope(app):
    """The API's rule, surviving the transport: a person's role beats their token."""
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token, reset_rate_limits
    reset_rate_limits()
    with app.app_context():
        ro = User(email="ro-mcp@example.test", name="Read Only", role="readonly", is_active=True)
        ro.set_password("password123")
        db.session.add(ro)
        db.session.flush()
        _, raw = create_token(ro, "ro", ["notes:write", "matters:read"], "full")
        db.session.commit()
        from app.models import Matter
        mid = Matter.query.first().id
    h = {"Authorization": f"Bearer {raw}"}
    payload, is_error = tool_payload(rpc(app.test_client(), h, "tools/call",
                                         {"name": "add_note", "arguments": {"matter_id": mid, "body": "should not land"}}))
    assert is_error
    assert "Read-only" in payload["error"]


# --- transport edges -------------------------------------------------------------------------

def test_get_is_refused_with_an_explanation_and_delete_is_a_no_op(app):
    h = _token(app, ["matters:read"])
    c = app.test_client()
    r = c.get("/mcp", headers=h)
    assert r.status_code == 405 and "POST only" in r.get_json()["error"]
    assert c.delete("/mcp", headers=h).status_code == 204


def test_batch_from_an_older_client_is_answered_as_a_list(app):
    h = _token(app, ["matters:read"])
    r = app.test_client().post("/mcp", headers=h, json=[
        {"jsonrpc": "2.0", "id": 1, "method": "ping"},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ])
    assert r.status_code == 200
    out = r.get_json()
    assert [m["id"] for m in out] == [1, 2], "the notification produces no reply; the two requests do"


def test_non_json_body_is_a_parse_error(app):
    h = _token(app, ["matters:read"])
    r = app.test_client().post("/mcp", data="not json", headers={**h, "Content-Type": "application/json"})
    assert r.status_code == 400
    assert r.get_json()["error"]["code"] == -32700
