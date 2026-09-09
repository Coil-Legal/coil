"""A guided walk through the optional integrations, one at a time, all skippable.

Coil works with none of these. The Integrations page explains them well enough once you
know they exist, but a new firm does not, and a grid of five "not configured" badges
reads as five problems rather than five choices. This walks through them in the order a
practice actually needs them, says plainly what each is for and whether it is worth it,
and lets someone skip anything they are not ready for and come back later.

Progress lives on Firm.setup_json as {"stripe": "done"} or {"stripe": "skipped"}, so the
wizard can be left half-finished and resumed, and the dashboard can stop nagging once
every step has been answered one way or the other.
"""
import json

from flask import Blueprint, redirect, render_template, request, url_for, flash

from ..extensions import db
from ..helpers import login_required, current_user
from ..integrations import save_firm_values, setting, SECRET_FIELDS
from ..models import Firm, audit

bp = Blueprint("setupguide", __name__, url_prefix="/setup-guide")

# Ordered by what a firm needs first, not by what is easiest to build. Sending email
# comes before taking payment, because an invoice nobody receives cannot be paid.
STEPS = [
    dict(key="smtp", title="Sending email",
         fields=[("SMTP_HOST", "Mail server", "smtp.gmail.com", False),
                 ("SMTP_PORT", "Port", "587", False),
                 ("SMTP_USER", "Your email address", "you@yourfirm.com", False),
                 ("SMTP_PASS", "App password", "", True),
                 ("MAIL_FROM", "Send as", "Your Firm <you@yourfirm.com>", False)]),
    dict(key="courtlistener", title="Case law research", fields=[]),   # stored on Firm directly
    dict(key="stripe", title="Getting paid online",
         fields=[("STRIPE_SECRET_KEY", "Secret key", "sk_test_... or sk_live_...", True),
                 ("STRIPE_PUBLISHABLE_KEY", "Publishable key", "pk_test_... or pk_live_...", False),
                 ("STRIPE_WEBHOOK_SECRET", "Webhook signing secret", "whsec_...", True)]),
    dict(key="imap", title="Filing email to matters",
         fields=[("IMAP_HOST", "Mail server", "imap.gmail.com", False),
                 ("IMAP_PORT", "Port", "993", False),
                 ("IMAP_USER", "Mailbox to watch", "files@yourfirm.com", False),
                 ("IMAP_PASS", "App password", "", True),
                 ("IMAP_FOLDER", "Folder", "INBOX", False)]),
    dict(key="twilio", title="Texting clients",
         fields=[("TWILIO_ACCOUNT_SID", "Account SID", "AC...", False),
                 ("TWILIO_AUTH_TOKEN", "Auth token", "", True),
                 ("TWILIO_FROM_NUMBER", "Your Twilio number", "+15125550100", False)]),
]
KEYS = [s["key"] for s in STEPS]


def progress():
    try:
        v = json.loads(Firm.get().setup_json or "{}")
        return v if isinstance(v, dict) else {}
    except Exception:  # noqa: BLE001
        return {}


def _record(key, state):
    firm = Firm.get()
    p = progress()
    p[key] = state
    firm.setup_json = json.dumps(p)
    db.session.add(firm)


def is_configured(key):
    """Whether the thing actually works, regardless of what the wizard was told."""
    if key == "courtlistener":
        return bool((Firm.get().courtlistener_token or "").strip() or setting("COURTLISTENER_TOKEN"))
    step = next(s for s in STEPS if s["key"] == key)
    required = [f[0] for f in step["fields"]
                if f[0] not in ("SMTP_PORT", "IMAP_PORT", "IMAP_FOLDER", "STRIPE_WEBHOOK_SECRET")]
    return all(setting(k) for k in required)


def remaining():
    """Steps neither set up nor deliberately skipped."""
    p = progress()
    return [s for s in STEPS if not is_configured(s["key"]) and p.get(s["key"]) != "skipped"]


def _step_or_none(key):
    return next((s for s in STEPS if s["key"] == key), None)


@bp.route("", strict_slashes=False)
@bp.route("/")
@login_required
def index():
    p = progress()
    rows = [dict(step=s, configured=is_configured(s["key"]), state=p.get(s["key"], "")) for s in STEPS]
    return render_template("setupguide/index.html", rows=rows, remaining=len(remaining()))


@bp.route("/<key>", methods=["GET", "POST"])
@login_required
def step(key):
    s = _step_or_none(key)
    if not s:
        return redirect(url_for("setupguide.index"))
    nxt = KEYS.index(key) + 1
    after = url_for("setupguide.step", key=KEYS[nxt]) if nxt < len(KEYS) else url_for("setupguide.index")

    if request.method == "POST":
        if request.form.get("action") == "skip":
            _record(key, "skipped")
            audit("setup_skip", "firm", Firm.get().id, key, current_user().id)
            db.session.commit()
            flash(f"Skipped {s['title'].lower()}. You can set it up any time from this guide.", "ok")
            return redirect(after)

        if key == "courtlistener":
            firm = Firm.get()
            firm.courtlistener_token = (request.form.get("COURTLISTENER_TOKEN") or "").strip()[:120]
            db.session.add(firm)
        else:
            # Blank means "leave whatever is stored", so a half-filled form does not wipe a
            # working setting. Someone clears a value by typing the word none.
            updates = {}
            for name, _label, _ph, _secret in s["fields"]:
                v = (request.form.get(name) or "").strip()
                if v.lower() == "none":
                    updates[name] = ""
                elif v:
                    updates[name] = v
            save_firm_values(updates)
        _record(key, "done")
        audit("setup_done", "firm", Firm.get().id, key, current_user().id)
        db.session.commit()
        flash(f"Saved. {s['title']} is set up.", "ok")
        return redirect(after)

    stored = {}
    for name, _l, _p, secret in s["fields"]:
        v = setting(name)
        stored[name] = "" if (secret and v) else v
        stored[name + "_isset"] = bool(v)
    if key == "courtlistener":
        stored["COURTLISTENER_TOKEN"] = (Firm.get().courtlistener_token or "")
    return render_template(f"setupguide/{key}.html", s=s, stored=stored, secrets=SECRET_FIELDS,
                           configured=is_configured(key), state=progress().get(key, ""),
                           step_no=KEYS.index(key) + 1, step_total=len(KEYS), after=after)
