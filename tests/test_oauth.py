"""OAuth 2.1 for /mcp (blueprints/oauth.py): discovery, registration, consent, PKCE, refresh
rotation, revocation and the connected apps list.

Synthetic data only, own SQLite file per test. Run:
  .venv/bin/python -m pytest tests/test_oauth.py -q
"""
import base64
import hashlib
import re
import secrets
from datetime import timedelta
from urllib.parse import urlsplit, parse_qs, urlencode

import pytest

BASE = "https://coil.example.test"
REDIRECT = "https://claude.ai/api/mcp/auth_callback"
PW = "synthetic-password"


@pytest.fixture
def app(tmp_path, monkeypatch):
    for key in ("DATABASE_URL", "STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "SMTP_HOST",
                "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    import requests

    def offline(*args, **kwargs):
        raise RuntimeError("external HTTP is disabled in tests")
    monkeypatch.setattr(requests.sessions.Session, "request", offline)
    from app import create_app
    from app.extensions import db
    from app.models import Firm, User, Contact, Matter
    from app.blueprints.api import reset_rate_limits
    from app.blueprints.oauth import reset_register_limits
    reset_rate_limits()
    reset_register_limits()
    a = create_app({"TESTING": True, "SECRET_KEY": "oauth-synthetic", "BASE_URL": BASE,
                    "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/oauth.db",
                    "UPLOAD_DIR": str(tmp_path / "uploads"), "PDF_DIR": str(tmp_path / "pdf"),
                    "SMTP_HOST": "", "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": ""})
    with a.app_context():
        Firm.get()
        for role in ("owner", "attorney", "readonly"):
            u = User(email=f"{role}@example.test", name=f"Test {role}", role=role)
            u.set_password(PW)
            db.session.add(u)
        c = Contact(first_name="Synthetic", last_name="Client", email="client@example.test", is_client=True)
        db.session.add(c)
        db.session.flush()
        db.session.add(Matter(number="M-OAUTH", name="Synthetic matter", client_id=c.id, status="open",
                              billing_type="hourly"))
        db.session.commit()
    yield a
    with a.app_context():
        db.session.remove()
        db.engine.dispose()


# ---------------------------------------------------------------- helpers

def _csrf(data):
    m = re.search(rb'name="_csrf" value="([^"]+)"', data)
    return m.group(1).decode() if m else None


def pkce():
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def register(c, **extra):
    body = {"redirect_uris": [REDIRECT], "client_name": "Claude", "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"]}
    body.update(extra)
    r = c.post("/oauth/register", json=body)
    assert r.status_code == 201, r.data
    return r.get_json()


def auth_query(client_id, challenge, **extra):
    q = {"response_type": "code", "client_id": client_id, "redirect_uri": REDIRECT, "code_challenge": challenge,
         "code_challenge_method": "S256", "state": "st-123", "resource": BASE + "/mcp"}
    q.update(extra)
    return "/oauth/authorize?" + urlencode({k: v for k, v in q.items() if v is not None})


def sign_in(c, role="owner"):
    r = c.get("/login")
    r = c.post("/login", data={"email": f"{role}@example.test", "password": PW, "_csrf": _csrf(r.data)})
    assert r.status_code == 302


def qs(location):
    return {k: v[0] for k, v in parse_qs(urlsplit(location).query).items()}


def consent_form(page):
    """The hidden fields of the consent form, as a browser would post them."""
    fields = dict(re.findall(rb'<input type="hidden" name="([^"]+)" value="([^"]*)">', page))
    import html
    return {k.decode(): html.unescape(v.decode()) for k, v in fields.items()}


def approve(c, client_id, challenge, scopes, mode=None, decision="approve", role="owner", **extra):
    """Sign in (if needed), open the consent page and submit it. Returns the redirect response."""
    r = c.get(auth_query(client_id, challenge, **extra))
    if r.status_code == 302 and "/login" in r.headers["Location"]:
        sign_in(c, role)
        r = c.get(auth_query(client_id, challenge, **extra))
    assert r.status_code == 200, r.data[:400]
    data = consent_form(r.data)
    data["decision"] = decision
    data["scopes"] = scopes
    if mode:
        data["confidentiality"] = mode
    return c.post("/oauth/authorize", data=data)


