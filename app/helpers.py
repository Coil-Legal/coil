"""Shared helpers: auth decorators, CSRF, money formatting, template globals."""
from functools import wraps
from datetime import date, datetime
import secrets
from flask import session, redirect, url_for, request, abort, g, flash
from .extensions import db
from .models import User, Contact, Firm, now as utcnow


# ---- money ----
def cents_to_str(c, symbol="$"):
    c = int(c or 0)
    neg = c < 0
    c = abs(c)
    s = f"{symbol}{c // 100:,}.{c % 100:02d}"
    return f"({s})" if neg else s


# A single time entry longer than a day, or an invoice above this, is almost always a typo
# rather than a real figure. Neither is refused outright: a marathon trial day and a large
# settlement both exist. The user is asked to confirm, once, and then it goes through.
UNUSUAL_MINUTES = 24 * 60
UNUSUAL_INVOICE_CENTS = 1_000_000_00


def csv_safe(v):
    """Neutralise a spreadsheet formula hiding in exported data.

    Excel, LibreOffice and Sheets evaluate any cell whose text begins with = + @ - or a
    lone tab or carriage return. A contact named =cmd|'/c calc'!A1 therefore runs on the
    machine of whoever opens the export, and firms open every export they take. The cell
    is prefixed with an apostrophe, which those readers strip on display.

    A leading minus in front of a real number is left alone: trust disbursements and
    discounts are negative, and quoting them turns money columns into text that will not
    sum. Only a value that is not a number gets the treatment.
    """
    if not isinstance(v, str):
        return v
    if not v or v[0] not in "=+@-\t\r":
        return v
    try:
        float(v)
        return v
    except ValueError:
        return "'" + v


def parse_money(s):
    """'1,250.50' -> 125050. Blank -> 0."""
    if s is None:
        return 0
    s = str(s).replace("$", "").replace(",", "").strip()
    if not s:
        return 0
    neg = s.startswith("(") and s.endswith(")") or s.startswith("-")
    s = s.strip("()-")
    whole, _, frac = s.partition(".")
    frac = (frac + "00")[:2]
    v = int(whole or 0) * 100 + int(frac or 0)
    return -v if neg else v


CURRENCY_SYMBOLS = {"USD": "$", "CAD": "CA$", "GBP": "\u00a3", "EUR": "\u20ac", "AUD": "A$", "MXN": "MX$"}
CURRENCIES = list(CURRENCY_SYMBOLS)


def fmt_money(cents, code="USD"):
    """Like money() but with the symbol for the given ISO code. fmt_money(123456, "GBP") -> "\u00a31,234.56"."""
    code = (code or "USD").upper()
    symbol = CURRENCY_SYMBOLS.get(code, code + " ")
    return cents_to_str(cents, symbol)


def fmt_money_by_currency(totals):
    """{"USD": 123456, "EUR": 100} -> "$1,234.56 + \u20ac1.00". A raw sum across currencies with a single
    symbol misrepresents the total (see issues #60/#61); this keeps each currency's figure separate instead
    of converting or picking one. Empty input formats as zero USD, matching the single-currency case."""
    if not totals:
        return fmt_money(0)
    return " + ".join(fmt_money(cents, code) for code, cents in sorted(totals.items()))


def fmt_pct(v):
    """0.0 -> "0%", 25.0 -> "25%", 33.33 -> "33.33%". A contingency percent is stored as a
    float (see issue #131: a whole-number input rendered raw as "25.0%")."""
    v = v or 0
    return f"{v:g}%"


def fmt_pct_by_currency(pcts):
    """Like fmt_money_by_currency, but for a ratio (e.g. margin as % of revenue) that's already computed
    separately per currency rather than being a share of one combined total (see issue #69: profitability's
    margin % is meaningless once revenue is split by currency, same reason the revenue itself can't be
    summed). A currency with no revenue in range shows as a dash for that currency, matching the single-value
    case; an empty dict shows a single dash."""
    if not pcts:
        return "-"
    single = len(pcts) == 1
    parts = [("-" if v is None else f"{v:.1f}%") + ("" if single else f" {code}")
             for code, v in sorted(pcts.items())]
    return " + ".join(parts)


def parse_date(s, default=None):
    if not s:
        return default
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return default


def parse_minutes(s):
    """Accept '1.5' (hours), '1:30', '90m', '0.1'. Returns minutes."""
    s = str(s or "").strip().lower()
    if not s:
        return 0
    if s.endswith("m"):
        return int(float(s[:-1]))
    if ":" in s:
        h, m = s.split(":", 1)
        return int(h or 0) * 60 + int(m or 0)
    if s.endswith("h"):
        s = s[:-1]
    return int(round(float(s) * 60))


# ---- auth ----
def current_user():
    if "user" not in g:
        uid = session.get("user_id")
        g.user = db.session.get(User, uid) if uid else None
    if g.user is not None and (not g.user.is_active or session.get("sv") != g.user.session_version):
        session.pop("user_id", None)
        session.pop("sv", None)
        session.pop("_new_api_token", None)
        session.pop("_csrf", None)
        g.user = None
    return g.user


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not current_user():
            return redirect(url_for("auth.login", next=request.path))
        return f(*a, **kw)
    return wrapper


def owner_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        u = current_user()
        if not u:
            return redirect(url_for("auth.login", next=request.path))
        if u.role != "owner":
            abort(403)
        return f(*a, **kw)
    return wrapper


