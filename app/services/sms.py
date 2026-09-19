"""Two-way SMS via Twilio REST API (no SDK dependency)."""
import requests
from flask import current_app

from ..integrations import setting


def configured():
    return all(setting(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"))


def provider_error(r):
    """Twilio's own account of what went wrong, as (short_status, human_reason).

    A bare "error:400" tells the person at the keyboard nothing they can act on: the
    number was fictional, or it was the firm's own Twilio number, or the account is
    unfunded, and each of those wants a different response. Twilio says which in the
    body, so say it back. The status stays short because Message.status is 30 chars;
    the reason is for the screen and the log, not the column.
    """
    try:
        j = r.json()
    except ValueError:
        j = {}
    code = j.get("code")
    msg = (j.get("message") or "").strip()
    if not msg:
        msg = f"Twilio returned HTTP {r.status_code} with no explanation."
    more = (j.get("more_info") or "").strip()
    if more:
        msg = f"{msg} ({more})"
    return (f"error:{code}" if code else f"error:{r.status_code}"), msg


def send_sms(to, body):
    """Returns (provider_id, status, detail).

    detail is empty on success and carries Twilio's own wording on failure.
    When Twilio is not configured, returns ('', 'unconfigured', '').
    """
    if not configured():
        current_app.logger.info("[SMS-DEV] to=%s body=%s", to, body)
        return "", "unconfigured", ""
    sid, tok, frm = (setting("TWILIO_ACCOUNT_SID"), setting("TWILIO_AUTH_TOKEN"),
                     setting("TWILIO_FROM_NUMBER"))
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, tok),
        data={"To": to, "From": frm, "Body": body}, timeout=20)
    if r.status_code >= 300:
        status, reason = provider_error(r)
        current_app.logger.warning("[SMS] to=%s rejected: %s %s", to, status, reason)
        return "", status, reason
    j = r.json()
    return j.get("sid", ""), j.get("status", "queued"), ""
