"""CLI dispatch and backup safety.

Two regressions this guards against, both shipped once already:
  1. An unknown command fell through to the reminders branch, so a typo emailed every
     client with an open invoice instead of printing usage.
  2. backup() tarred the live SQLite file, which can capture a torn database.
"""
import os
import subprocess
import sys
import sqlite3
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _run(args, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    return subprocess.run([sys.executable, "-m", "app.cli", *args],
                          cwd=ROOT, env=env, capture_output=True, text=True)


def test_unknown_command_exits_2_without_building_the_app():
    """No DATABASE_URL is set, so if this reaches create_app it would touch the real DB."""
    r = _run(["not-a-command"])
    assert r.returncode == 2
    assert "unknown command" in r.stdout
    assert "sent" not in r.stdout  # never ran reminders


def test_no_args_exits_2_and_lists_commands():
    r = _run([])
    assert r.returncode == 2
    for cmd in ("agenda", "reminders", "backup", "payment_plans"):
        assert cmd in r.stdout


def test_backup_snapshots_the_database_and_bundles_uploads(tmp_path):
    db = tmp_path / "practice.db"
    env = {"DATABASE_URL": f"sqlite:///{db}"}
    subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")],
                   check=True, cwd=ROOT, env={**os.environ, **env})

    from app import create_app
    from app.cli import backup
    import app.cli as cli
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": env["DATABASE_URL"]})

    data_dir = tmp_path / "data"
    (data_dir / "uploads").mkdir(parents=True)
    (data_dir / "uploads" / "note.txt").write_text("hello")
    cli.DATA_DIR = str(data_dir)

    with app.app_context():
        out = backup()

    assert out.parent == data_dir / "backups", "backups must sit inside the mounted data dir"
    names = set(tarfile.open(out).getnames())
    assert "data/practice.db" in names
    assert "data/uploads/note.txt" in names
    assert not (data_dir / ".backup-snapshot.db").exists()  # snapshot cleaned up

    extract = tmp_path / "restored"
    tarfile.open(out).extractall(extract, filter="data")
    con = sqlite3.connect(extract / "data" / "practice.db")
    assert con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert con.execute("SELECT count(*) FROM matters").fetchone()[0] > 0
    con.close()


# --- login rate limiting -------------------------------------------------------------
# Successful logins used to count toward the per-IP limit, so ten normal sign-ins in five
# minutes locked out everyone behind one office IP. It also made the test suite fail once
# enough tests had logged in.
import re
import pytest

DB_PATH = os.path.join(ROOT, "data", "test_cli_auth.db")
DB_URI = f"sqlite:///{DB_PATH}"


@pytest.fixture(scope="module")
def auth_app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = dict(os.environ, DATABASE_URL=DB_URI)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True})


def _post_login(c, password):
    r = c.get("/login")
    m = re.search(rb'name="_csrf" value="([^"]+)"', r.data)
    tok = m.group(1).decode() if m else None
    return c.post("/login", data={"email": "owner@example.com", "password": password, "_csrf": tok})


def test_many_successful_logins_are_not_rate_limited(auth_app):
    for i in range(25):
        c = auth_app.test_client()
        assert _post_login(c, "password123").status_code == 302, f"locked out on sign-in {i + 1}"


def test_repeated_wrong_passwords_still_lock_out(auth_app):
    auth_app.config.pop("_login_attempts", None)
    c = auth_app.test_client()
    for _ in range(10):
        assert _post_login(c, "wrong").status_code == 200
    r = _post_login(c, "password123")  # right password, but the door is shut now
    assert r.status_code == 200
    assert b"Too many login attempts" in r.data


def test_a_good_password_clears_the_failure_run(auth_app):
    auth_app.config.pop("_login_attempts", None)
    c = auth_app.test_client()
    for _ in range(9):
        assert _post_login(c, "wrong").status_code == 200
    assert _post_login(c, "password123").status_code == 302
    for _ in range(9):  # counter reset, so nine more failures do not lock
        assert _post_login(c, "wrong").status_code == 200
    assert _post_login(c, "password123").status_code == 302


# --- health endpoint -----------------------------------------------------------------
# /health referenced current_app without importing it, so it returned 500 from the day it
# was written. The self-updater polls it to decide whether a new build came up, which
# means a broken health check would have made every update look like a failure and roll
# back a perfectly good release.
def test_health_reports_the_build_without_touching_the_database(auth_app):
    c = auth_app.test_client()
    r = c.get("/health")
    assert r.status_code == 200, r.data[:200]
    body = r.get_json()
    assert body["status"] == "healthy"
    for key in ("version", "commit", "channel"):
        assert key in body, f"/health must report {key}"


