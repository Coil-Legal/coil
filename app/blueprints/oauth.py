"""OAuth 2.1 for the MCP endpoint, so claude.ai, Claude Desktop and ChatGPT connectors can
connect to a Coil install by URL alone, without anyone pasting a token.

It follows the MCP authorization spec (2025-06-18) and the RFCs it cites:

  RFC 9728  /.well-known/oauth-protected-resource      where /mcp says its tokens come from
  RFC 8414  /.well-known/oauth-authorization-server    what this server supports
  RFC 7591  POST /oauth/register                       an app registers itself
            GET/POST /oauth/authorize                  a signed-in person approves it
  RFC 6749  POST /oauth/token                          code (with PKCE) or refresh for tokens
  RFC 7009  POST /oauth/revoke                         an app gives a token back

The design choice that matters: an access token issued here IS an ApiToken row, with the
scopes and confidentiality mode the person approved, an hour's expiry and the app it was
issued to. The REST API and /mcp therefore accept it through the same code path as a token
made by hand on Settings > API, and nothing in either of them knows OAuth exists. /mcp
still never checks a token itself.

Security choices:
  * PKCE with S256 is required on every authorization. "plain" is refused.
  * Codes and refresh tokens are random, stored only as sha256, and compared by hash lookup
    plus constant-time comparison where a secret is checked directly.
  * The redirect URI must match a registered one exactly. An unknown app or an unregistered
    redirect gets an error page, never a redirect.
  * Codes are single use and last ten minutes. Using one twice revokes every token issued
    from it.
  * Refresh tokens rotate on every use and last 60 days. Presenting a rotated one again
    revokes the whole chain, on the assumption that it leaked.
  * The consent page defaults to withholding client details, and every grant is capped by
    the person's role through api.allowed_scopes(), so an app can never be given more than
    the person approving it could do.
"""
import base64
import hashlib
import hmac
import json
import re
import secrets
import threading
import time as _time
import unicodedata
from collections import deque
from datetime import timedelta
from urllib.parse import urlsplit, urlencode, parse_qsl, urlunsplit, unquote

from flask import (Blueprint, request, jsonify, current_app, render_template, redirect, url_for, flash,
                   abort, make_response)

from ..extensions import db
from ..models import ApiToken, OAuthClient, OAuthCode, OAuthRefreshToken, User, audit, now
from ..helpers import current_user, client_ip
from .api import ALL_SCOPES, RESOURCES, RESOURCE_LABELS, allowed_scopes, create_token, hash_token

bp = Blueprint("oauth", __name__)

ACCESS_TOKEN_TTL = 3600                      # seconds
REFRESH_TOKEN_TTL = timedelta(days=60)
CODE_TTL = timedelta(minutes=10)
GRANT_TYPES = ("authorization_code", "refresh_token")
AUTH_METHODS = ("none", "client_secret_post", "client_secret_basic")
MAX_REDIRECT_URIS = 10

# Registration is open to anyone on the internet, as RFC 7591 intends, so it is limited per
# address and overall. The address comes from client_ip(), which trusts the first
# X-Forwarded-For entry; a caller who forges that only escapes the per-address limit, and the
# overall ceiling still holds.
REGISTER_PER_IP = 20
REGISTER_GLOBAL = 300
REGISTER_WINDOW = 3600.0
_reg = {}
_reg_lock = threading.Lock()

# Answered for any origin. None of these read the session cookie, so allowing every origin
# (without credentials) gives a web page nothing it could not do from a server.
CORS_PATHS = ("/.well-known/oauth-protected-resource", "/.well-known/oauth-authorization-server",
              "/oauth/token", "/oauth/register", "/oauth/revoke", "/mcp")
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, Mcp-Protocol-Version, Mcp-Session-Id",
    "Access-Control-Expose-Headers": "WWW-Authenticate, Mcp-Session-Id",
    "Access-Control-Max-Age": "600",
}

_PKCE = re.compile(r"^[A-Za-z0-9\-._~]{43,128}$")


