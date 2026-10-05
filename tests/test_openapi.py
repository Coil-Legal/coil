"""The OpenAPI description at /api/v1/openapi.json matches the API.

Agents and automation tools build their calls from this file, so a documented path that does
not exist, or an API route left out, is a bug that costs someone a failed integration.

Run: .venv/bin/python -m pytest tests/test_openapi.py -q
"""
import re

from tests.test_phase1_independent import app  # noqa: F401


def _api_routes(app):
    out = set()
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith("/api/v1/") or "<path:" in rule.rule or rule.rule.endswith("/openapi.json"):
            continue
        if rule.rule.startswith("/api/v1/voice/"):
            continue  # the phone agent's own endpoints, with their own sign-in; not part of the public API
        path = re.sub(r"<(?:int:)?([a-z_]+)>", r"{\1}", rule.rule[len("/api/v1"):])
        for m in rule.methods - {"HEAD", "OPTIONS"}:
            out.add((m.lower(), path))
    return out


def test_openapi_is_public_valid_json_and_complete(app):
    r = app.test_client().get("/api/v1/openapi.json")
    assert r.status_code == 200
    spec = r.get_json()
    assert spec["openapi"].startswith("3.1") and spec["servers"][0]["url"].endswith("/api/v1")
    documented = {(m, p) for p, ops in spec["paths"].items() for m in ops}
    routes = _api_routes(app)
    assert documented - routes == set(), f"documented but not routed: {documented - routes}"
    assert routes - documented == set(), f"routed but not documented: {routes - documented}"
    for p, ops in spec["paths"].items():
        for m, op in ops.items():
            assert op["summary"] and op["operationId"], (m, p)


def test_other_api_paths_still_need_a_token(app):
    assert app.test_client().get("/api/v1/matters").status_code == 401