def exchange(c, client_id, code, verifier, redirect_uri=REDIRECT):
    return c.post("/oauth/token", data={"grant_type": "authorization_code", "code": code, "client_id": client_id,
                                        "redirect_uri": redirect_uri, "code_verifier": verifier})


def refresh(c, client_id, rt, **extra):
    return c.post("/oauth/token", data=dict({"grant_type": "refresh_token", "refresh_token": rt,
                                             "client_id": client_id}, **extra))


def grant(app, scopes=("matters:read",), mode=None, role="owner"):
    """Run the whole flow and return (client, client_id, token json)."""
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    r = approve(c, cid, challenge, list(scopes), mode=mode, role=role)
    assert r.status_code == 302 and r.headers["Location"].startswith(REDIRECT), r.headers.get("Location")
    code = qs(r.headers["Location"])["code"]
    r = exchange(c, cid, code, verifier)
    assert r.status_code == 200, r.data
    return c, cid, r.get_json()


def bearer(tok):
    return {"Authorization": f"Bearer {tok}"}


def me(app, tok):
    from app.blueprints.api import reset_rate_limits
    reset_rate_limits()
    return app.test_client().get("/api/v1/me", headers=bearer(tok))


def mcp_tools(app, tok):
    return app.test_client().post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                                  headers=bearer(tok))


# ---------------------------------------------------------------- discovery

def test_protected_resource_metadata(app):
    c = app.test_client()
    for path in ("/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"):
        r = c.get(path)
        assert r.status_code == 200
        j = r.get_json()
        assert j["resource"] == BASE + "/mcp"
        assert j["authorization_servers"] == [BASE]
        assert j["bearer_methods_supported"] == ["header"]
        assert "matters:read" in j["scopes_supported"] and "time:write" in j["scopes_supported"]
        assert r.headers["Access-Control-Allow-Origin"] == "*"


def test_authorization_server_metadata(app):
    j = app.test_client().get("/.well-known/oauth-authorization-server").get_json()
    assert j["issuer"] == BASE
    assert j["authorization_endpoint"] == BASE + "/oauth/authorize"
    assert j["token_endpoint"] == BASE + "/oauth/token"
    assert j["registration_endpoint"] == BASE + "/oauth/register"
    assert j["revocation_endpoint"] == BASE + "/oauth/revoke"
    assert j["response_types_supported"] == ["code"]
    assert j["grant_types_supported"] == ["authorization_code", "refresh_token"]
    assert j["code_challenge_methods_supported"] == ["S256"]
    assert "none" in j["token_endpoint_auth_methods_supported"]
    from app.blueprints.api import ALL_SCOPES
    assert j["scopes_supported"] == list(ALL_SCOPES)


def test_mcp_401_points_at_metadata(app):
    c = app.test_client()
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert r.status_code == 401
    assert r.headers["WWW-Authenticate"] == \
        f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'
    assert r.get_json()["error"]["code"] == -32001          # the existing JSON body is kept
    r = c.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, headers=bearer("coil_nonsense"))
    assert r.status_code == 401
    assert 'resource_metadata="' in r.headers["WWW-Authenticate"]
    assert 'error="invalid_token"' in r.headers["WWW-Authenticate"]


def test_cors_preflight(app):
    c = app.test_client()
    hdrs = {"Origin": "https://claude.ai", "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type"}
    for path in ("/mcp", "/oauth/token", "/oauth/register", "/oauth/revoke",
                 "/.well-known/oauth-authorization-server", "/.well-known/oauth-protected-resource"):
        r = c.open(path, method="OPTIONS", headers=hdrs)
        assert r.status_code in (200, 204), path
        assert r.headers.get("Access-Control-Allow-Origin") == "*", path
        assert "Authorization" in r.headers.get("Access-Control-Allow-Headers", ""), path
        assert "Access-Control-Allow-Credentials" not in r.headers
    # The consent page is a browser page bound to the session: no CORS there.
    r = c.open("/oauth/authorize", method="OPTIONS", headers=hdrs)
    assert "Access-Control-Allow-Origin" not in r.headers
    # The 401 from /mcp exposes the challenge header to browser clients.
    r = c.post("/mcp", json={}, headers={"Origin": "https://claude.ai"})
    assert "WWW-Authenticate" in r.headers["Access-Control-Expose-Headers"]


# ---------------------------------------------------------------- registration