# ---------------------------------------------------------------- small helpers

def base_url():
    return current_app.config["BASE_URL"].rstrip("/")


def resource_url():
    return base_url() + "/mcp"


def metadata_url():
    return base_url() + "/.well-known/oauth-protected-resource"


def www_authenticate(had_token=False):
    """The 401 challenge /mcp sends, pointing the client at the metadata (RFC 9728 s5.1)."""
    v = f'Bearer resource_metadata="{metadata_url()}"'
    if had_token:
        v += ', error="invalid_token"'
    return v


def _sha(raw):
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def _scope_list(raw):
    """Space or comma separated scope string -> supported scopes, in canonical order."""
    parts = set(re.split(r"[\s,]+", raw or "")) if not isinstance(raw, (list, tuple, set)) else set(raw)
    return [s for s in ALL_SCOPES if s in parts]


def _clean_name(v):
    v = "".join(ch for ch in str(v or "") if unicodedata.category(ch)[0] != "C")
    return " ".join(v.split())[:200]


def _json_error(error, description, status=400, headers=None):
    resp = jsonify({"error": error, "error_description": description})
    resp.status_code = status
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    for k, v in (headers or {}).items():
        resp.headers[k] = v
    return resp


def _no_store(resp):
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Pragma"] = "no-cache"
    return resp


def _with_params(uri, params):
    """Add query parameters to a registered redirect URI, keeping any it already had."""
    parts = urlsplit(uri)
    q = parse_qsl(parts.query, keep_blank_values=True) + [(k, v) for k, v in params.items() if v is not None]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), ""))


def valid_redirect_uri(uri):
    """https anywhere, or http only on this machine (for desktop apps listening locally)."""
    if not isinstance(uri, str) or not uri or len(uri) > 1000:
        return False
    try:
        p = urlsplit(uri)
    except ValueError:
        return False
    if p.fragment or not p.netloc or "\\" in uri or any(ch.isspace() for ch in uri):
        return False
    if p.scheme == "https":
        return bool(p.hostname)
    if p.scheme == "http":
        return p.hostname in ("localhost", "127.0.0.1")
    return False


def _resource_ok(resource):
    """RFC 8707: the resource, when sent, must be this server's MCP endpoint (or its origin)."""
    if not resource:
        return True
    want = {resource_url(), base_url(), request.host_url.rstrip("/") + "/mcp", request.host_url.rstrip("/")}
    return resource.rstrip("/") in want


def _register_limited(ip):
    t = _time.monotonic()
    with _reg_lock:
        everyone = _reg.setdefault("*", deque())
        mine = _reg.setdefault(ip or "unknown", deque())
        for dq in (everyone, mine):
            while dq and dq[0] <= t - REGISTER_WINDOW:
                dq.popleft()
        if len(mine) >= REGISTER_PER_IP or len(everyone) >= REGISTER_GLOBAL:
            return True
        mine.append(t)
        everyone.append(t)
    return False


def reset_register_limits():
    with _reg_lock:
        _reg.clear()


# ---------------------------------------------------------------- CORS

def _cors_path(path):
    return any(path == p or path.startswith(p + "/") for p in CORS_PATHS)


@bp.before_app_request
def _preflight():
    if request.method == "OPTIONS" and _cors_path(request.path):
        resp = make_response("", 204)
        resp.headers.update(CORS_HEADERS)
        return resp
    return None


@bp.after_app_request
def _cors(resp):
    if _cors_path(request.path):
        for k, v in CORS_HEADERS.items():
            resp.headers.setdefault(k, v)
    return resp


# ---------------------------------------------------------------- metadata

def _protected_resource():
    return _no_store(jsonify({
        "resource": resource_url(),
        "authorization_servers": [base_url()],
        "scopes_supported": list(ALL_SCOPES),
        "bearer_methods_supported": ["header"],
        "resource_name": "Coil",
    }))


