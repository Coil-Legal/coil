"""Two-way SMS via Twilio REST API (no SDK dependency)."""
import requests
from flask import current_app

from ..integrations import setting


def configured():
    return all(setting(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER"))


def send_sms(to, body):
    """Returns (provider_id, status). When Twilio is not configured, returns ('', 'unconfigured')."""
    if not configured():
        current_app.logger.info("[SMS-DEV] to=%s body=%s", to, body)
        return "", "unconfigured"
    sid, tok, frm = (setting("TWILIO_ACCOUNT_SID"), setting("TWILIO_AUTH_TOKEN"),
                     setting("TWILIO_FROM_NUMBER"))
    r = requests.post(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",
        auth=(sid, tok),
        data={"To": to, "From": frm, "Body": body}, timeout=20)
    if r.status_code >= 300:
        return "", f"error:{r.status_code}"
    j = r.json()
    return j.get("sid", ""), j.get("status", "queued")