def test_every_listed_blueprint_actually_exists():
    """A name in the registration list with no module logs a warning on every startup and
    every cron run. Six dead names were doing that and burying real warnings."""
    import re
    src = open(os.path.join(ROOT, "app", "__init__.py")).read()
    listed = re.search(r"for modname in \((.*?)\):", src, re.S).group(1)
    names = [n.strip().strip('"') for n in listed.replace("\n", "").split(",") if n.strip()]
    assert names, "could not parse the blueprint list"
    missing = [n for n in names
               if not os.path.exists(os.path.join(ROOT, "app", "blueprints", f"{n}.py"))]
    assert not missing, f"listed but not present: {missing}"


def test_backup_keeps_only_the_newest_archives(tmp_path):
    """Unbounded backups fill the disk, which takes Coil down for the same reason having
    no backup would."""
    db = tmp_path / "practice.db"
    env = {"DATABASE_URL": f"sqlite:///{db}"}
    subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")],
                   check=True, cwd=ROOT, env={**os.environ, **env})
    from app import create_app
    import app.cli as cli
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": env["DATABASE_URL"]})
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    cli.DATA_DIR = str(data_dir)
    os.environ["COIL_BACKUP_KEEP"] = "3"
    try:
        with app.app_context():
            for _ in range(5):
                cli.backup()
    finally:
        os.environ.pop("COIL_BACKUP_KEEP", None)
    kept = sorted((data_dir / "backups").glob("coil-backup-*.tar.gz"))
    assert len(kept) == 3, [p.name for p in kept]


def test_two_backups_in_the_same_second_do_not_overwrite_each_other(tmp_path):
    """The filename is second-resolution, and the nightly cron and an update can land
    together. Without a suffix the second one silently replaces the first."""
    db = tmp_path / "practice.db"
    env = {"DATABASE_URL": f"sqlite:///{db}"}
    subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")],
                   check=True, cwd=ROOT, env={**os.environ, **env})
    from app import create_app
    import app.cli as cli
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": env["DATABASE_URL"]})
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    cli.DATA_DIR = str(data_dir)
    with app.app_context():
        a = cli.backup()
        b = cli.backup()
    assert a != b, "the second backup overwrote the first"
    assert a.exists() and b.exists()


# --- OpenRouter routing ---------------------------------------------------------------
# Coil's prompts carry client matters. OpenRouter picks a provider on price and speed
# unless told otherwise, and its default data policy permits providers that retain and
# train on prompts, so the routing block is the part that actually keeps the promise the
# confidentiality settings make.
def test_openrouter_requests_are_pinned_to_zero_retention_providers(auth_app, monkeypatch):
    import app.llm as llm
    seen = {}

    class R:
        status_code = 200
        text = ""
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    def fake_post(url, headers=None, json=None, timeout=None):
        seen["url"] = url
        seen["payload"] = json
        return R()

    monkeypatch.setattr(llm.requests, "post", fake_post)
    with auth_app.app_context():
        auth_app.config["OPENROUTER_API_KEY"] = "test-key"
        llm._openrouter("anthropic/claude-haiku-4.5", "hello", "", 256, None, None)

    prov = seen["payload"].get("provider")
    assert prov, "no provider block: the prompt could be routed to a provider that trains on it"
    assert prov.get("zdr") is True
    assert prov.get("data_collection") == "deny"


def test_the_routing_restriction_can_be_lifted_deliberately(auth_app, monkeypatch):
    """A firm on a private endpoint may need the wider pool. It has to be a choice."""
    import app.llm as llm

    class R:
        status_code = 200
        text = ""
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    seen = {}
    monkeypatch.setattr(llm.requests, "post",
                        lambda url, headers=None, json=None, timeout=None: (seen.update(payload=json), R())[1])
    monkeypatch.setenv("AI_OPENROUTER_ZDR", "0")
    monkeypatch.setenv("AI_OPENROUTER_NO_TRAINING", "0")
    with auth_app.app_context():
        auth_app.config["OPENROUTER_API_KEY"] = "test-key"
        llm._openrouter("anthropic/claude-haiku-4.5", "hello", "", 256, None, None)
    assert "provider" not in seen["payload"]