@bp.route("/.well-known/oauth-protected-resource", methods=["GET"])
@bp.route("/.well-known/oauth-protected-resource/mcp", methods=["GET"])
def protected_resource():
    return _protected_resource()


@bp.route("/.well-known/oauth-authorization-server", methods=["GET"])
@bp.route("/.well-known/oauth-authorization-server/mcp", methods=["GET"])
def authorization_server():
    b = base_url()
    return _no_store(jsonify({
        "issuer": b,
        "authorization_endpoint": b + "/oauth/authorize",
        "token_endpoint": b + "/oauth/token",
        "registration_endpoint": b + "/oauth/register",
        "revocation_endpoint": b + "/oauth/revoke",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query"],
        "grant_types_supported": list(GRANT_TYPES),
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": list(AUTH_METHODS),
        "revocation_endpoint_auth_methods_supported": list(AUTH_METHODS),
        "scopes_supported": list(ALL_SCOPES),
    }))


# ---------------------------------------------------------------- registration (RFC 7591)

@bp.route("/oauth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _json_error("invalid_client_metadata", "Send the client metadata as a JSON object.")
    if _register_limited(client_ip()):
        return _json_error("invalid_request", "Too many registrations from this address. Try again later.", 429,
                           {"Retry-After": "3600"})

    uris = body.get("redirect_uris")
    if not isinstance(uris, list) or not uris:
        return _json_error("invalid_redirect_uri", "redirect_uris is required and must be a list.")
    if len(uris) > MAX_REDIRECT_URIS:
        return _json_error("invalid_redirect_uri", f"Register at most {MAX_REDIRECT_URIS} redirect URIs.")
    for u in uris:
        if not valid_redirect_uri(u):
            return _json_error("invalid_redirect_uri",
                               "Each redirect URI must use https, or http on localhost or 127.0.0.1, "
                               "and must not carry a fragment.")

    grants = body.get("grant_types") or ["authorization_code", "refresh_token"]
    if not isinstance(grants, list) or not grants or any(gt not in GRANT_TYPES for gt in grants):
        return _json_error("invalid_client_metadata", "grant_types may only be authorization_code and refresh_token.")
    if "authorization_code" not in grants:
        return _json_error("invalid_client_metadata", "grant_types must include authorization_code.")
    rtypes = body.get("response_types") or ["code"]
    if not isinstance(rtypes, list) or any(rt != "code" for rt in rtypes):
        return _json_error("invalid_client_metadata", "response_types may only be code.")
    method = body.get("token_endpoint_auth_method") or "none"
    if method not in AUTH_METHODS:
        return _json_error("invalid_client_metadata",
                           "token_endpoint_auth_method must be none, client_secret_post or client_secret_basic.")

    # A client may narrow what it will ask for, never widen it. Anything Coil does not
    # support is dropped rather than refused, so a client listing extra scopes still works.
    scope = " ".join(_scope_list(body.get("scope") or ""))
    name = _clean_name(body.get("client_name")) or "Unnamed app"

    secret = None
    c = OAuthClient(client_id="coilc_" + secrets.token_urlsafe(24), client_name=name,
                    redirect_uris_json=json.dumps(list(uris)), grant_types=",".join(grants),
                    token_endpoint_auth_method=method, scope=scope, created_ip=(client_ip() or "")[:64])
    if method != "none":
        secret = "coils_" + secrets.token_urlsafe(32)
        c.client_secret_hash = _sha(secret)
    db.session.add(c)
    db.session.flush()
    audit("oauth_client_register", "oauth_client", c.id, f"{name} ({', '.join(uris)})")
    db.session.commit()

    out = {"client_id": c.client_id, "client_id_issued_at": int(_time.time()), "client_name": name,
           "redirect_uris": list(uris), "grant_types": grants, "response_types": ["code"],
           "token_endpoint_auth_method": method}
    if scope:
        out["scope"] = scope
    if secret:
        out["client_secret"] = secret
        out["client_secret_expires_at"] = 0
    resp = jsonify(out)
    resp.status_code = 201
    return _no_store(resp)


# ---------------------------------------------------------------- authorize

def _error_page(message, status=400):
    resp = make_response(render_template("oauth/error.html", message=message), status)
    return resp


def _validate_request(src):
    """Check an authorization request. Returns (ctx, None) or (None, response).

    Every problem is an error page, never a redirect. Anyone can register any https
    redirect URI, so bouncing a malformed request straight back to it would make this
    endpoint an open redirector (RFC 9700 s4.11.2). The app only gets an OAuth error on its
    redirect after a signed-in person chooses Deny.
    """
    client = OAuthClient.query.filter_by(client_id=(src.get("client_id") or "").strip()).first() \
        if src.get("client_id") else None
    if not client:
        return None, _error_page("This app is not registered with Coil. Remove the connector in the app "
                                 "and add it again so it can register itself.")
    registered = client.redirect_uris
    redirect_uri = src.get("redirect_uri") or ""
    if not redirect_uri and len(registered) == 1:
        redirect_uri = registered[0]
    if redirect_uri not in registered:
        return None, _error_page("The app asked Coil to send you to an address it did not register. "
                                 "Coil stopped here rather than send you somewhere unknown.")
    state = src.get("state")

    def back(error, description):
        return None, _error_page(f"The app sent a request Coil cannot accept ({error}): {description} "
                                 "Try connecting again from the app. If it keeps happening, the app may "
                                 "not support how Coil connects.")

    if src.get("response_type") != "code":
        return back("unsupported_response_type", "Only response_type=code is supported.")
    challenge = src.get("code_challenge") or ""
    if not challenge:
        return back("invalid_request", "PKCE is required: send code_challenge with code_challenge_method=S256.")
    if (src.get("code_challenge_method") or "") != "S256":
        return back("invalid_request", "Only the S256 code_challenge_method is supported.")
    if not _PKCE.match(challenge):
        return back("invalid_request", "code_challenge is not a valid S256 challenge.")
    resource = (src.get("resource") or "").strip()
    if not _resource_ok(resource):
        return back("invalid_target", "This server only issues tokens for its own MCP endpoint.")
    requested = _scope_list(src.get("scope") or "")
    if client.scope:
        requested = [s for s in requested if s in client.scope.split()]
    return {"client": client, "redirect_uri": redirect_uri, "state": state, "code_challenge": challenge,
            "resource": resource, "requested": requested, "scope_raw": src.get("scope") or ""}, None


def _offerable(client, user):
    """Scopes the consent page may offer: the person's role caps it, and so does the app's registration."""
    allowed = allowed_scopes(user)
    out = [s for s in ALL_SCOPES if s in allowed]
    if client.scope:
        out = [s for s in out if s in client.scope.split()]
    return out


def _consent(ctx, user, picked=None, error=None):
    offer = _offerable(ctx["client"], user)
    if picked is None:
        picked = [s for s in ctx["requested"] if s in offer]
        if not ctx["requested"]:
            # Nothing named: start from reading everything the person can read, and nothing written.
            picked = [s for s in offer if s.endswith(":read")]
    trimmed = [s for s in ctx["requested"] if s not in offer]
    host = urlsplit(ctx["redirect_uri"]).hostname or ctx["redirect_uri"]
    resp = make_response(render_template(
        "oauth/consent.html", client=ctx["client"], host=host, user=user, resources=RESOURCES,
        resource_labels=RESOURCE_LABELS, offer=offer, picked=set(picked), trimmed=trimmed, error=error,
        params={"client_id": ctx["client"].client_id, "redirect_uri": ctx["redirect_uri"],
                "state": ctx["state"] or "", "code_challenge": ctx["code_challenge"],
                "code_challenge_method": "S256", "response_type": "code", "resource": ctx["resource"],
                "scope": ctx["scope_raw"]}))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@bp.route("/oauth/authorize", methods=["GET"])
def authorize():
    ctx, bad = _validate_request(request.args)
    if bad is not None:
        return bad
    user = current_user()
    if not user or not user.is_active:
        return redirect(url_for("auth.login", next=request.full_path))
    if not _offerable(ctx["client"], user):
        return _error_page("Your role in Coil does not allow access to anything an app could connect to. "
                           "Ask the firm owner if you need it.", 403)
    return _consent(ctx, user)


@bp.route("/oauth/authorize", methods=["POST"])
def authorize_decide():
    # check_csrf() has already run: this is the one OAuth POST that is not CSRF exempt.
    user = current_user()
    if not user or not user.is_active:
        return redirect(url_for("auth.login"))
    ctx, bad = _validate_request(request.form)
    if bad is not None:
        return bad
    client = ctx["client"]
    if request.form.get("decision") != "approve":
        audit("oauth_deny", "oauth_client", client.id, client.client_name, user.id)
        db.session.commit()
        return redirect(_with_params(ctx["redirect_uri"], {"error": "access_denied",
                                                            "error_description": "The request was declined.",
                                                            "state": ctx["state"]}))
    offer = _offerable(client, user)
    picked = [s for s in ALL_SCOPES if s in set(request.form.getlist("scopes")) and s in offer]
    if not picked:
        return _consent(ctx, user, picked=[], error="Tick at least one thing the app may do, or choose Deny.")
    mode = "full" if request.form.get("confidentiality") == "full" else "redacted"
    raw = secrets.token_urlsafe(32)
    code = OAuthCode(code_hash=_sha(raw), oauth_client_id=client.id, user_id=user.id,
                     redirect_uri=ctx["redirect_uri"], scopes=",".join(picked), confidentiality=mode,
                     code_challenge=ctx["code_challenge"], resource=ctx["resource"],
                     expires_at=now() + CODE_TTL)
    db.session.add(code)
    db.session.flush()
    audit("oauth_authorize", "oauth_client", client.id, f"{client.client_name} [{mode}] ({','.join(picked)})", user.id)
    db.session.commit()
    return redirect(_with_params(ctx["redirect_uri"], {"code": raw, "state": ctx["state"]}))


# ---------------------------------------------------------------- token

def _client_from_request():
    """Identify and authenticate the client. Returns (client, None) or (None, error response)."""
    form = request.form
    cid, secret, basic = form.get("client_id"), form.get("client_secret"), False
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("basic "):
        try:
            dec = base64.b64decode(auth[6:].strip()).decode("utf-8")
            u, _, p = dec.partition(":")
            cid, secret, basic = unquote(u), unquote(p), True
        except (ValueError, UnicodeDecodeError):
            return None, _json_error("invalid_client", "Malformed Basic credentials.", 401,
                                     {"WWW-Authenticate": 'Basic realm="coil"'})
    if not cid:
        return None, _json_error("invalid_client", "client_id is required.", 401)
    client = OAuthClient.query.filter_by(client_id=cid).first()
    if not client:
        return None, _json_error("invalid_client", "Unknown client.", 401)
    if client.token_endpoint_auth_method != "none":
        if not secret or not client.client_secret_hash or \
                not hmac.compare_digest(_sha(secret), client.client_secret_hash):
            return None, _json_error("invalid_client", "Client authentication failed.", 401,
                                     {"WWW-Authenticate": 'Basic realm="coil"'} if basic else None)
    return client, None


def _pkce_ok(verifier, challenge):
    if not verifier or not _PKCE.match(verifier):
        return False
    digest = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).rstrip(b"=").decode()
    return hmac.compare_digest(digest, challenge or "")


