"""Per-firm tool switches: which parts of Coil each firm sees.

Every firm runs the same code. What differs between firms is which tools are switched on,
and that choice is stored on the firm, not in the code. Turning a tool off hides it from
the menu, the dashboard and the matter tabs, and closes its staff pages. Nothing is
deleted: the records stay in the database and come back the moment the tool is switched
on again.

This is also how a feature built for one firm reaches every firm without being forced on
any of them. A new tool is registered here with ``default_on=False``. It ships to every
firm in the next update, sits switched off, and the firm that asked for it turns it on.
If it turns out everyone wants it, flip the default. See docs/CUSTOMIZING.md.

Three things are deliberately never switchable:

* Core tools (dashboard, contacts, matters, settings, audit log, exports and the rest in
  CORE below). A firm cannot run without them, and exports are how a firm leaves, which
  must never be one checkbox away from disappearing.
* Links already sent to clients. Signing links, pay links, public invoice links and
  tracking pixels keep working when their tool is off, because the client was promised
  them. Turning a tool off is a decision about the firm's own screens.
* Inbound webhooks and the API. Twilio, Stripe and integrations keep posting and are
  recorded, so switching a tool off never silently loses a text or a payment. The API
  and MCP carry their own token scopes.

Stored as ``Firm.tool_overrides``: a JSON object of ``{tool_key: bool}`` holding only the
choices that differ from each tool's default, so adding a new tool later never needs a
data migration and an upgraded firm sees exactly what it saw before.
"""
import json
from collections import OrderedDict

from flask import g, has_request_context

# Paths a tool switch never closes. See the module docstring for why each is here.
NEVER_GUARDED = ("/static", "/health", "/login", "/logout", "/setup", "/webhooks/", "/sign/", "/pay/",
                 "/p/", "/track/", "/api/", "/mcp", "/manifest.webmanifest", "/sw.js", "/offline")


class Tool:
    __slots__ = ("key", "label", "section", "description", "prefixes", "default_on", "requires")

    def __init__(self, key, label, section, description, prefixes, default_on=True, requires=()):
        self.key, self.label, self.section = key, label, section
        self.description, self.prefixes, self.default_on = description, tuple(prefixes), default_on
        # A tool that only makes sense alongside another. Switching the other off switches this
        # off with it, so no page is left pointing at a tool that is gone.
        self.requires = tuple(requires)


# Order here is the order on the Settings > Tools page. Sections match the sidebar.
TOOLS = OrderedDict((t.key, t) for t in [
    Tool("intake", "Intake and pipeline", "Clients",
         "Web intake form, lead inbox, pipeline board and follow-up sequences. Turning this off also "
         "closes the public intake form on your website.",
         ["/intake"]),
    Tool("conflicts", "Conflict check", "Clients",
         "Search contacts, parties and documents for conflicts before taking a matter.",
         ["/conflicts"]),
    Tool("engagements", "Engagement letters", "Clients",
         "Letter templates, sending, and signature tracking for engagement letters.",
         ["/engagements"]),
    Tool("messages", "Messages", "Clients",
         "Text, email and portal message threads with clients. Incoming texts are still recorded while off.",
         ["/messages"]),
    Tool("signatures", "Signatures", "Clients",
         "E-signature requests on documents. Links already sent to clients keep working.",
         ["/signatures"]),
    Tool("voice", "Voice line", "Clients",
         "The after-hours phone agent and its call log.",
         ["/voice", "/settings/voice"]),
    Tool("portal", "Client portal", "Clients",
         "The secure portal where clients read messages and download shared documents. Off closes the "
         "portal sign-in for every client.",
         ["/portal"]),
    Tool("time", "Time and expenses", "Work",
         "Timers, time entries, expenses and receipt capture.",
         ["/time"]),
    Tool("time_suggestions", "Time suggestions", "Work",
         "Suggested time entries built from your calendar, email and documents.",
         ["/time/suggestions"], requires=["time"]),
    Tool("tasks", "Tasks and deadlines", "Work",
         "Tasks, deadlines and court dates on each matter.",
         ["/tasks"]),
    Tool("calendar", "Calendar", "Work",
         "Firm calendar and the calendar feed for Outlook, Google and Apple.",
         ["/calendar"]),
    Tool("court_rules", "Court rules", "Work",
         "Rule sets that turn a trigger date into deadlines, and the court holiday list.",
         ["/settings/rules", "/settings/holidays", "/rules"], requires=["tasks"]),
    Tool("documents", "Documents", "Work",
         "Document storage on each matter, sharing to the portal, and email filing.",
         ["/documents"]),
    Tool("doctemplates", "Document templates", "Work",
         "Merge templates that draft documents from matter data.",
         ["/doctemplates"]),
    Tool("ai", "Ask Coil", "Work",
         "Questions and summaries over your matters using your own AI model key.",
         ["/ai"]),
    Tool("research", "Research", "Work",
         "Case law search and the citation check.",
         ["/research"]),
    Tool("case_audit", "Case audit", "Work",
         "Nightly review of open matters for missing steps and risks.",
         ["/audit"]),
    Tool("pi", "Personal injury", "Work",
         "Medical providers, records requests, damages and demand letters.",
         ["/pi", "/records"]),
    Tool("criminal", "Criminal defense", "Work",
         "Charges, court settings, speedy-trial tracking and discovery for criminal matters.",
         ["/criminal"]),
    Tool("discovery", "Discovery and depositions", "Work",
         "Discovery drafting and deposition summaries.",
         ["/discovery"]),
    Tool("invoices", "Invoices", "Money",
         "Building, sending and tracking invoices, credit notes and the invoice template. Public invoice "
         "links already sent keep working.",
         ["/invoices", "/settings/invoice-template"]),
    Tool("statements", "Client statements", "Money",
         "Statements of account for each client.",
         ["/statements"]),
    Tool("payments", "Payments", "Money",
         "Recorded payments and card and bank payments. Pay links already sent keep working.",
         ["/payments"], requires=["invoices"]),
    Tool("plans", "Plans and splits", "Money",
         "Payment plans and fee splits.",
         ["/money"], requires=["invoices"]),
    Tool("trust", "Trust accounting", "Money",
         "Client trust ledgers, three-way reconciliation and transfers.",
         ["/trust"]),
    Tool("accounting", "Accounting", "Money",
         "The general ledger and bank imports.",
         ["/accounting"]),
    Tool("reports", "Reports", "Money",
         "Revenue, realization, work in progress and aging reports.",
         ["/reports"]),
])

