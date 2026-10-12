"""/health/ready and the cron job heartbeats behind it (C08 monitoring).

/health deliberately proves nothing beyond "a worker is up", because the updater polls it
right after a restart. /health/ready is the one that has to fail when the database, the
data directory, the disk or a cron job is in trouble, and it must do that without leaking
anything to the stranger who can call it, and without ever raising.

Run: .venv/bin/python -m pytest tests/test_readiness.py -q
"""
import json
import os
import shutil
import subprocess
import sys
import time
from collections import namedtuple
from datetime import datetime, timedelta, timezone

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_readiness.db")
DB_URI = f"sqlite:///{DB_PATH}"

from tests.helpers import login  # noqa: E402

Usage = namedtuple("Usage", "total used free")
GB = 1024 ** 3


@pytest.fixture(scope="module")
def app(tmp_path_factory):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = dict(os.environ, DATABASE_URL=DB_URI, SMTP_HOST="")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    data = tmp_path_factory.mktemp("ready-data")
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True, "SMTP_HOST": "",
                       "COIL_READY_CACHE_SECONDS": 0, "COIL_DATA_DIR": str(data),
                       "COIL_HEARTBEAT_FILE": str(data / "job-heartbeats.json"),
                       "COIL_VERSION": "test-1", "COIL_COMMIT": "abc1234"})


@pytest.fixture(autouse=True)
def clean(app):
    beats = app.config["COIL_HEARTBEAT_FILE"]
    if os.path.exists(beats):
        os.remove(beats)
    saved = dict(app.config)
    yield
    app.config.clear()
    app.config.update(saved)


def _get(app):
    r = app.test_client().get("/health/ready")
    return r.status_code, r.get_json(), r


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_beats(app, jobs):
    with open(app.config["COIL_HEARTBEAT_FILE"], "w") as f:
        json.dump({"format": 1, "jobs": jobs}, f)


# --- the healthy case -----------------------------------------------------------------
def test_fresh_install_is_ready_with_jobs_unknown(app):
    code, body, r = _get(app)
    assert code == 200, body
    assert body["status"] == "ready"
    assert body["version"] == "test-1" and body["commit"] == "abc1234"
    for name in ("database", "data_dir", "disk"):
        assert body["checks"][name] == "ok"
    assert body["checks"]["jobs.emailin"] == "unknown"
    assert body["checks"]["jobs.monthly_invoicing"] == "unknown"
    assert r.headers["Cache-Control"] == "no-store"


def test_response_reveals_no_paths_secrets_or_firm_data(app):
    _, body, r = _get(app)
    text = r.get_data(as_text=True)
    assert app.config["COIL_DATA_DIR"] not in text
    assert "practice.db" not in text and "test_readiness" not in text
    from app.models import Firm
    with app.app_context():
        name = Firm.get().name
    assert name and name not in text
    assert set(body) == {"status", "checks", "version", "commit"}
    assert set(body["checks"].values()) <= {"ok", "stale", "fail", "unknown"}


def test_health_itself_is_unchanged(app):
    r = app.test_client().get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"
    assert set(r.get_json()) == {"status", "version", "commit", "channel"}


def test_ready_works_logged_out_and_with_every_tool_switched_off(app):
    from app.extensions import db
    from app.models import Firm
    from app.tools import TOOLS
    with app.app_context():
        Firm.get().tool_overrides = json.dumps({k: False for k in TOOLS})
        db.session.commit()
    try:
        assert app.test_client().get("/health/ready").status_code == 200
        c = app.test_client()
        login(c)
        assert c.get("/health/ready").status_code == 200
    finally:
        with app.app_context():
            Firm.get().tool_overrides = "{}"
            db.session.commit()


# --- each check failing ---------------------------------------------------------------
def test_database_unreachable_fails(app, monkeypatch):
    import app.readiness as readiness

    def broken(engine):
        raise RuntimeError("database is locked")
    monkeypatch.setattr(readiness, "check_database", broken)
    code, body, r = _get(app)
    assert code == 503
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "fail"
    assert "locked" not in r.get_data(as_text=True)


def test_database_check_reads_the_real_file(app, tmp_path):
    """A query that never touches the file (SELECT 1) passes on a missing database."""
    from sqlalchemy import create_engine
    from app.readiness import check_database
    bad = tmp_path / "not-a-db"
    bad.write_bytes(b"this is not sqlite" * 100)
    with pytest.raises(Exception):
        check_database(create_engine(f"sqlite:///{bad}"))


def test_data_dir_not_writable_fails(app, tmp_path):
    gone = tmp_path / "missing" / "data"
    app.config["COIL_DATA_DIR"] = str(gone)
    code, body, _ = _get(app)
    assert code == 503
    assert body["checks"]["data_dir"] == "fail"