def revoke_chain(chain):
    """Revoke every refresh token in a chain and every access token they issued."""
    t = now()
    rows = OAuthRefreshToken.query.filter_by(chain=chain).all()
    ids = [r.access_token_id for r in rows if r.access_token_id]
    for r in rows:
        if not r.revoked_at:
            r.revoked_at = t
    if ids:
        for tok in ApiToken.query.filter(ApiToken.id.in_(ids), ApiToken.revoked_at.is_(None)).all():
            tok.revoked_at = t
    return len(rows)


def _issue(client, user, scopes, mode, chain, code_id=None, granted_at=None):
    """Mint an access token (an ApiToken) and a refresh token. Raises ValueError when the
    person's role no longer covers any of the scopes."""
    t = now()
    tok, raw_access = create_token(user, f"OAuth: {client.client_name}"[:120], scopes, mode)
    tok.created_at = t
    tok.expires_at = t + timedelta(seconds=ACCESS_TOKEN_TTL)
    tok.oauth_client_id = client.id
    db.session.flush()
    raw_refresh = "coilr_" + secrets.token_urlsafe(32)
    rt = OAuthRefreshToken(token_hash=_sha(raw_refresh), oauth_client_id=client.id, user_id=user.id,
                           scopes=tok.scopes, confidentiality=tok.confidentiality, chain=chain, code_id=code_id,
                           access_token_id=tok.id, granted_at=granted_at or t, created_at=t,
                           expires_at=t + REFRESH_TOKEN_TTL)
    db.session.add(rt)
    db.session.flush()
    body = {"access_token": raw_access, "token_type": "Bearer", "expires_in": ACCESS_TOKEN_TTL,
            "refresh_token": raw_refresh, "scope": " ".join(tok.scopes.split(","))}
    return tok, body


