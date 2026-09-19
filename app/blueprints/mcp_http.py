"""MCP over HTTP, served by Coil itself at /mcp.

mcp/coil_mcp.py is a bridge that runs beside a desktop assistant, holds one person's
token, and calls the REST API. That is right for a laptop and wrong for anything that
connects over the network: a web tool such as Mike (an open-source legal AI workbench
that speaks MCP as a client) cannot reach a stdio process, and running the bridge as a
shared service would mean one fixed token for everyone, which throws away the per-token
scopes and redaction that are the whole security model.

So this is the same set of tools, spoken over the Streamable HTTP transport, inside the
app. Every request carries the caller's own API token as a bearer, exactly as Mike's
"add a connector, paste the URL and a token" pathway sends it.

Two decisions worth knowing:

1. Nothing here checks a token or reads the database. Authentication is an internal
   request to /api/v1/me with the caller's header, and every tool is an internal request
   to the REST endpoint it maps to, through Werkzeug's in-process client. Scopes,
   redaction, rate limiting and the wording of every refusal therefore come from the one
   code path that already has the tests, and this file cannot drift from it or widen it.

2. Responses are plain JSON, never an event stream. The transport allows a server to
   answer a POST with a single JSON body, and every Coil tool is request-and-response,
   so there is nothing to stream. GET, which opens a server-to-client stream, is refused
   with an explanation. No session id is issued: the token is the session.
"""
import json
import logging
from flask import Blueprint, request, jsonify, current_app

bp = Blueprint("mcp_http", __name__, url_prefix="/mcp")
log = logging.getLogger("coil.mcp")

PROTOCOL_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_NAME = "coil"

# JSON-RPC error codes
PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS, INTERNAL = -32700, -32600, -32601, -32602, -32603

REDACTED_NOTE = (
    "IMPORTANT: this token runs in WITHHELD mode. Coil removes client identities and the "
    "substance of matters before they reach you. Names like 'Client #4', 'Matter #7' and the "
    "value '[redacted]' are placeholders, NOT real data. Never present them as a client's name, "
    "never guess what they stand for, and if the user needs the real detail, tell them to look "
    "in Coil or to issue a token that sends everything."
)
FULL_NOTE = (
    "This token returns unredacted client data. Treat everything you see as confidential "
    "client information and do not repeat it outside this conversation."
)


def _s(desc, **extra):
    return {"type": "string", "description": desc, **extra}


def _i(desc, **extra):
    return {"type": "integer", "description": desc, **extra}


def _b(desc, **extra):
    return {"type": "boolean", "description": desc, **extra}