def test_data_dir_check_leaves_nothing_behind(app):
    before = set(os.listdir(app.config["COIL_DATA_DIR"]))
    _get(app)
    assert set(os.listdir(app.config["COIL_DATA_DIR"])) == before


def test_low_disk_fails_on_percent(app, monkeypatch):
    import app.readiness as readiness
    # 1 TB disk, 30 GB free: above 1 GB but below 5%.
    monkeypatch.setattr(readiness.shutil, "disk_usage", lambda p: Usage(1000 * GB, 970 * GB, 30 * GB))
    code, body, _ = _get(app)
    assert code == 503 and body["checks"]["disk"] == "fail"


def test_low_disk_fails_on_absolute_floor(app, monkeypatch):
    import app.readiness as readiness
    # 10 GB disk, 0.9 GB free: 9% is above 5% but under the 1 GB floor.
    monkeypatch.setattr(readiness.shutil, "disk_usage", lambda p: Usage(10 * GB, 9.1 * GB, 0.9 * GB))
    code, body, _ = _get(app)
    assert code == 503 and body["checks"]["disk"] == "fail"


def test_disk_threshold_is_configurable(app, monkeypatch):
    import app.readiness as readiness
    monkeypatch.setattr(readiness.shutil, "disk_usage", lambda p: Usage(10 * GB, 9.1 * GB, 0.9 * GB))
    app.config["COIL_READY_DISK_MIN_MB"] = 500
    code, body, _ = _get(app)
    assert code == 200 and body["checks"]["disk"] == "ok"


def test_a_hung_check_times_out_instead_of_hanging(app, monkeypatch):
    import app.readiness as readiness

    def slow(path, config):
        time.sleep(3)
        return "ok"
    monkeypatch.setattr(readiness, "check_disk", slow)
    app.config["COIL_READY_TIMEOUT"] = 0.3
    started = time.monotonic()
    code, body, _ = _get(app)
    assert time.monotonic() - started < 2
    assert code == 503 and body["checks"]["disk"] == "fail"


def test_endpoint_never_raises(app, monkeypatch):
    import app.readiness as readiness

    def explode(app):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(readiness, "run_checks", explode)
    code, body, _ = _get(app)
    assert code == 503
    assert body == {"status": "degraded", "checks": {"readiness": "fail"}, "version": "unknown", "commit": "unknown"}


# --- job heartbeats -------------------------------------------------------------------
def test_recent_success_is_ok_and_old_success_is_stale(app):
    now = datetime.now(timezone.utc)
    _write_beats(app, {
        "emailin": {"last_success": _iso(now - timedelta(minutes=10))},
        "webhooks": {"last_success": _iso(now - timedelta(minutes=50))},
        "agenda": {"last_success": _iso(now - timedelta(hours=25))},
        "reminders": {"last_success": _iso(now - timedelta(hours=27))},
        "interest": {"last_success": _iso(now - timedelta(days=31))},
        "monthly_invoicing": {"last_success": _iso(now - timedelta(days=33))},
    })
    code, body, _ = _get(app)
    checks = body["checks"]
    assert checks["jobs.emailin"] == "ok"
    assert checks["jobs.webhooks"] == "stale"
    assert checks["jobs.agenda"] == "ok"
    assert checks["jobs.reminders"] == "stale"
    assert checks["jobs.interest"] == "ok"
    assert checks["jobs.monthly_invoicing"] == "stale"
    assert checks["jobs.sequences"] == "unknown"
    assert code == 503 and body["status"] == "degraded"


def test_failure_after_success_is_fail_and_recovery_clears_it(app):
    now = datetime.now(timezone.utc)
    _write_beats(app, {"emailin": {"last_success": _iso(now - timedelta(minutes=20)),
                                   "last_failure": _iso(now - timedelta(minutes=5))}})
    code, body, _ = _get(app)
    assert code == 503 and body["checks"]["jobs.emailin"] == "fail"
    _write_beats(app, {"emailin": {"last_success": _iso(now - timedelta(minutes=1)),
                                   "last_failure": _iso(now - timedelta(minutes=5))}})
    code, body, _ = _get(app)
    assert code == 200 and body["checks"]["jobs.emailin"] == "ok"


def test_only_ever_failed_is_fail(app):
    _write_beats(app, {"agenda": {"last_failure": _iso(datetime.now(timezone.utc))}})
    code, body, _ = _get(app)
    assert code == 503 and body["checks"]["jobs.agenda"] == "fail"