# Always on. Listed on the Settings > Tools page so a firm sees what it cannot switch off.
CORE = OrderedDict([
    ("dashboard", "Dashboard"),
    ("contacts", "Contacts"),
    ("matters", "Matters"),
    ("settings", "Settings, users and offices"),
    ("audit_log", "Audit log"),
    ("exports", "Exports, so you can always take your data with you"),
    ("import", "Import from another system"),
    ("setup_guide", "Setup guide"),
])

# Longest prefix wins, so /time/suggestions resolves to time_suggestions, not time.
_PREFIXES = sorted(((p, t.key) for t in TOOLS.values() for p in t.prefixes), key=lambda x: -len(x[0]))


def _parse(raw):
    try:
        data = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: bool(v) for k, v in data.items() if k in TOOLS}


def overrides_for(firm):
    return _parse(getattr(firm, "tool_overrides", "") if firm is not None else "")


def enabled_map(firm=None):
    """{tool_key: on?} for every registered tool, defaults filled in. Cached per request."""
    if firm is None and has_request_context() and "_coil_tools" in g:
        return g._coil_tools
    if firm is None:
        from .models import Firm
        firm = Firm.get()
    ov = overrides_for(firm)
    result = {k: ov.get(k, t.default_on) for k, t in TOOLS.items()}
    for k, t in TOOLS.items():
        if result[k] and any(not result.get(r, True) for r in t.requires):
            result[k] = False
    if has_request_context():
        g._coil_tools = result
    return result


def tool_enabled(key):
    """True for core tools and unknown keys, so a typo in a template never hides something by accident."""
    if key not in TOOLS:
        return True
    return enabled_map().get(key, True)


def tool_for_path(path):
    """The tool that owns ``path``, or None when the path belongs to core or is never guarded."""
    path = path or "/"
    for p in NEVER_GUARDED:
        if path == p.rstrip("/") or path.startswith(p):
            return None
    for prefix, key in _PREFIXES:
        if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
            return key
    return None


def overrides_from_choices(on_keys):
    """Turn the set of tools a firm ticked into the smallest override object to store."""
    on_keys = set(on_keys)
    out = {}
    for k, t in TOOLS.items():
        want = k in on_keys
        if want != t.default_on:
            out[k] = want
    return out


def by_section():
    out = OrderedDict()
    for t in TOOLS.values():
        out.setdefault(t.section, []).append(t)
    return out


def guard():
    """before_request: close the pages of a tool this firm has switched off.

    Answers 404 rather than 403. The page does not exist for this firm; it is not a matter
    of the person lacking permission. The owner is told where to switch it back on.
    """
    from flask import request, render_template
    key = tool_for_path(request.path)
    if key is None or tool_enabled(key):
        return None
    from .helpers import current_user
    u = current_user()
    label = TOOLS[key].label
    if u and u.role == "owner":
        msg = (f"{label} is switched off for this firm. You can switch it back on under Settings, Tools, "
               f"and everything recorded in it before is still there.")
    else:
        msg = f"{label} is switched off for this firm. Ask the firm owner if you need it."
    return render_template("error.html", code=404, message=msg, tools_link=bool(u and u.role == "owner")), 404