def test_register_validates_redirects(app):
    c = app.test_client()
    j = register(c)
    assert j["client_id"].startswith("coilc_") and j["redirect_uris"] == [REDIRECT]
    assert j["token_endpoint_auth_method"] == "none" and "client_secret" not in j
    assert register(c, redirect_uris=["http://localhost:6274/callback"])["client_id"]
    assert register(c, redirect_uris=["http://127.0.0.1:33418/cb"])["client_id"]
    for bad in (["http://evil.example/cb"], ["javascript:alert(1)"], ["https://x.example/cb#frag"], [], "nope"):
        r = c.post("/oauth/register", json={"redirect_uris": bad, "client_name": "x"})
        assert r.status_code == 400, bad
        assert r.get_json()["error"] == "invalid_redirect_uri"
    r = c.post("/oauth/register", json={"redirect_uris": [REDIRECT], "grant_types": ["client_credentials"]})
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_client_metadata"
    r = c.post("/oauth/register", data="not json", content_type="text/plain")
    assert r.status_code == 400
    # Scopes a client lists beyond what Coil supports are dropped, never stored.
    j = register(c, scope="matters:read admin:everything trust:write")
    assert j["scope"] == "matters:read"


def test_register_rate_limited(app):
    c = app.test_client()
    from app.blueprints.oauth import REGISTER_PER_IP
    for _ in range(REGISTER_PER_IP):
        register(c)
    r = c.post("/oauth/register", json={"redirect_uris": [REDIRECT]})
    assert r.status_code == 429


# ---------------------------------------------------------------- the whole flow

def test_full_flow(app):
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()

    # Not signed in: through the normal login and back to the same request.
    r = c.get(auth_query(cid, challenge, scope="matters:read time:write"))
    assert r.status_code == 302 and "/login" in r.headers["Location"]
    login_url = r.headers["Location"]
    page = c.get(login_url)
    r = c.post(login_url, data={"email": "owner@example.test", "password": PW, "_csrf": _csrf(page.data)})
    assert r.status_code == 302
    assert r.headers["Location"].startswith("/oauth/authorize?")

    page = c.get(r.headers["Location"])
    assert page.status_code == 200
    body = page.data.decode()
    assert "Claude" in body and "claude.ai" in body
    assert re.search(r'value="redacted" checked', body), "redacted must be preselected"
    assert not re.search(r'value="full" checked', body)
    assert 'value="matters:read" aria-label="Read Matters and cases" checked' in body
    assert 'value="time:write" aria-label="Write Time entries and the timer" checked' in body
    assert "frame-ancestors 'none'" in page.headers["Content-Security-Policy"]
    assert page.headers["X-Frame-Options"] == "DENY"

    data = consent_form(page.data)
    data.update({"decision": "approve", "scopes": ["matters:read", "time:write"], "confidentiality": "redacted"})
    r = c.post("/oauth/authorize", data=data)
    assert r.status_code == 302
    q = qs(r.headers["Location"])
    assert r.headers["Location"].startswith(REDIRECT + "?") and q["state"] == "st-123"

    r = exchange(c, cid, q["code"], verifier)
    assert r.status_code == 200, r.data
    assert r.headers["Cache-Control"] == "no-store"
    tok = r.get_json()
    assert tok["token_type"] == "Bearer" and tok["expires_in"] == 3600
    assert set(tok["scope"].split()) == {"matters:read", "time:write"}
    assert tok["access_token"] and tok["refresh_token"]

    r = me(app, tok["access_token"])
    assert r.status_code == 200
    j = r.get_json()
    assert j["token"]["confidentiality"] == "redacted"
    assert j["token"]["name"] == "OAuth: Claude"
    assert set(j["token"]["scopes"]) == {"matters:read", "time:write"}

    r = mcp_tools(app, tok["access_token"])
    assert r.status_code == 200
    names = {t["name"] for t in r.get_json()["result"]["tools"]}
    assert {"list_matters", "log_time"} <= names and "list_invoices" not in names

    # Refresh rotates; the old access token stays valid until it expires.
    r = refresh(c, cid, tok["refresh_token"])
    assert r.status_code == 200, r.data
    tok2 = r.get_json()
    assert tok2["refresh_token"] != tok["refresh_token"] and tok2["access_token"] != tok["access_token"]
    assert me(app, tok2["access_token"]).status_code == 200

    # The replaced refresh token presented again: the whole chain goes.
    r = refresh(c, cid, tok["refresh_token"])
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_grant"
    assert refresh(c, cid, tok2["refresh_token"]).get_json()["error"] == "invalid_grant"
    assert me(app, tok["access_token"]).status_code == 401
    assert me(app, tok2["access_token"]).status_code == 401
    with app.app_context():
        from app.models import AuditLog
        actions = [a.action for a in AuditLog.query.all()]
        for want in ("oauth_authorize", "oauth_token_issue", "oauth_token_refresh", "oauth_refresh_reuse"):
            assert want in actions, want

    # A fresh grant, then revocation (RFC 7009) of the access token and of the refresh token.
    c3, cid3, tok3 = grant(app)
    r = c3.post("/oauth/revoke", data={"token": tok3["access_token"], "token_type_hint": "access_token",
                                       "client_id": cid3})
    assert r.status_code == 200
    assert me(app, tok3["access_token"]).status_code == 401
    r = c3.post("/oauth/revoke", data={"token": tok3["refresh_token"], "client_id": cid3})
    assert r.status_code == 200
    assert refresh(c3, cid3, tok3["refresh_token"]).get_json()["error"] == "invalid_grant"
    # Unknown tokens get the same answer.
    assert c3.post("/oauth/revoke", data={"token": "nope", "client_id": cid3}).status_code == 200