def _grant_code(client):
    f = request.form
    raw, redirect_uri, verifier = f.get("code"), f.get("redirect_uri"), f.get("code_verifier")
    if not raw or not verifier:
        return _json_error("invalid_request", "code and code_verifier are required.")
    code = OAuthCode.query.filter_by(code_hash=_sha(raw)).first()
    if not code or code.oauth_client_id != client.id:
        return _json_error("invalid_grant", "The authorization code is not valid.")
    if code.used_at:
        # Replay. Whoever holds this code is not who it was issued to, or something is
        # retrying blindly. Either way, nothing issued from it can be trusted any more.
        chains = {r.chain for r in OAuthRefreshToken.query.filter_by(code_id=code.id).all()}
        for ch in chains:
            revoke_chain(ch)
        audit("oauth_code_replay", "oauth_client", client.id,
              f"{client.client_name}: authorization code used twice; {len(chains)} grant(s) revoked", code.user_id)
        db.session.commit()
        return _json_error("invalid_grant", "The authorization code has already been used.")
    if not code.expires_at or code.expires_at <= now():
        return _json_error("invalid_grant", "The authorization code has expired.")
    if (redirect_uri or code.redirect_uri) != code.redirect_uri:
        return _json_error("invalid_grant", "redirect_uri does not match the authorization request.")
    if not _pkce_ok(verifier, code.code_challenge):
        return _json_error("invalid_grant", "code_verifier does not match the code_challenge.")
    resource = (f.get("resource") or "").strip()
    if not _resource_ok(resource):
        return _json_error("invalid_target", "This server only issues tokens for its own MCP endpoint.")
    user = db.session.get(User, code.user_id)
    if not user or not user.is_active:
        return _json_error("invalid_grant", "The person who approved this is no longer active.")
    # Claim the code atomically so two simultaneous exchanges cannot both succeed.
    claimed = OAuthCode.query.filter_by(id=code.id, used_at=None).update({"used_at": now()},
                                                                         synchronize_session=False)
    if not claimed:
        db.session.rollback()
        return _json_error("invalid_grant", "The authorization code has already been used.")
    try:
        tok, body = _issue(client, user, code.scopes, code.confidentiality, secrets.token_urlsafe(24),
                           code_id=code.id)
    except ValueError:
        db.session.commit()
        return _json_error("invalid_grant", "Your role no longer allows any of what was approved.")
    audit("oauth_token_issue", "api_token", tok.id,
          f"{client.client_name} [{tok.confidentiality}] ({tok.scopes})", user.id)
    db.session.commit()
    return _no_store(jsonify(body))


