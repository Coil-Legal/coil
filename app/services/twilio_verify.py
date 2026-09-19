"""Validate Twilio's form webhook signature without trusting proxy host headers.

Algorithm: https://www.twilio.com/docs/usage/security#validating-requests
"""
import base64
import hashlib
import hmac


def valid_signature(token, url, form, signature):
    if not token or not signature:
        return False
    body = url
    for name in sorted(form):
        for value in sorted(set(form.getlist(name))):
            body += name + value
    expected = base64.b64encode(hmac.new(token.encode(), body.encode(), hashlib.sha1).digest())
    return hmac.compare_digest(expected, signature.encode())
