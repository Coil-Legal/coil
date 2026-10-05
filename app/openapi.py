"""OpenAPI 3.1 description of Coil's REST API, served at /api/v1/openapi.json.

Written by hand as data rather than generated from the routes, because what an agent or an
automation tool needs from it is the meaning (which scope a call needs, what redaction
does, that invoices are only ever drafts), and that lives in the descriptions, not in the
URL map. tests/test_openapi.py checks that every documented path exists and every API route
is documented, so the two cannot drift apart silently.
"""
from .blueprints.api import ALL_SCOPES, RESOURCE_LABELS

ID = {"type": "integer"}
STR = {"type": "string"}
BOOL = {"type": "boolean"}
DATE = {"type": "string", "format": "date", "description": "YYYY-MM-DD"}
OBJ = {"type": "object", "additionalProperties": True}


def _q(name, schema, desc, required=False):
    return {"name": name, "in": "query", "required": required, "schema": schema, "description": desc}


def _id(name="id"):
    return {"name": name, "in": "path", "required": True, "schema": ID}


def _body(props, required=()):
    return {"required": True, "content": {"application/json": {"schema": {
        "type": "object", "properties": props, "required": list(required)}}}}


# (method, path, scope, summary, description, parameters, requestBody, success status)
OPS = [
    ("get", "/me", None, "Who this token is",
     "The token's owner, its scopes, its confidentiality mode and the firm. Call this first: it tells an "
     "agent whether client details are withheld.", [], None, 200),
    ("get", "/search", None, "Search the firm",
     "One query across contacts, matters, documents (names and extracted text), tasks and notes. Only the "
     "kinds this token may read are searched; `searched` lists them.",
     [_q("q", STR, "What to look for", True), _q("limit", ID, "Max results per kind, up to 50")], None, 200),
    ("get", "/matters", "matters:read", "List matters", "Newest first, up to 50.",
     [_q("q", STR, "Search number, name, case number or client"),
      _q("status", STR, "open (default), closed, pending or all")], None, 200),
    ("post", "/matters", "matters:write", "Open a matter",
     "For an existing contact, who becomes a client. Coil assigns the number. Run a conflict check first.",
     [], _body({"client_id": ID, "name": STR, "practice_area": STR, "description": STR,
                "billing_type": {"type": "string", "enum": ["flat", "hourly", "contingency", "hybrid"]}},
               ("client_id", "name")), 201),
    ("get", "/matters/{id}", "matters:read", "One matter", "With unbilled time and expense totals in cents.",
     [_id()], None, 200),
    ("get", "/contacts", "contacts:read", "List contacts",
     "Search by full or partial name, company or email, up to 50.", [_q("q", STR, "Search text")], None, 200),
    ("post", "/contacts", "contacts:write", "Add a contact",
     "A person needs first_name or last_name; a company needs company_name. Coil does not stop duplicates; "
     "search first.",
     [], _body({"kind": {"type": "string", "enum": ["person", "company"]}, "first_name": STR, "last_name": STR,
                "company_name": STR, "email": STR, "phone": STR, "address": STR, "notes": STR,
                "is_client": BOOL}), 201),
    ("get", "/contacts/{id}", "contacts:read", "One contact", "Full details and their matters.", [_id()], None, 200),
    ("get", "/time", "time:read", "List time entries", "With total minutes.",
     [_q("matter_id", ID, "Restrict to a matter"), _q("user_id", ID, "Restrict to a user"),
      _q("from", DATE, "From date"), _q("to", DATE, "To date"), _q("limit", ID, "Up to 200")], None, 200),
    ("post", "/time", "time:write", "Log time",
     "Whole minutes. A time entry becomes an invoice line, so confirm it with the user first.",
     [], _body({"matter_id": ID, "minutes": ID, "description": STR, "date": DATE, "billable": BOOL},
               ("matter_id", "minutes", "description")), 201),
    ("get", "/timer", "time:read", "The running timer", "Or null.", [], None, 200),
    ("post", "/timer/start", "time:write", "Start the timer", "On a matter.", [],
     _body({"matter_id": ID, "description": STR}, ("matter_id",)), 201),
    ("post", "/timer/stop", "time:write", "Stop the timer", "Saves it as a time entry.", [],
     _body({"description": STR}), 200),
    ("get", "/invoices", "invoices:read", "List invoices", "Amounts in integer cents.",
     [_q("status", STR, "draft, sent, partial, paid, void, or blank for all")], None, 200),
    ("post", "/invoices", "invoices:write", "Draft an invoice",
     "From every unbilled time entry, expense and due milestone on a matter. Only ever a draft: never "
     "submitted, approved, sent or paid through the API. The same entries cannot be billed twice.",
     [], _body({"matter_id": ID, "issued_on": DATE, "due_on": DATE}, ("matter_id",)), 201),
    ("get", "/invoices/{id}", "invoices:read", "One invoice", "With its lines. Amounts in cents.", [_id()], None, 200),
    ("get", "/tasks", "tasks:read", "List open tasks", "Soonest first.",
     [_q("matter_id", ID, "Restrict to a matter"), _q("due", STR, "today, overdue or week"),
      _q("mine", BOOL, "Only tasks assigned to the token owner")], None, 200),
    ("post", "/tasks", "tasks:write", "Add a task",
     "Court deadlines belong in Coil's deadline chains, which calculate from court rules.",
     [], _body({"title": STR, "matter_id": ID, "due_on": DATE,
                "kind": {"type": "string", "enum": ["task", "deadline", "court_date"]},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                "assignee_id": ID, "notes": STR}, ("title",)), 201),
    ("post", "/tasks/{id}/done", "tasks:write", "Complete or reopen a task", "done defaults to true.",
     [_id()], _body({"done": BOOL}), 200),
    ("post", "/conflicts", "conflicts:write", "Run a conflict check",
     "Checks names against contacts, parties, matters, notes, documents and leads, and stores the check. "
     "A hit is a possible conflict for a lawyer to review, not a decision.",
     [], _body({"names": {"type": "array", "items": STR}, "matter_id": ID, "contact_id": ID}, ("names",)), 201),
    ("get", "/conflicts/{id}", "conflicts:read", "One conflict check", "Its outcome and hits.", [_id()], None, 200),
    ("get", "/documents", "documents:read", "List documents", "Metadata only.",
     [_q("matter_id", ID, "Restrict to a matter"), _q("limit", ID, "Up to 200")], None, 200),
    ("get", "/documents/{id}", "documents:read", "One document",
     "Metadata and extracted text, up to 100,000 characters. Never the file bytes.", [_id()], None, 200),
    ("get", "/calendar", "calendar:read", "List calendar events", "From a date onwards.",
     [_q("matter_id", ID, "Restrict to a matter"), _q("from", DATE, "From date"),
      _q("limit", ID, "Up to 200")], None, 200),
    ("post", "/calendar", "calendar:write", "Add a calendar event",
     "For meetings and calls, not filing deadlines. starts_at is ISO 8601.",
     [], _body({"title": STR, "starts_at": {"type": "string", "format": "date-time"}, "matter_id": ID,
                "location": STR}, ("title", "starts_at")), 201),
    ("get", "/notes", "notes:read", "List notes", "Newest first.",
     [_q("matter_id", ID, "Restrict to a matter"), _q("limit", ID, "Up to 200")], None, 200),
    ("post", "/notes", "notes:write", "Add a note to a matter", "Attributed to the token owner.",
     [], _body({"matter_id": ID, "body": STR}, ("matter_id", "body")), 201),
    ("post", "/leads", "leads:write", "File an intake lead",
     "From a phone agent or answering service. Idempotent on external_id.",
     [], _body({"name": STR, "email": STR, "phone": STR, "matter_type": STR, "description": STR,
                "call_summary": STR, "transcript": {"type": "array", "items": OBJ}, "adverse_party": STR,
                "source": STR, "external_id": STR}, ("name",)), 201),
    ("post", "/capture", "time:write", "Send captured activity",
     "Activity segments from the browser extension, turned into time suggestions for review.",
     [], _body({"segments": {"type": "array", "items": OBJ}}), 201),
    ("get", "/capture/pending", "time:read", "Pending time suggestions", "How many are waiting for review.",
     [], None, 200),
]