def test_static_tokens_unchanged(app):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token
    with app.app_context():
        u = User.query.filter_by(email="owner@example.test").first()
        t, raw = create_token(u, "laptop", ["matters:read"], "full")
        db.session.commit()
        assert t.expires_at is None and t.oauth_client_id is None
    assert me(app, raw).status_code == 200
    assert mcp_tools(app, raw).status_code == 200


def test_expired_access_token(app):
    c, cid, tok = grant(app)
    from app.extensions import db
    from app.models import ApiToken, now
    from app.blueprints.api import hash_token
    with app.app_context():
        t = ApiToken.query.filter_by(token_hash=hash_token(tok["access_token"])).first()
        assert t.expires_at is not None and t.oauth_client_id is not None
        t.expires_at = now() - timedelta(seconds=1)
        db.session.commit()
    r = me(app, tok["access_token"])
    assert r.status_code == 401 and r.get_json()["error"] == "Unknown or revoked token."
    r = mcp_tools(app, tok["access_token"])
    assert r.status_code == 401 and 'error="invalid_token"' in r.headers["WWW-Authenticate"]
    # The refresh token still gets a new one.
    r = refresh(c, cid, tok["refresh_token"])
    assert r.status_code == 200 and me(app, r.get_json()["access_token"]).status_code == 200


# ---------------------------------------------------------------- authorize refusals

def test_unregistered_client_and_wrong_redirect_show_error_page(app):
    c = app.test_client()
    sign_in(c)
    verifier, challenge = pkce()
    r = c.get(auth_query("coilc_not_registered", challenge))
    assert r.status_code == 400 and "Location" not in r.headers
    assert b"not registered" in r.data
    cid = register(c)["client_id"]
    for bad in ("https://evil.example/cb", REDIRECT + "/extra", REDIRECT + "?x=1", REDIRECT.upper()):
        r = c.get(auth_query(cid, challenge, redirect_uri=bad))
        assert r.status_code == 400 and "Location" not in r.headers, bad
    # The consent POST re-checks too: a tampered redirect never gets a code.
    page = c.get(auth_query(cid, challenge))
    data = consent_form(page.data)
    data.update({"decision": "approve", "scopes": ["matters:read"], "redirect_uri": "https://evil.example/cb"})
    r = c.post("/oauth/authorize", data=data)
    assert r.status_code == 400 and "Location" not in r.headers