def _grant_refresh(client):
    f = request.form
    raw = f.get("refresh_token")
    if not raw:
        return _json_error("invalid_request", "refresh_token is required.")
    rt = OAuthRefreshToken.query.filter_by(token_hash=_sha(raw)).first()
    if not rt or rt.oauth_client_id != client.id or rt.revoked_at:
        return _json_error("invalid_grant", "The refresh token is not valid.")
    if rt.rotated_at:
        n = revoke_chain(rt.chain)
        audit("oauth_refresh_reuse", "oauth_client", client.id,
              f"{client.client_name}: a replaced refresh token was used again; {n} token(s) in the chain revoked",
              rt.user_id)
        db.session.commit()
        return _json_error("invalid_grant", "The refresh token has already been used.")
    if not rt.expires_at or rt.expires_at <= now():
        return _json_error("invalid_grant", "The refresh token has expired. Connect the app again.")
    user = db.session.get(User, rt.user_id)
    if not user or not user.is_active:
        return _json_error("invalid_grant", "The person who approved this is no longer active.")
    scopes = rt.scopes.split(",") if rt.scopes else []
    if f.get("scope"):
        asked = _scope_list(f.get("scope"))
        if not asked or any(s not in scopes for s in asked):
            return _json_error("invalid_scope", "A refresh cannot add scopes that were not approved.")
        scopes = asked
    claimed = OAuthRefreshToken.query.filter_by(id=rt.id, rotated_at=None, revoked_at=None) \
        .update({"rotated_at": now()}, synchronize_session=False)
    if not claimed:
        db.session.rollback()
        n = revoke_chain(rt.chain)
        audit("oauth_refresh_reuse", "oauth_client", client.id,
              f"{client.client_name}: a refresh token was used twice at once; {n} token(s) in the chain revoked",
              rt.user_id)
        db.session.commit()
        return _json_error("invalid_grant", "The refresh token has already been used.")
    try:
        tok, body = _issue(client, user, scopes, rt.confidentiality, rt.chain, code_id=rt.code_id,
                           granted_at=rt.granted_at)
    except ValueError:
        revoke_chain(rt.chain)
        db.session.commit()
        return _json_error("invalid_grant", "Your role no longer allows any of what was approved.")
    audit("oauth_token_refresh", "api_token", tok.id,
          f"{client.client_name} [{tok.confidentiality}] ({tok.scopes})", user.id)
    db.session.commit()
    return _no_store(jsonify(body))