def permission_required(name):
    """Explicit check against app.permissions: @permission_required("trust"). Owners always pass."""
    def deco(f):
        @wraps(f)
        def wrapper(*a, **kw):
            u = current_user()
            if not u:
                return redirect(url_for("auth.login", next=request.path))
            from .permissions import has_permission
            if not has_permission(u, name):
                abort(403)
            return f(*a, **kw)
        return wrapper
    return deco


def portal_contact():
    if "portal_contact" in g:
        return g.portal_contact
    cid = session.get("portal_contact_id")
    g.portal_contact = db.session.get(Contact, cid) if cid else None
    return g.portal_contact


def portal_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not portal_contact():
            return redirect(url_for("portal.login"))
        return f(*a, **kw)
    return wrapper


# ---- CSRF ----
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_urlsafe(24)
    return session["_csrf"]


def csrf_field():
    from markupsafe import Markup
    return Markup(f'<input type="hidden" name="_csrf" value="{csrf_token()}">')


CSRF_EXEMPT_PREFIXES = ("/webhooks/", "/intake/submit", "/track/", "/sign/", "/pay/", "/p/", "/portal/", "/api/v1/",
                        "/mcp",  # bearer-authenticated JSON-RPC, same footing as the API
                        # OAuth machine endpoints (blueprints/oauth.py). They never read the session.
                        # The consent POST at /oauth/authorize is deliberately NOT here.
                        "/oauth/token", "/oauth/register", "/oauth/revoke", "/.well-known/")


def check_csrf():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    for p in CSRF_EXEMPT_PREFIXES:
        if request.path.startswith(p):
            return
    tok = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
    if not tok or tok != session.get("_csrf"):
        abort(400, "CSRF token missing or invalid")


def emit_event(name, payload):
    """Queue one outgoing-webhook delivery per active Webhook subscribed to `name`; the HTTP attempts
    run on a background thread so a slow or dead endpoint never blocks the caller. Returns the
    WebhookDelivery ids created. Call it after your own commit: it writes through its own short-lived
    session so it is safe from SQLAlchemy after_commit hooks too. Implemented in
    app/blueprints/webhooks_out.py; this is the import-friendly entry point."""
    from .blueprints.webhooks_out import deliver_event
    return deliver_event(name, payload)


def client_ip():
    xf = request.headers.get("X-Forwarded-For", "")
    return (xf.split(",")[0].strip() if xf else request.remote_addr) or ""


# ---- SQLite write contention ----
# Two requests committing at nearly the same moment can collide in SQLite even in WAL mode:
# plain contention (SQLITE_BUSY, SQLITE_LOCKED) or a snapshot a concurrent commit made stale
# mid-transaction (SQLITE_BUSY_SNAPSHOT). All three are transient and normally clear on the very
# next attempt with a fresh transaction, so they are worth a few quick retries rather than an
# unhandled 500 for whichever request loses the race.
LOCK_RETRIES = 5
_LOCK_SQLITE_CODES = {5, 6, 517}  # SQLITE_BUSY, SQLITE_LOCKED, SQLITE_BUSY_SNAPSHOT


def is_lock_error(e):
    orig = getattr(e, "orig", None)
    if getattr(orig, "sqlite_errorcode", None) in _LOCK_SQLITE_CODES:
        return True
    msg = str(e).lower()
    return "database is locked" in msg or "database table is locked" in msg


def _mike_url():
    """Where the optional Mike AI workbench lives, or "" when a firm has not set one up.

    Resolved through the integrations layer so a self-hoster sets MIKE_URL in .env and a
    hosted firm sets it under Settings, Integrations. Only http(s) is ever rendered into a
    link, so a stray value cannot become a javascript: href in the navigation.
    """
    from .integrations import setting
    v = (setting("MIKE_URL") or "").strip()
    return v if v.startswith(("http://", "https://")) else ""


def _day_type_label(key):
    """One source for the court-rule unit labels.

    The task detail page used to carry its own copy of this mapping, so a unit added to
    the rules blueprint rendered there as the raw key. Import it instead.
    """
    from .blueprints.rules import DAY_TYPES
    return dict(DAY_TYPES).get(key, key)


def _tool_on(key):
    """Template global: is this firm using the tool? See app/tools.py."""
    from .tools import tool_enabled
    return tool_enabled(key)


def register_template_globals(app):
    app.jinja_env.globals.update(
        money=cents_to_str, csrf=csrf_field, current_user=current_user, portal_contact=portal_contact,
        firm=lambda: Firm.get(), today=date.today, now=utcnow,
        mike_url=_mike_url, day_type_label=_day_type_label, tool_on=_tool_on,
    )
    app.jinja_env.filters["money"] = cents_to_str
    app.jinja_env.filters["cur"] = fmt_money
    app.jinja_env.filters["curmix"] = fmt_money_by_currency
    app.jinja_env.filters["pctmix"] = fmt_pct_by_currency
    app.jinja_env.filters["pct"] = fmt_pct
    app.jinja_env.filters["hours"] = lambda m: f"{(m or 0) / 60:.2f}"
    app.jinja_env.filters["d"] = lambda v: v.strftime("%b %-d, %Y") if v else ""
    app.jinja_env.filters["dt"] = lambda v: v.strftime("%b %-d, %Y %-I:%M %p") if v else ""
    app.jinja_env.filters["iso"] = lambda v: v.isoformat() if v else ""
