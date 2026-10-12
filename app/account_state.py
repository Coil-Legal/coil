"""Hosted account lifecycle: active, suspended (paused) or closed.

Set by the operator, never by the firm: COIL_ACCOUNT_STATE in the firm's .env, changed
with ops/firm-state.sh, which recreates the container so the new value takes effect.
docs/OPERATIONS.md has the policy. There is no billing: hosted firms are free, so these
states exist for cancellation, for a firm that asks to pause, and for an operator who has
to stop an account without losing its data.

active     normal.
suspended  the firm signs in and reads everything, and can always take its data with it.
           Every state-changing request is refused with HTTP 423 Locked. Client-facing
           links (pay, sign, portal, the public intake form) show a polite "temporarily
           unavailable" page with HTTP 503, inbound provider webhooks get 503 so the
           provider retries later, and the cron jobs that send, charge or change records
           skip with a logged notice.
closed     only sign in, sign out, the owner's export page (/settings/export), /health,
           /health/ready and static files work. Everything else shows the closed page.

Why 423 for a refused write, not 403: 403 already means "your role cannot do this" in
Coil (app/permissions.py). A paused account is not a permission problem, and the person
seeing it should not go asking the owner for a role change. 423 Locked says the resource
exists and the request was understood but is locked right now, which is exactly the
situation, and it lets logs, the QA bots and API clients tell the two apart.

Why 503 for inbound webhooks: Stripe and most providers treat any non-2xx as a failed
delivery and retry with backoff (Stripe for up to three days), so a short pause loses
nothing and the events land after reactivation. Accepting them would record payments and
messages in an account that is supposed to be frozen. Twilio does not retry inbound texts;
they stay visible in the Twilio console. docs/OPERATIONS.md says what to replay.

An unrecognised value is treated as suspended and logged: a typo must not silently leave
an account the operator meant to pause fully writable, and suspended still lets the firm
read and export everything.
"""
import logging
import re
from datetime import date

from flask import current_app, has_request_context, jsonify, render_template, request

log = logging.getLogger("account_state")

STATES = ("active", "suspended", "closed")
CONTACT_EMAIL = "hello@coil.legal"
EXPORT_PATH = "/settings/export"

READ_METHODS = ("GET", "HEAD", "OPTIONS")

# Work in every state. /settings/export is the owner's way out with the firm's data; the
# owner-only rule for it is app/permissions.py's, not this module's.
ALWAYS_ALLOWED = ("/static", "/health", "/login", "/logout", EXPORT_PATH,
                  "/manifest.webmanifest", "/sw.js", "/offline", "/favicon.ico")

# Pages the firm's clients and website visitors reach, not the firm's own staff.
CLIENT_PREFIXES = ("/p/", "/pay/", "/sign/", "/portal", "/intake/form", "/intake/submit")
WEBHOOK_PREFIX = "/webhooks/"
TRACK_PREFIX = "/track/"
# Bearer-token machine endpoints: they get JSON, not an HTML page.
MACHINE_PREFIXES = ("/api/", "/mcp", "/oauth/token", "/oauth/register", "/oauth/revoke", "/.well-known/")
# Token refresh and revocation keep a read-only connected app working and let a firm cut
# one off. They change credentials, not firm records, so a paused account allows them.
SUSPENDED_MACHINE_WRITES = ("/oauth/token", "/oauth/revoke")

_SELF_EDIT = re.compile(r"^/settings/users/(\d+)/edit/?$")

# CLI commands that send email or texts, charge cards, place calls or change records.
# They skip while an account is not active. backup, known_schema and anything else
# (an export, for example) still run, because those are how the data gets out.
PAUSED_CLI_SKIPS = frozenset({"agenda", "reminders", "interest", "emailin", "sequences", "webhooks",
                              "monthly_invoicing", "case_audit", "payment_plans", "voice_reminders"})

_warned = set()


def _matches(path, prefixes):
    for p in prefixes:
        if p.endswith("/"):
            if path.startswith(p):
                return True
        elif path == p or path.startswith(p + "/"):
            return True
    return False


def current_state(config=None):
    config = config if config is not None else current_app.config
    raw = str(config.get("COIL_ACCOUNT_STATE") or "active").strip().lower()
    if raw in STATES:
        return raw
    if raw not in _warned:
        _warned.add(raw)
        log.error("COIL_ACCOUNT_STATE=%r is not one of %s; treating the account as suspended", raw, ", ".join(STATES))
    return "suspended"