# Every tool the bridge offers, as data. `scope` gates whether the token sees it;
# `call` maps the arguments onto the REST request. Descriptions are the bridge's own.
TOOLS = [
    {"name": "list_matters", "scope": "matters:read",
     "description": "List matters. status is open, closed, pending or all.",
     "props": {"query": _s("Search text", default=""), "status": _s("open, closed, pending or all", default="open"),
               "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/matters", {"q": a.get("query", ""), "status": a.get("status", "open"),
                                            "limit": a.get("limit", 50)}, None)},
    {"name": "get_matter", "scope": "matters:read",
     "description": "One matter in full, by its numeric id (not its M- number).",
     "props": {"matter_id": _i("Numeric matter id")}, "required": ["matter_id"],
     "call": lambda a: ("GET", f"/matters/{int(a['matter_id'])}", None, None)},
    {"name": "list_contacts", "scope": "contacts:read",
     "description": "List contacts and clients.",
     "props": {"query": _s("Search text", default=""), "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/contacts", {"q": a.get("query", ""), "limit": a.get("limit", 50)}, None)},
    {"name": "list_time", "scope": "time:read",
     "description": "Time entries, with the total minutes. Dates are YYYY-MM-DD.",
     "props": {"matter_id": _i("Restrict to a matter", default=0), "date_from": _s("YYYY-MM-DD", default=""),
               "date_to": _s("YYYY-MM-DD", default=""), "limit": _i("Max rows", default=100)},
     "call": lambda a: ("GET", "/time", _drop({"matter_id": a.get("matter_id") or None, "from": a.get("date_from") or None,
                                               "to": a.get("date_to") or None, "limit": a.get("limit", 100)}), None)},
    {"name": "get_timer", "scope": "time:read",
     "description": "The running timer, if there is one.", "props": {},
     "call": lambda a: ("GET", "/timer", None, None)},
    {"name": "log_time", "scope": "time:write",
     "description": ("Log a time entry. minutes is a whole number; date defaults to today.\n\n"
                     "Read the description back to the user before calling this. Time entries become "
                     "invoices, and a wrong one is a billing error rather than a typo."),
     "props": {"matter_id": _i("Numeric matter id"), "minutes": _i("Whole minutes"), "description": _s("What was done"),
               "date": _s("YYYY-MM-DD, default today", default=""), "billable": _b("Billable", default=True)},
     "required": ["matter_id", "minutes", "description"],
     "call": lambda a: ("POST", "/time", None, {"matter_id": a["matter_id"], "minutes": a["minutes"],
                                                "description": a["description"], "date": a.get("date") or None,
                                                "billable": a.get("billable", True)})},
    {"name": "start_timer", "scope": "time:write",
     "description": "Start the timer on a matter.",
     "props": {"matter_id": _i("Numeric matter id"), "description": _s("What is being done", default="")},
     "required": ["matter_id"],
     "call": lambda a: ("POST", "/timer/start", None, {"matter_id": a["matter_id"], "description": a.get("description", "")})},
    {"name": "stop_timer", "scope": "time:write",
     "description": "Stop the running timer and save it as a time entry.",
     "props": {"description": _s("What was done", default="")},
     "call": lambda a: ("POST", "/timer/stop", None, {"description": a.get("description", "")})},
    {"name": "list_invoices", "scope": "invoices:read",
     "description": "Invoices. status is draft, sent, partial, paid or void. Amounts are cents.",
     "props": {"status": _s("draft, sent, partial, paid, void or blank for all", default=""), "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/invoices", {"status": a.get("status", ""), "limit": a.get("limit", 50)}, None)},
    {"name": "draft_invoice", "scope": "invoices:write",
     "description": ("Draft an invoice for every unbilled time entry, expense and due milestone on a matter. "
                     "Dates are YYYY-MM-DD; issued_on defaults to today, due_on to issued_on.\n\n"
                     "This only ever creates a draft. It never submits, approves or sends. Read the totals "
                     "back to the user before anyone opens the invoice in Coil."),
     "props": {"matter_id": _i("Numeric matter id"), "issued_on": _s("YYYY-MM-DD", default=""), "due_on": _s("YYYY-MM-DD", default="")},
     "required": ["matter_id"],
     "call": lambda a: ("POST", "/invoices", None, {"matter_id": a["matter_id"], "issued_on": a.get("issued_on") or None,
                                                    "due_on": a.get("due_on") or None})},
    {"name": "list_tasks", "scope": "tasks:read",
     "description": "Tasks and deadlines.",
     "props": {"matter_id": _i("Restrict to a matter", default=0), "done": _b("Completed ones instead of open", default=False),
               "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/tasks", _drop({"matter_id": a.get("matter_id") or None, "limit": a.get("limit", 50),
                                                "done": "true" if a.get("done") else "false"}), None)},
    {"name": "list_documents", "scope": "documents:read",
     "description": "Documents on a matter. Metadata only; Coil never sends file contents here.",
     "props": {"matter_id": _i("Restrict to a matter", default=0), "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/documents", _drop({"matter_id": a.get("matter_id") or None, "limit": a.get("limit", 50)}), None)},
    {"name": "list_events", "scope": "calendar:read",
     "description": "Calendar events from a date onwards. date_from is YYYY-MM-DD.",
     "props": {"matter_id": _i("Restrict to a matter", default=0), "date_from": _s("YYYY-MM-DD", default=""), "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/calendar", _drop({"matter_id": a.get("matter_id") or None, "from": a.get("date_from") or None,
                                                   "limit": a.get("limit", 50)}), None)},
    {"name": "create_event", "scope": "calendar:write",
     "description": ("Add a calendar event. starts_at is ISO 8601, e.g. 2026-09-08T14:30:00.\n\n"
                     "Court dates and deadlines belong in Coil's own deadline chains, which calculate from "
                     "court rules. Use this for meetings and calls, not for a filing deadline."),
     "props": {"title": _s("Event title"), "starts_at": _s("ISO 8601 start"), "matter_id": _i("Matter, optional", default=0),
               "location": _s("Location", default="")},
     "required": ["title", "starts_at"],
     "call": lambda a: ("POST", "/calendar", None, {"title": a["title"], "starts_at": a["starts_at"],
                                                    "matter_id": a.get("matter_id") or None, "location": a.get("location", "")})},
    {"name": "list_notes", "scope": "notes:read",
     "description": "Notes on a matter.",
     "props": {"matter_id": _i("Restrict to a matter", default=0), "limit": _i("Max rows", default=50)},
     "call": lambda a: ("GET", "/notes", _drop({"matter_id": a.get("matter_id") or None, "limit": a.get("limit", 50)}), None)},
    {"name": "add_note", "scope": "notes:write",
     "description": "Add a note to a matter. It is attributed to the token's owner.",
     "props": {"matter_id": _i("Numeric matter id"), "body": _s("The note")}, "required": ["matter_id", "body"],
     "call": lambda a: ("POST", "/notes", None, {"matter_id": a["matter_id"], "body": a["body"]})},
    {"name": "create_lead", "scope": "leads:write",
     "description": "File a new intake lead. It lands in the intake pipeline for a human to triage.",
     "props": {"name": _s("Full name"), "email": _s("Email", default=""), "phone": _s("Phone", default=""),
               "matter_type": _s("What kind of matter", default=""), "message": _s("What they said", default="")},
     "required": ["name"],
     "call": lambda a: ("POST", "/leads", None, {"name": a["name"], "email": a.get("email", ""), "phone": a.get("phone", ""),
                                                 "matter_type": a.get("matter_type", ""), "message": a.get("message", "")})},
    {"name": "coil_status", "scope": None,
     "description": ("What this connection can see and do, and whether client details are withheld.\n\n"
                     "Worth calling first: it says which mode you are in, and the user may not know."),
     "props": {}, "call": None},
]
BY_NAME = {t["name"]: t for t in TOOLS}


