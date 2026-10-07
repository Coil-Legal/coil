"""Coil QA #172: GET /api/v1/tasks (and the MCP list_tasks tool built on it) ignored the
`done` query param and always returned open tasks, so a completed task could never be
listed through the REST API or MCP.

Reuses the already-seeded app/token fixtures from test_ai_compat_tools.py.

Run: .venv/bin/python -m pytest tests/test_task_done_filter.py -q
"""
from tests.test_ai_compat_tools import ALL_READ, WRITES, _call, _token, app  # noqa: F401


def test_rest_tasks_done_filter(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES, name="done filter test")
    r = c.post("/api/v1/tasks", json={"title": "Done filter task 20261007"}, headers=h)
    assert r.status_code == 201, r.data
    t = r.get_json()["task"]
    r = c.post(f"/api/v1/tasks/{t['id']}/done", json={}, headers=h)
    assert r.status_code == 200 and r.get_json()["task"]["done"] is True

    open_ids = [x["id"] for x in c.get("/api/v1/tasks", headers=h).get_json()["tasks"]]
    assert t["id"] not in open_ids

    done_ids = [x["id"] for x in c.get("/api/v1/tasks?done=true", headers=h).get_json()["tasks"]]
    assert t["id"] in done_ids
    assert all(x["done"] for x in c.get("/api/v1/tasks?done=true", headers=h).get_json()["tasks"])

    explicit_open_ids = [x["id"] for x in c.get("/api/v1/tasks?done=false", headers=h).get_json()["tasks"]]
    assert t["id"] not in explicit_open_ids

    r = c.post(f"/api/v1/tasks/{t['id']}/done", json={"done": False}, headers=h)
    assert r.status_code == 200 and r.get_json()["task"]["done"] is False
    done_ids_after_reopen = [x["id"] for x in c.get("/api/v1/tasks?done=true", headers=h).get_json()["tasks"]]
    assert t["id"] not in done_ids_after_reopen


def test_mcp_list_tasks_done_filter(app):
    c = app.test_client()
    h = _token(app, ALL_READ + WRITES, name="mcp done filter test")
    r = c.post("/api/v1/tasks", json={"title": "MCP done filter task 20261007"}, headers=h)
    task = r.get_json()["task"]
    c.post(f"/api/v1/tasks/{task['id']}/done", json={}, headers=h)

    payload, is_error = _call(c, h, "list_tasks", {"done": True, "matter_id": 0})
    assert is_error is False
    assert any(x["id"] == task["id"] for x in payload["tasks"])

    payload, _ = _call(c, h, "list_tasks", {})
    assert not any(x["id"] == task["id"] for x in payload["tasks"])

    c.post(f"/api/v1/tasks/{task['id']}/done", json={"done": False}, headers=h)
    payload, _ = _call(c, h, "list_tasks", {"done": True})
    assert not any(x["id"] == task["id"] for x in payload["tasks"])
