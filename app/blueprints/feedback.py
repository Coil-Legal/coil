"""In-app feedback, from a running Coil back to the people building it.

Coil ships changes most days on the strength of what firms actually report, which only
works if reporting something takes ten seconds from the screen where it went wrong.

The submission is made server-side by this instance, never by the attorney's browser.
That matters for a self-hosted firm: their machine talks to coil.legal, the browser does
not, and the instance decides exactly what leaves the building. What leaves is listed in
the form itself so nobody has to guess:

    the firm name, the sender's name and email, the page they were on,
    the Coil version, and what they typed

Never the matter, the client, or anything from the database. A feedback box on a legal
practice manager has to be boring about that or it should not exist.

Turn it off entirely with FEEDBACK_ENABLED=0.
"""
import json
import urllib.error
import urllib.request

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from ..helpers import current_user, login_required
from ..models import Firm

bp = Blueprint("feedback", __name__, url_prefix="/feedback")

KINDS = [
    ("bug", "Something is broken"),
    ("missing", "Something is missing"),
    ("confusing", "Something is confusing"),
    ("praise", "Something works well"),
]
KIND_KEYS = {k for k, _ in KINDS}


def _enabled():
    return str(current_app.config.get("FEEDBACK_ENABLED", "1")).lower() not in ("0", "false", "no")


def _payload(user, firm, kind, message, page):
    """Exactly what gets sent. Kept in one place so the page can show it honestly."""
    return {
        "firm": firm.name if firm else "",
        "name": user.name if user else "",
        "email": user.email if user else "",
        "kind": kind,
        "message": message,
        "page": page,
        "version": current_app.config.get("COIL_VERSION", "unknown"),
        "commit": current_app.config.get("COIL_COMMIT", "unknown"),
        "channel": current_app.config.get("COIL_CHANNEL", "unknown"),
        "base_url": current_app.config.get("BASE_URL", ""),
        "hosting": current_app.config.get("COIL_HOSTING", "self-hosted"),
    }


@bp.route("", strict_slashes=False, methods=["GET", "POST"])
@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if not _enabled():
        flash("Feedback is turned off on this install.", "error")
        return redirect(url_for("dashboard.index"))

    user = current_user()
    firm = Firm.get()
    # Where they were when they hit the button, so a bug report carries its own context.
    page = (request.values.get("from") or request.referrer or "")[:300]

    if request.method == "POST":
        kind = request.form.get("kind", "bug")
        if kind not in KIND_KEYS:
            kind = "bug"
        message = (request.form.get("message") or "").strip()
        if not message:
            flash("Tell us what happened and we will read it.", "error")
            return render_template("feedback/index.html", kinds=KINDS, page=page,
                                   payload=_payload(user, firm, kind, "", page), message=message)

        ok, note = send_feedback(_payload(user, firm, kind, message, page))
        if ok:
            flash("Sent. If it is worth doing we usually have it built within a day or two.", "ok")
            return redirect(page if page.startswith("/") else url_for("dashboard.index"))
        flash(note, "error")
        return render_template("feedback/index.html", kinds=KINDS, page=page,
                               payload=_payload(user, firm, kind, message, page), message=message)

    return render_template("feedback/index.html", kinds=KINDS, page=page,
                           payload=_payload(user, firm, "bug", "", page), message="")


def send_feedback(payload):
    """POST to coil.legal. Returns (ok, message_for_the_user).

    A firm on a locked-down network, or offline, must get a clear answer and somewhere
    else to send it, rather than a spinner and silence.
    """
    url = current_app.config.get("COIL_FEEDBACK_URL", "https://coil.legal/api/coil-feedback")
    body = json.dumps(payload).encode("utf-8")
    # Identify as Coil. The default urllib agent is blocked as a bot by the WAF in front
    # of coil.legal, which turned every send into a 403, and an unnamed agent hammering a
    # public endpoint deserves to be blocked anyway.
    agent = f"Coil/{current_app.config.get('COIL_VERSION', 'unknown')} (+https://coil.legal)"
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/json",
                                          "User-Agent": agent})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            if 200 <= r.status < 300:
                return True, ""
            return False, f"coil.legal answered {r.status}. Email hello@coil.legal instead."
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return False, "That is a lot of feedback at once. Give it a minute and send again."
        return False, f"coil.legal answered {e.code}. Email hello@coil.legal instead."
    except Exception as e:  # noqa: BLE001
        current_app.logger.warning("feedback send failed: %s", e)
        return False, ("Could not reach coil.legal from this server. Check the connection, "
                       "or email hello@coil.legal and paste what you wrote.")