def _drop(d):
    return {k: v for k, v in d.items() if v is not None}


def _schema(tool):
    return {"type": "object", "properties": tool["props"], "required": tool.get("required", []),
            "additionalProperties": False}


# ------------------------------------------------------------------ internal calls

def _internal(method, path, params=None, body=None):
    """Call the REST API in-process with the caller's own Authorization header.

    Returns (status, parsed json or {"error": ...}). Never raises, so a refusal reaches
    the model as words rather than as a dead turn.
    """
    auth = request.headers.get("Authorization", "")
    with current_app.test_client() as c:
        r = c.open("/api/v1" + path, method=method, query_string=params or None, json=body,
                   headers={"Authorization": auth, "X-Forwarded-For": request.remote_addr or "",
                            "User-Agent": "coil-mcp-http/1.0"})
    try:
        data = r.get_json(silent=True)
    except Exception:  # noqa: BLE001
        data = None
    if data is None:
        data = {"error": f"Coil returned {r.status_code}."}
    return r.status_code, data


def _me():
    """Who is calling, from the token.

    Returns (status, me-dict-or-None). status is what /api/v1/me itself answered:
    401 for a missing or bad token, 429 if the token's own rate limit was already spent
    finding that out, 200 with the token/user/firm otherwise. The caller needs the real
    status because a 429 must reach the client as a 429, not get folded into a generic
    401 that tells someone to send a token they already sent.
    """
    if not request.headers.get("Authorization", "").startswith("Bearer "):
        return 401, None
    status, me = _internal("GET", "/me")
    if status != 200 or "token" not in me:
        return status, None
    return status, me


def _instructions(me):
    firm = me.get("firm", {}).get("name", "this firm")
    who = me.get("user", {}).get("name", "the token owner")
    mode = me.get("token", {}).get("confidentiality", "full")
    return (f"Practice management for {firm}, acting as {who}. Matters are addressed by their number, "
            f"like M-1001. Money is in integer cents. Time is in minutes.\n\n"
            + (REDACTED_NOTE if mode == "redacted" else FULL_NOTE))


def _visible_tools(me):
    scopes = set(me.get("token", {}).get("scopes") or [])
    return [t for t in TOOLS if t["scope"] is None or t["scope"] in scopes]


# ------------------------------------------------------------------ JSON-RPC

def _ok(id_, result):
    return {"jsonrpc": "2.0", "id": id_, "result": result}


def _err(id_, code, message, data=None):
    e = {"code": code, "message": message}
    if data is not None:
        e["data"] = data
    return {"jsonrpc": "2.0", "id": id_, "error": e}


