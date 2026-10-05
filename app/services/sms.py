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


#: Twilio delivery-status error codes worth explaining in a sentence a non-technical
#: staff member can act on. Anything else just shows Twilio's own ErrorCode.
DELIVERY_ERROR_EXPLANATIONS = {
    "30034": "Carriers refused this text because the firm's number is not registered for "
             "business texting (A2P 10DLC). Register it in Twilio.",
    "30003": "The client's phone is unreachable (carrier reports the handset turned off or out of range).",
    "30005": "The client's number is unknown to the carrier (likely disconnected or mistyped).",
    "30006": "The client's carrier flagged this number as unable to receive SMS (often a landline).",
    "30007": "The client's carrier or phone filtered this message as suspected spam.",
}


def explain_delivery_error(code):
    """A plain-English reason for a Twilio delivery-status ErrorCode, for the staff thread."""
    code = (code or "").strip()
    if not code:
        return ""
    known = DELIVERY_ERROR_EXPLANATIONS.get(code)
    return f"Twilio error {code}: {known}" if known else f"Twilio error {code}: delivery failed."


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
    status_callback = current_app.config["BASE_URL"].rstrip("/") + "/webhooks/twilio/status"
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, tok),
        data={"To": to, "From": frm, "Body": body, "StatusCallback": status_callback}, timeout=20)
    if r.status_code >= 300:
        status, reason = provider_error(r)
        current_app.logger.warning("[SMS] to=%s rejected: %s %s", to, status, reason)
        return "", status, reason
    j = r.json()
    return j.get("sid", ""), j.get("status", "queued"), ""