def retain_until(config=None):
    config = config if config is not None else current_app.config
    raw = str(config.get("COIL_ACCOUNT_CLOSED_RETAIN_UNTIL") or "").strip()
    try:
        return date.fromisoformat(raw) if raw else None
    except ValueError:
        return None


def state_message(state=None, config=None):
    state = state or current_state(config)
    if state == "suspended":
        return (f"This account is paused. You can view and export your data. "
                f"Contact {CONTACT_EMAIL} to reactivate.")
    if state == "closed":
        until = retain_until(config)
        when = f" until {until:%B} {until.day}, {until.year}" if until else ""
        return (f"This account is closed. The owner can still sign in and download all firm data{when}. "
                f"Contact {CONTACT_EMAIL} with any questions.")
    return ""


def _export_link(state):
    """The export page when this build has it; the CSV exports page while only paused."""
    try:
        rules = {r.rule for r in current_app.url_map.iter_rules()}
    except Exception:  # noqa: BLE001
        rules = set()
    if EXPORT_PATH in rules:
        return EXPORT_PATH
    if state == "suspended" and "/exports" in rules:
        return "/exports"
    return None


def _user():
    if not has_request_context():
        return None
    try:
        from .helpers import current_user
        return current_user()
    except Exception:  # noqa: BLE001
        return None


def banner():
    """Template global: {"state", "message", "export_url"} while not active, else None."""
    try:
        state = current_state()
    except Exception:  # noqa: BLE001
        return None
    if state == "active":
        return None
    user = _user()
    is_owner = bool(user and user.role == "owner")
    export_url = _export_link(state) if is_owner else None
    return {"state": state, "message": state_message(state), "export_url": export_url,
            "signed_in": bool(user)}


def _blocked_page(state, status):
    info = banner() or {}
    return render_template("account/blocked.html", state=state, message=state_message(state),
                           export_url=info.get("export_url"), signed_in=info.get("signed_in"),
                           hide_account_banner=True), status


def _client_page(state):
    status = 503 if state == "suspended" else 410
    response = render_template("account/unavailable.html", state=state, hide_account_banner=True)
    headers = {"Retry-After": "86400"} if state == "suspended" else {}
    return response, status, headers


def _machine_refusal(state):
    response = jsonify({"error": f"account_{state}", "message": state_message(state)})
    response.status_code = 423
    return response


def guard():
    """before_request: apply the account state. Does nothing while the account is active."""
    try:
        state = current_state()
    except Exception:  # noqa: BLE001
        return None
    if state == "active":
        return None
    path = request.path or "/"
    method = request.method
    if _matches(path, ALWAYS_ALLOWED):
        return None
    if path.startswith(WEBHOOK_PREFIX):
        return jsonify({"error": f"account_{state}", "retry": state == "suspended"}), 503, {"Retry-After": "3600"}
    if path.startswith(TRACK_PREFIX):
        return "", 204   # an email open pixel; recording it would be a write
    if _matches(path, CLIENT_PREFIXES):
        return _client_page(state)
    machine = _matches(path, MACHINE_PREFIXES)
    if state == "closed":
        return _machine_refusal(state) if machine else _blocked_page(state, 423)
    # suspended
    if method in READ_METHODS:
        return None
    if machine:
        if _matches(path, SUSPENDED_MACHINE_WRITES):
            return None
        return _machine_refusal(state)
    # A paused firm can still change its own password (and name or email) on its own
    # account page, so a leaked password can be rotated without reactivating.
    m = _SELF_EDIT.match(path)
    if m:
        user = _user()
        if user and int(m.group(1)) == user.id:
            return None
    return _blocked_page(state, 423)


def cli_skip_reason(command, config=None):
    """The notice to print when a cron command must not run in this account state, else None."""
    state = current_state(config)
    if state == "active" or command not in PAUSED_CLI_SKIPS:
        return None
    return (f"{command}: skipped, the account is {state} (COIL_ACCOUNT_STATE={state}). "
            f"Nothing was sent, charged or changed.")


def init_app(app):
    app.before_request(guard)
    app.add_template_global(banner, "account_banner")