def _tool_result(payload, is_error=False):
    """MCP tool results carry text for every client and structured content for the ones
    that read it. The text IS the JSON, so nothing is lost either way."""
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, default=str)}],
            "structuredContent": payload if isinstance(payload, dict) else {"result": payload},
            "isError": bool(is_error)}


def _handle(msg, me):
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return _err(None, INVALID_REQUEST, "Expected a JSON-RPC 2.0 object.")
    method = msg.get("method")
    id_ = msg.get("id")
    params = msg.get("params") or {}
    is_notification = "id" not in msg

    if method == "notifications/initialized" or (is_notification and str(method).startswith("notifications/")):
        return None                                  # acknowledged with an empty 202

    if method == "initialize":
        asked = str(params.get("protocolVersion") or "")
        version = asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0]
        return _ok(id_, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "version": current_app.config.get("COIL_VERSION", "dev")},
            "instructions": _instructions(me),
        })

    if method == "ping":
        return _ok(id_, {})

    if method == "tools/list":
        return _ok(id_, {"tools": [{"name": t["name"], "description": t["description"], "inputSchema": _schema(t)}
                                   for t in _visible_tools(me)]})

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        tool = BY_NAME.get(name)
        if not tool or tool not in _visible_tools(me):
            # The same wording the REST API uses for a scope it lacks, so a model that has
            # seen one refusal recognises the other.
            return _ok(id_, _tool_result({"error": f"Unknown tool or this token is not allowed to use it: {name}"}, True))
        if not isinstance(args, dict):
            return _err(id_, INVALID_PARAMS, "arguments must be an object.")
        missing = [r for r in tool.get("required", []) if r not in args]
        if missing:
            return _ok(id_, _tool_result({"error": f"Missing required argument(s): {', '.join(missing)}"}, True))
        if tool["call"] is None:                     # coil_status
            tok = me.get("token", {})
            return _ok(id_, _tool_result({
                "firm": me.get("firm", {}).get("name"), "acting_as": me.get("user", {}).get("name"),
                "instance": request.host_url.rstrip("/"), "confidentiality": tok.get("confidentiality", "full"),
                "client_details_withheld": tok.get("confidentiality") == "redacted",
                "scopes": sorted(tok.get("scopes") or []), "note": tok.get("note", ""),
                "transport": "streamable-http",
            }))
        try:
            m, path, q, body = tool["call"](args)
        except (KeyError, TypeError, ValueError) as e:
            return _ok(id_, _tool_result({"error": f"Bad arguments: {e}"}, True))
        status, data = _internal(m, path, q, body)
        return _ok(id_, _tool_result(data, is_error=status >= 400))

    if is_notification:
        return None
    return _err(id_, METHOD_NOT_FOUND, f"Method not found: {method}")


# ------------------------------------------------------------------ routes

@bp.route("", methods=["POST"])
@bp.route("/", methods=["POST"])
def rpc():
    status, me = _me()
    if me is None:
        if status == 429:
            resp = jsonify(_err(None, -32000, "Rate limit reached on this token. Wait and retry."))
            resp.status_code = 429
            resp.headers["Retry-After"] = "60"
            return resp
        resp = jsonify(_err(None, -32001, "Send an Authorization: Bearer <Coil API token> header. "
                                          "Create one in Coil at Settings, API tokens."))
        resp.status_code = 401
        resp.headers["WWW-Authenticate"] = 'Bearer realm="coil-mcp"'
        return resp
    try:
        payload = request.get_json(force=True, silent=False)
    except Exception:  # noqa: BLE001
        return jsonify(_err(None, PARSE_ERROR, "Body must be JSON.")), 400

    if isinstance(payload, list):                    # a batch, from an older client
        out = [r for r in (_handle(m, me) for m in payload) if r is not None]
        if not out:
            return ("", 202)
        return jsonify(out)
    result = _handle(payload, me)
    if result is None:
        return ("", 202)
    return jsonify(result)


@bp.route("", methods=["GET"])
@bp.route("/", methods=["GET"])
def stream_refused():
    """GET opens a server-to-client event stream. Coil has nothing to push, so say so
    rather than hanging a connection open."""
    return jsonify({"error": "This MCP endpoint answers POST only; it does not open a server event stream. "
                             "Point your client at the same URL and it will work."}), 405


@bp.route("", methods=["DELETE"])
@bp.route("/", methods=["DELETE"])
def end_session():
    return ("", 204)                                 # stateless: nothing to end