def test_pkce_required_and_s256_only(app):
    """Malformed requests get an error page, never an automatic redirect to the registered URI,
    because anyone can register one and that would make Coil an open redirector."""
    c = app.test_client()
    sign_in(c)
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    cases = [(auth_query(cid, None), b"invalid_request"),
             (auth_query(cid, verifier, code_challenge_method="plain"), b"S256"),
             (auth_query(cid, challenge, code_challenge_method=None), b"S256"),
             (auth_query(cid, "tooshort"), b"invalid_request"),
             (auth_query(cid, challenge, response_type="token"), b"unsupported_response_type"),
             (auth_query(cid, challenge, resource="https://other.example/mcp"), b"invalid_target")]
    for url, words in cases:
        r = c.get(url)
        assert r.status_code == 400 and "Location" not in r.headers, url
        assert words in r.data, url
    # Not signed in gets the same page: no redirect to an attacker-registered address.
    r = app.test_client().get(auth_query(cid, None))
    assert r.status_code == 400 and "Location" not in r.headers
    # The consent POST re-checks the challenge as well.
    page = c.get(auth_query(cid, challenge))
    data = consent_form(page.data)
    data.update({"decision": "approve", "scopes": ["matters:read"], "code_challenge_method": "plain"})
    r = c.post("/oauth/authorize", data=data)
    assert r.status_code == 400 and "Location" not in r.headers


def test_bad_verifier_then_good(app):
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    code = qs(approve(c, cid, challenge, ["matters:read"]).headers["Location"])["code"]
    other, _ = pkce()
    r = exchange(c, cid, code, other)
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_grant"
    r = exchange(c, cid, code, "short")
    assert r.get_json()["error"] == "invalid_grant"
    r = c.post("/oauth/token", data={"grant_type": "authorization_code", "code": code, "client_id": cid})
    assert r.get_json()["error"] == "invalid_request"
    r = exchange(c, cid, code, verifier, redirect_uri="https://claude.ai/other")
    assert r.get_json()["error"] == "invalid_grant"
    # A different client cannot use the code either.
    cid2 = register(c)["client_id"]
    assert exchange(c, cid2, code, verifier).get_json()["error"] == "invalid_grant"
    assert exchange(c, cid, code, verifier).status_code == 200


def test_expired_code(app):
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    code = qs(approve(c, cid, challenge, ["matters:read"]).headers["Location"])["code"]
    from app.extensions import db
    from app.models import OAuthCode, now
    with app.app_context():
        row = OAuthCode.query.one()
        assert row.code_hash != code and len(row.code_hash) == 64       # hashed at rest
        assert row.expires_at - row.created_at <= timedelta(minutes=10, seconds=1)
        row.expires_at = now() - timedelta(seconds=1)
        db.session.commit()
    r = exchange(c, cid, code, verifier)
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_grant"


def test_code_replay_revokes_what_it_issued(app):
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    code = qs(approve(c, cid, challenge, ["matters:read"]).headers["Location"])["code"]
    tok = exchange(c, cid, code, verifier).get_json()
    assert me(app, tok["access_token"]).status_code == 200
    r = exchange(c, cid, code, verifier)
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_grant"
    assert me(app, tok["access_token"]).status_code == 401
    assert refresh(c, cid, tok["refresh_token"]).get_json()["error"] == "invalid_grant"
    with app.app_context():
        from app.models import AuditLog
        assert AuditLog.query.filter_by(action="oauth_code_replay").count() == 1


def test_deny(app):
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    r = approve(c, cid, challenge, ["matters:read"], decision="deny")
    assert r.status_code == 302
    q = qs(r.headers["Location"])
    assert q["error"] == "access_denied" and q["state"] == "st-123" and "code" not in q


def test_consent_post_needs_csrf(app):
    c = app.test_client()
    sign_in(c)
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    data = consent_form(c.get(auth_query(cid, challenge)).data)
    data.pop("_csrf", None)
    data.update({"decision": "approve", "scopes": ["matters:read"]})
    r = c.post("/oauth/authorize", data=data)
    assert r.status_code == 400 and "Location" not in r.headers


def test_redacted_default_and_full_on_request(app):
    c, cid, tok = grant(app)                                  # no confidentiality field posted
    assert me(app, tok["access_token"]).get_json()["token"]["confidentiality"] == "redacted"
    c, cid, tok = grant(app, mode="full")
    assert me(app, tok["access_token"]).get_json()["token"]["confidentiality"] == "full"


