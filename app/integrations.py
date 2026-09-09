"""One place to resolve an integration setting, wherever the firm put it.

Order: the server environment, then what the firm saved itself, then app config, then a
default. The environment wins because an operator who pinned something in .env made a
deliberate choice; a settings page must not silently undo it. The firm's own value comes
next because a firm on an instance somebody else runs has no other way to configure
anything, and telling a solo attorney to edit a file inside a container is not a plan.

Never raises. A malformed settings row must degrade to "not configured", which every
feature already handles, rather than taking the app down.
"""
import json
import os

from flask import current_app, has_app_context

# Only these may be stored on the firm. An allowlist rather than a free-for-all: this
# blob is written from a web form, and SECRET_KEY or DATABASE_URL must never be settable
# that way.
FIRM_SETTABLE = (
    "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "MAIL_FROM",
    "STRIPE_SECRET_KEY", "STRIPE_PUBLISHABLE_KEY", "STRIPE_WEBHOOK_SECRET",
    "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER",
    "IMAP_HOST", "IMAP_PORT", "IMAP_USER", "IMAP_PASS", "IMAP_FOLDER",
)

SECRET_FIELDS = ("SMTP_PASS", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET",
                 "TWILIO_AUTH_TOKEN", "IMAP_PASS")


def firm_values():
    """Everything the firm saved, as a dict. Empty on any problem."""
    if not has_app_context():
        return {}
    try:
        from .models import Firm
        raw = Firm.get().integration_json or "{}"
        v = json.loads(raw)
        return v if isinstance(v, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def save_firm_values(updates):
    """Merge updates into the firm's stored settings. A blank value clears that key,
    so a firm can undo a setting without an admin. Returns the merged dict."""
    from .extensions import db
    from .models import Firm
    firm = Firm.get()
    current = firm_values()
    for k, v in (updates or {}).items():
        if k not in FIRM_SETTABLE:
            continue
        v = (v or "").strip()
        if v:
            current[k] = v
        else:
            current.pop(k, None)
    firm.integration_json = json.dumps(current)
    db.session.add(firm)
    return current


def setting(name, default=""):
    """Resolve one integration setting. See the module docstring for the order."""
    v = os.environ.get(name)
    if v not in (None, ""):
        return v
    fv = firm_values().get(name)
    if fv not in (None, ""):
        return fv
    if has_app_context():
        cv = current_app.config.get(name)
        if cv not in (None, ""):
            return cv
    return default