def test_thresholds_configurable_and_zero_drops_a_job(app):
    now = datetime.now(timezone.utc)
    _write_beats(app, {"webhooks": {"last_success": _iso(now - timedelta(minutes=50))},
                       "voice_reminders": {"last_failure": _iso(now)}})
    app.config["COIL_JOB_STALE_MINUTES"] = "webhooks=60,voice_reminders=0"
    code, body, _ = _get(app)
    assert body["checks"]["jobs.webhooks"] == "ok"
    assert "jobs.voice_reminders" not in body["checks"]
    assert code == 200
    app.config["COIL_JOB_STALE_MINUTES"] = {"webhooks": 30}
    assert _get(app)[1]["checks"]["jobs.webhooks"] == "stale"


def test_damaged_heartbeat_file_fails_readiness(app):
    with open(app.config["COIL_HEARTBEAT_FILE"], "w") as f:
        f.write("{not json")
    code, body, _ = _get(app)
    assert code == 503 and body["checks"]["heartbeats"] == "fail"


def test_record_keeps_other_jobs_and_never_stores_messages(tmp_path):
    from app import heartbeat
    path = str(tmp_path / "beats.json")
    heartbeat.record("agenda", True, path=path)
    heartbeat.record("emailin", False, error="ValueError", path=path)
    heartbeat.record("agenda", False, error="OperationalError", path=path)
    jobs = heartbeat.load(path)
    assert set(jobs) == {"agenda", "emailin"}
    assert jobs["agenda"]["last_success"] and jobs["agenda"]["last_error"] == "OperationalError"
    assert [p.name for p in tmp_path.iterdir() if not p.name.startswith(".")] == ["beats.json"]


def test_run_recorded_marks_exceptions_and_exit_codes(tmp_path):
    from app import heartbeat
    path = str(tmp_path / "beats.json")
    os.environ["COIL_HEARTBEAT_FILE"] = path
    try:
        assert heartbeat.run_recorded("agenda", lambda: 0) == 0
        with pytest.raises(RuntimeError):
            heartbeat.run_recorded("reminders", lambda: (_ for _ in ()).throw(RuntimeError("Jane Client")))
        assert heartbeat.run_recorded("webhooks", lambda: 3) == 3
    finally:
        del os.environ["COIL_HEARTBEAT_FILE"]
    jobs = heartbeat.load(path)
    assert "last_success" in jobs["agenda"]
    assert jobs["reminders"]["last_error"] == "RuntimeError"
    assert "Jane" not in open(path).read()
    assert jobs["webhooks"]["last_error"] == "exit 3"
    states = heartbeat.job_states(path, heartbeat.stale_thresholds({}))
    assert states["agenda"] == "ok" and states["reminders"] == "fail" and states["webhooks"] == "fail"


def test_heartbeat_write_failure_never_fails_the_job(tmp_path):
    from app import heartbeat
    blocker = tmp_path / "file"
    blocker.write_text("x")
    os.environ["COIL_HEARTBEAT_FILE"] = str(blocker / "beats.json")   # parent is a file
    try:
        assert heartbeat.run_recorded("agenda", lambda: 0) == 0
    finally:
        del os.environ["COIL_HEARTBEAT_FILE"]


def test_cli_main_records_every_command(tmp_path):
    """Through the real `python -m app.cli` entry, so the cron path is what is tested."""
    db = tmp_path / "practice.db"
    beats = tmp_path / "beats.json"
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", COIL_HEARTBEAT_FILE=str(beats), SMTP_HOST="",
               IMAP_HOST="")
    subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], check=True, cwd=ROOT, env=env,
                   capture_output=True)
    for cmd in ("emailin", "interest"):
        r = subprocess.run([sys.executable, "-m", "app.cli", cmd], cwd=ROOT, env=env, capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
    jobs = json.loads(beats.read_text())["jobs"]
    assert "last_success" in jobs["emailin"] and "last_success" in jobs["interest"]
    # known_schema must not build the app or write anything.
    r = subprocess.run([sys.executable, "-m", "app.cli", "known_schema"], cwd=ROOT, env=env, capture_output=True)
    assert r.returncode == 0
    assert "known_schema" not in json.loads(beats.read_text())["jobs"]


def test_cli_records_a_failure_to_start(tmp_path):
    beats = tmp_path / "beats.json"
    unreadable = tmp_path / "db-is-a-directory"
    unreadable.mkdir()
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{unreadable}", COIL_HEARTBEAT_FILE=str(beats))
    r = subprocess.run([sys.executable, "-m", "app.cli", "agenda"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode != 0
    entry = json.loads(beats.read_text())["jobs"]["agenda"]
    assert entry["last_failure"] and "last_success" not in entry