INTRO = (
    "Coil's REST API. Every call carries `Authorization: Bearer <token>`. A token comes from Settings, "
    "API tokens, or from connecting an app through OAuth.\n\n"
    "**Scopes.** Each call needs one scope, shown on the operation. A token can never do more than the "
    "role of the person it belongs to.\n\n"
    "**Confidentiality.** A token is either `redacted` (the default) or `full`. Redacted tokens get ids, "
    "numbers, dates, amounts and statuses, but never a client's name, contact details or the substance of "
    "a matter (descriptions, time narratives, note bodies, document text): those come back as "
    "`[redacted]` or a label such as `Client #12`.\n\n"
    "**Not reachable at all.** Trust accounting, payments, users and permissions, firm settings and "
    "deletes are not part of this API, whatever the token's scopes.\n\n"
    "**Money** is integer cents. **Time** is whole minutes. Rate limit: about 120 calls a minute per token; "
    "a 429 carries Retry-After.\n\n"
    "The same tools are available to AI assistants over MCP at `/mcp`."
)


def spec(base_url, version="dev"):
    paths = {}
    for method, path, scope, summary, desc, params, body, ok in OPS:
        op = {"summary": summary, "description": desc + (f"\n\nScope: `{scope}`." if scope else ""),
              "operationId": (method + path.replace("/", "_").replace("{", "").replace("}", "")).strip("_"),
              "parameters": params,
              "responses": {str(ok): {"description": "Success",
                                      "content": {"application/json": {"schema": OBJ}}},
                            "400": {"$ref": "#/components/responses/Error"},
                            "401": {"$ref": "#/components/responses/Error"},
                            "403": {"$ref": "#/components/responses/Error"},
                            "404": {"$ref": "#/components/responses/Error"},
                            "429": {"$ref": "#/components/responses/Error"}},
              "security": [{"bearer": []}, {"oauth": [scope] if scope else []}]}
        if scope:
            op["tags"] = [scope.split(":")[0]]
        if body:
            op["requestBody"] = body
        paths.setdefault(path, {})[method] = op
    scopes = {s: f"{RESOURCE_LABELS.get(s.split(':')[0], s.split(':')[0])}: {s.split(':')[1]}" for s in ALL_SCOPES}
    return {
        "openapi": "3.1.0",
        "info": {"title": "Coil API", "version": version, "description": INTRO,
                 "license": {"name": "AGPL-3.0", "identifier": "AGPL-3.0-only"}},
        "servers": [{"url": base_url.rstrip("/") + "/api/v1"}],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "bearer": {"type": "http", "scheme": "bearer",
                           "description": "A Coil API token from Settings, API tokens."},
                "oauth": {"type": "oauth2", "description": "OAuth 2.1 with PKCE, for apps a user connects.",
                          "flows": {"authorizationCode": {
                              "authorizationUrl": base_url.rstrip("/") + "/oauth/authorize",
                              "tokenUrl": base_url.rstrip("/") + "/oauth/token",
                              "refreshUrl": base_url.rstrip("/") + "/oauth/token",
                              "scopes": scopes}}},
            },
            "responses": {"Error": {"description": "An error, in words an agent can relay to the user.",
                                    "content": {"application/json": {"schema": {
                                        "type": "object", "properties": {"error": STR, "status": ID}}}}}},
        },
    }
