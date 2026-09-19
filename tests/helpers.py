import re


def _tok(data):
    m = re.search(rb'name="_csrf" value="([^"]+)"', data)
    return m.group(1).decode() if m else None


def login(c, email="owner@example.com", pw="password123"):
    """Log in through the real form and return a CSRF token valid for the new session."""
    r = c.get("/login")
    tok = _tok(r.data)
    r = c.post("/login", data={"email": email, "password": pw, "_csrf": tok})
    assert r.status_code == 302, r.data[:300]
    # auth.login clears the session, so fetch a fresh token from an authenticated page.
    r = c.get("/")
    return _tok(r.data) or tok


def capture_delivered_mail(to, subject, html, **kwargs):
    """Successful test delivery, captured locally without contacting an SMTP server."""
    from app.services.mail import _dev_outbox
    _dev_outbox.append({"to": to, "subject": subject, "html": html})
    return True


def post_stripe_event(client, app, event):
    """Exercise webhook verification with a signed synthetic event."""
    import hashlib
    import hmac
    import json
    import time
    from unittest.mock import patch
    body = json.dumps(event)
    stamp = str(int(time.time()))
    secret = 'whsec_local_test'
    signature = hmac.new(secret.encode(), f'{stamp}.{body}'.encode(), hashlib.sha256).hexdigest()
    with patch.dict(app.config, {'STRIPE_WEBHOOK_SECRET': secret}):
        return client.post('/webhooks/stripe', data=body, content_type='application/json',
                           headers={'Stripe-Signature': f't={stamp},v1={signature}'})


def post_twilio_form(client, app, data):
    """Deliver a signed synthetic form using the configured public URL."""
    import base64
    import hashlib
    import hmac
    from unittest.mock import patch
    token = 'local-twilio-test-token'
    url = app.config['BASE_URL'].rstrip('/') + '/webhooks/twilio'
    payload = url + ''.join(key + data[key] for key in sorted(data))
    signature = base64.b64encode(hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()).decode()
    with patch.dict(app.config, {'TWILIO_AUTH_TOKEN': token}):
        return client.post('/webhooks/twilio', data=data, headers={'X-Twilio-Signature': signature})