def test_scopes_capped_by_role(app):
    c = app.test_client()
    cid = register(c)["client_id"]
    verifier, challenge = pkce()
    sign_in(c, "readonly")
    page = c.get(auth_query(cid, challenge, scope="matters:read matters:write time:write"))
    assert page.status_code == 200
    body = page.data.decode()
    assert 'value="matters:read"' in body
    assert ":write" not in re.sub(r"The app also asked for[^<]*", "", body.split("<form")[1].split("</table>")[0])
    assert "Your role does not allow that" in body
    # Posting write scopes anyway gets them dropped, and the readonly user may post the consent at all.
    data = consent_form(page.data)
    data.update({"decision": "approve", "scopes": ["matters:read", "matters:write", "time:write"]})
    r = c.post("/oauth/authorize", data=data)
    assert r.status_code == 302, r.data[:300]
    tok = exchange(c, cid, qs(r.headers["Location"])["code"], verifier).get_json()
    assert tok["scope"] == "matters:read"
    assert me(app, tok["access_token"]).get_json()["token"]["scopes"] == ["matters:read"]
    # Only write scopes ticked: nothing to grant, so the page asks again rather than issuing a code.
    data["scopes"] = ["time:write"]
    r = c.post("/oauth/authorize", data=data)
    assert r.status_code == 200 and b"Tick at least one" in r.data


def test_refresh_cannot_widen_scope(app):
    c, cid, tok = grant(app, scopes=("matters:read",))
    r = refresh(c, cid, tok["refresh_token"], scope="matters:read time:write")
    assert r.status_code == 400 and r.get_json()["error"] == "invalid_scope"
    r = refresh(c, cid, tok["refresh_token"], scope="matters:read")
    assert r.status_code == 200 and r.get_json()["scope"] == "matters:read"


def test_refresh_token_hashed_and_bound_to_client(app):
    c, cid, tok = grant(app)
    from app.models import OAuthRefreshToken
    with app.app_context():
        row = OAuthRefreshToken.query.one()
        assert row.token_hash != tok["refresh_token"] and len(row.token_hash) == 64
        assert (row.expires_at - row.created_at).days == 60
    other = register(app.test_client())["client_id"]
    assert refresh(c, other, tok["refresh_token"]).get_json()["error"] == "invalid_grant"
    r = c.post("/oauth/token", data={"grant_type": "password", "client_id": cid})
    assert r.get_json()["error"] == "unsupported_grant_type"
    r = c.post("/oauth/token", data={"grant_type": "refresh_token", "refresh_token": "x", "client_id": "nope"})
    assert r.status_code == 401 and r.get_json()["error"] == "invalid_client"


def test_confidential_client_secret(app):
    c = app.test_client()
    reg = register(c, token_endpoint_auth_method="client_secret_post")
    assert reg["client_secret"]
    cid = reg["client_id"]
    verifier, challenge = pkce()
    code = qs(approve(c, cid, challenge, ["matters:read"]).headers["Location"])["code"]
    r = exchange(c, cid, code, verifier)
    assert r.status_code == 401 and r.get_json()["error"] == "invalid_client"
    r = c.post("/oauth/token", data={"grant_type": "authorization_code", "code": code, "client_id": cid,
                                     "client_secret": reg["client_secret"], "redirect_uri": REDIRECT,
                                     "code_verifier": verifier})
    assert r.status_code == 200
    # client_secret_basic works the same way.
    reg = register(c, token_endpoint_auth_method="client_secret_basic")
    basic = base64.b64encode(f"{reg['client_id']}:{reg['client_secret']}".encode()).decode()
    verifier, challenge = pkce()
    code = qs(approve(c, reg["client_id"], challenge, ["matters:read"]).headers["Location"])["code"]
    r = c.post("/oauth/token", data={"grant_type": "authorization_code", "code": code, "redirect_uri": REDIRECT,
                                     "code_verifier": verifier}, headers={"Authorization": f"Basic {basic}"})
    assert r.status_code == 200


# ---------------------------------------------------------------- connected apps