@bp.route("/oauth/token", methods=["POST"])
def token():
    client, bad = _client_from_request()
    if bad is not None:
        return bad
    grant = request.form.get("grant_type")
    if grant not in GRANT_TYPES:
        return _json_error("unsupported_grant_type", "grant_type must be authorization_code or refresh_token.")
    if grant not in (client.grant_types or "").split(","):
        return _json_error("unauthorized_client", "This client did not register for that grant type.")
    return _grant_code(client) if grant == "authorization_code" else _grant_refresh(client)


# ---------------------------------------------------------------- revocation (RFC 7009)

@bp.route("/oauth/revoke", methods=["POST"])
def revoke():
    client, bad = _client_from_request()
    if bad is not None:
        return bad
    raw = request.form.get("token") or ""
    hint = request.form.get("token_type_hint") or ""
    if not raw:
        return _json_error("invalid_request", "token is required.")
    order = ("access", "refresh") if hint == "access_token" else ("refresh", "access")
    for kind in order:
        if kind == "refresh":
            rt = OAuthRefreshToken.query.filter_by(token_hash=_sha(raw)).first()
            if rt and rt.oauth_client_id == client.id:
                revoke_chain(rt.chain)
                audit("oauth_revoke", "oauth_client", client.id, f"{client.client_name}: refresh token revoked",
                      rt.user_id)
                db.session.commit()
                break
        else:
            tok = ApiToken.query.filter_by(token_hash=hash_token(raw)).first()
            if tok and tok.oauth_client_id == client.id:
                if not tok.revoked_at:
                    tok.revoked_at = now()
                    audit("oauth_revoke", "api_token", tok.id, f"{client.client_name}: access token revoked",
                          tok.user_id)
                    db.session.commit()
                break
    # RFC 7009: the answer is the same whether or not the token was known.
    return _no_store(make_response("", 200))