def test_connected_apps_and_disconnect(app):
    c, cid, tok = grant(app, scopes=("matters:read", "time:read"))
    assert me(app, tok["access_token"]).status_code == 200
    page = c.get("/settings/api")
    assert page.status_code == 200
    body = page.data.decode()
    assert "Connected apps" in body and "Claude" in body and "client details withheld" in body
    assert "OAuth: Claude" not in body               # the hourly tokens stay out of the hand-made list
    m = re.search(r'action="(/oauth/connections/\d+/\d+/disconnect)"', body)
    assert m
    # Someone else (not the owner) cannot disconnect it.
    other = app.test_client()
    sign_in(other, "attorney")
    tok_page = other.get("/oauth/connections")
    assert tok_page.status_code == 200 and b"No apps are connected" in tok_page.data
    r = other.post(m.group(1), data={"_csrf": _csrf(tok_page.data)})
    assert r.status_code == 403
    assert me(app, tok["access_token"]).status_code == 200
    # The person who connected it can.
    r = c.post(m.group(1), data={"_csrf": _csrf(page.data), "next": "/settings/api"})
    assert r.status_code == 302 and r.headers["Location"].endswith("/settings/api")
    assert me(app, tok["access_token"]).status_code == 401
    assert refresh(c, cid, tok["refresh_token"]).get_json()["error"] == "invalid_grant"
    assert b"No apps are connected" in c.get("/settings/api").data
    with app.app_context():
        from app.models import AuditLog
        assert AuditLog.query.filter_by(action="oauth_disconnect").count() == 1


def test_owner_sees_and_disconnects_everyones_apps(app):
    c, cid, tok = grant(app, role="attorney")
    owner = app.test_client()
    sign_in(owner, "owner")
    page = owner.get("/settings/api")
    assert b"Test attorney" in page.data and b"Claude" in page.data
    m = re.search(rb'action="(/oauth/connections/\d+/\d+/disconnect)"', page.data)
    r = owner.post(m.group(1).decode(), data={"_csrf": _csrf(page.data)})
    assert r.status_code == 302
    assert me(app, tok["access_token"]).status_code == 401


def test_readonly_can_disconnect_own_app(app):
    c, cid, tok = grant(app, role="readonly")
    page = c.get("/oauth/connections")
    assert page.status_code == 200 and b"Claude" in page.data
    m = re.search(rb'action="(/oauth/connections/\d+/\d+/disconnect)"', page.data)
    r = c.post(m.group(1).decode(), data={"_csrf": _csrf(page.data)})
    assert r.status_code == 302
    assert me(app, tok["access_token"]).status_code == 401


def test_existing_install_gets_tables_and_columns(app, tmp_path):
    """An install from before OAuth: api_tokens lacks the two columns and the OAuth tables are
    missing. Restarting must add both, and old tokens must keep working with no expiry."""
    import sqlite3
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token
    with app.app_context():
        u = User.query.filter_by(email="owner@example.test").first()
        _, raw = create_token(u, "old laptop", ["matters:read"], "full")
        db.session.commit()
        db.session.remove()
        db.engine.dispose()
    path = str(tmp_path / "oauth.db")
    con = sqlite3.connect(path)
    for t in ("oauth_refresh_tokens", "oauth_codes", "oauth_clients"):
        con.execute(f"DROP TABLE {t}")
    # SQLite cannot drop a foreign key column, so rebuild the table as it was before.
    old = ("id, user_id, name, token_hash, prefix, scopes, confidentiality, last_used_at, revoked_at, "
           "created_at")
    con.execute("CREATE TABLE api_tokens_old (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, "
                "name VARCHAR(120), token_hash VARCHAR(80) NOT NULL UNIQUE, prefix VARCHAR(12), "
                "scopes VARCHAR(500), confidentiality VARCHAR(20), last_used_at DATETIME, revoked_at DATETIME, "
                "created_at DATETIME)")
    con.execute(f"INSERT INTO api_tokens_old ({old}) SELECT {old} FROM api_tokens")
    con.execute("DROP TABLE api_tokens")
    con.execute("ALTER TABLE api_tokens_old RENAME TO api_tokens")
    con.commit()
    con.close()
    from app import create_app
    a2 = create_app({"TESTING": True, "SECRET_KEY": "oauth-synthetic", "BASE_URL": BASE,
                     "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}", "UPLOAD_DIR": str(tmp_path / "uploads"),
                     "PDF_DIR": str(tmp_path / "pdf"), "SMTP_HOST": ""})
    con = sqlite3.connect(path)
    cols = {r[1] for r in con.execute("PRAGMA table_info(api_tokens)")}
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    assert {"expires_at", "oauth_client_id"} <= cols
    assert {"oauth_clients", "oauth_codes", "oauth_refresh_tokens"} <= tables
    assert me(a2, raw).status_code == 200
    c, cid, tok = grant(a2)
    assert me(a2, tok["access_token"]).status_code == 200
    with a2.app_context():
        db.session.remove()
        db.engine.dispose()