# ---------------------------------------------------------------- connected apps

def connected_apps(user, everyone=False):
    """Apps holding a live grant, one row per (app, person). Owners may ask for everyone's."""
    t = now()
    q = OAuthRefreshToken.query.filter(OAuthRefreshToken.revoked_at.is_(None),
                                       OAuthRefreshToken.rotated_at.is_(None),
                                       OAuthRefreshToken.expires_at > t)
    aq = ApiToken.query.filter(ApiToken.oauth_client_id.isnot(None), ApiToken.revoked_at.is_(None),
                               ApiToken.expires_at > t)
    if not everyone:
        q = q.filter(OAuthRefreshToken.user_id == user.id)
        aq = aq.filter(ApiToken.user_id == user.id)
    groups = {}
    for r in q.order_by(OAuthRefreshToken.created_at).all():
        g_ = groups.setdefault((r.oauth_client_id, r.user_id), {"client": r.client, "user": r.user,
                                                                "connected_at": r.granted_at})
        g_["scopes"], g_["confidentiality"] = r.scopes, r.confidentiality
        if r.granted_at and (not g_["connected_at"] or r.granted_at < g_["connected_at"]):
            g_["connected_at"] = r.granted_at
    for a in aq.order_by(ApiToken.created_at).all():
        g_ = groups.setdefault((a.oauth_client_id, a.user_id), {
            "client": db.session.get(OAuthClient, a.oauth_client_id), "user": a.user, "connected_at": a.created_at,
            "scopes": a.scopes, "confidentiality": a.confidentiality})
    for (cid, uid), g_ in groups.items():
        last = db.session.query(db.func.max(ApiToken.last_used_at)).filter(
            ApiToken.oauth_client_id == cid, ApiToken.user_id == uid).scalar()
        g_["last_used_at"] = last
        g_["scope_list"] = [s for s in (g_.get("scopes") or "").split(",") if s]
    return sorted(groups.values(), key=lambda g_: (g_["user"].name if g_["user"] else "", g_["client"].client_name
                                                   if g_["client"] else ""))


def _safe_back(v):
    return v if v in ("/settings/api", "/oauth/connections") else "/oauth/connections"


@bp.route("/oauth/connections")
def connections():
    """Every signed-in person can see and disconnect their own apps here, including roles
    that cannot open Settings > API (readonly)."""
    user = current_user()
    if not user:
        return redirect(url_for("auth.login", next=request.path))
    owner = user.role == "owner"
    return render_template("oauth/connections.html", apps=connected_apps(user, everyone=owner), is_owner=owner,
                           mcp_url=resource_url())


@bp.route("/oauth/connections/<int:client_pk>/<int:user_id>/disconnect", methods=["POST"])
def disconnect(client_pk, user_id):
    user = current_user()
    if not user:
        return redirect(url_for("auth.login"))
    if user.id != user_id and user.role != "owner":
        abort(403)
    client = db.session.get(OAuthClient, client_pk) or abort(404)
    t = now()
    n = 0
    for r in OAuthRefreshToken.query.filter_by(oauth_client_id=client.id, user_id=user_id, revoked_at=None).all():
        r.revoked_at = t
        n += 1
    for tok in ApiToken.query.filter_by(oauth_client_id=client.id, user_id=user_id, revoked_at=None).all():
        tok.revoked_at = t
        n += 1
    who = db.session.get(User, user_id)
    audit("oauth_disconnect", "oauth_client", client.id,
          f"{client.client_name} disconnected for {who.name if who else user_id}; {n} token(s) revoked", user.id)
    db.session.commit()
    flash(f"{client.client_name} is disconnected. It can no longer reach Coil unless someone approves it again.", "ok")
    return redirect(_safe_back(request.form.get("next")))
