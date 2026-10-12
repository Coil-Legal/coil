"""GET /health/ready: can this instance actually do its work right now?

/health stays exactly as it is. The self-updater polls it right after a restart, so it
must answer without the database. That also means a 200 from /health proves only that a
worker is up. This endpoint answers the rest, for the fleet monitor (ops/monitor.sh) and
for ops/firm-state.sh and ops/new-firm.sh after they recreate a container:

  database    a trivial read of the real database file
  data_dir    the data directory takes a write (a temp file created and deleted)
  disk        free space on the data directory's filesystem is above the floor
              (COIL_READY_DISK_MIN_PERCENT, default 5, or COIL_READY_DISK_MIN_MB,
              default 1024, whichever is larger)
  jobs.<cmd>  each cron job's last run, from app/heartbeat.py

It is public and unauthenticated, so it says nothing a stranger should learn: check names
and one-word states, plus the version and commit that /health already shows. No paths, no
timestamps, no error text, no firm data. Each check runs with a short timeout
(COIL_READY_TIMEOUT seconds, default 2) on a small bounded thread pool, and the endpoint
never raises: anything unexpected becomes a "fail" state and a 503.

200 {"status": "ready", ...} when no check is "fail" or "stale". "unknown" never fails it,
so a fresh install whose cron jobs have not run yet is ready. Otherwise 503 "degraded".
"""
import logging
import os
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, current_app, jsonify

from . import heartbeat
from .config import DATA_DIR

log = logging.getLogger("readiness")

bp = Blueprint("readiness", __name__)

_pool = None
_pool_pid = None
_pool_lock = threading.Lock()
_cache = {"at": 0.0, "body": None, "code": 0}


def _executor():
    """One small pool per process. Created lazily so a gunicorn fork never inherits a pool
    whose threads did not survive the fork. Bounded: a hung disk ties up four threads, not
    one per poll."""
    global _pool, _pool_pid
    with _pool_lock:
        if _pool is None or _pool_pid != os.getpid():
            _pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="coil-ready")
            _pool_pid = os.getpid()
        return _pool


def data_dir(config):
    return config.get("COIL_DATA_DIR") or DATA_DIR


def check_database(engine):
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            # Reads the schema page, so this touches the real file, unlike SELECT 1.
            conn.exec_driver_sql("SELECT count(*) FROM sqlite_master").scalar()
        else:
            conn.exec_driver_sql("SELECT 1").scalar()
    return "ok"


def check_data_dir(path):
    fd, tmp = tempfile.mkstemp(prefix=".coil-ready-", dir=path)
    try:
        os.write(fd, b"ok")
    finally:
        os.close(fd)
        os.unlink(tmp)
    return "ok"


def disk_floor_bytes(total, config):
    pct = float(config.get("COIL_READY_DISK_MIN_PERCENT") or os.environ.get("COIL_READY_DISK_MIN_PERCENT") or 5)
    mb = float(config.get("COIL_READY_DISK_MIN_MB") or os.environ.get("COIL_READY_DISK_MIN_MB") or 1024)
    return max(total * pct / 100.0, mb * 1024 * 1024)


def check_disk(path, config):
    usage = shutil.disk_usage(path)
    return "ok" if usage.free >= disk_floor_bytes(usage.total, config) else "fail"


def run_checks(app):
    """{check name: state}. Never raises."""
    config = app.config
    timeout = float(config.get("COIL_READY_TIMEOUT") or os.environ.get("COIL_READY_TIMEOUT") or 2)
    path = data_dir(config)
    checks = {}
    try:
        from .extensions import db
        engine = db.engine
    except Exception:  # noqa: BLE001
        engine = None
    jobs_path = heartbeat.heartbeat_path(config)
    thresholds = heartbeat.stale_thresholds(config)
    tasks = {
        "database": (check_database, engine) if engine is not None else None,
        "data_dir": (check_data_dir, path),
        "disk": (check_disk, path, config),
        "jobs": (heartbeat.job_states, jobs_path, thresholds),
    }
    pool = _executor()
    futures = {}
    for name, task in tasks.items():
        if task is None:
            checks[name] = "fail"
            continue
        try:
            futures[name] = pool.submit(*task)
        except Exception:  # noqa: BLE001
            checks[name] = "fail"
    deadline = time.monotonic() + timeout
    for name, future in futures.items():
        try:
            result = future.result(timeout=max(0.01, deadline - time.monotonic()))
        except Exception as exc:  # noqa: BLE001  (includes the timeout)
            log.warning("readiness: %s check failed (%s)", name, type(exc).__name__)
            if name == "jobs":
                checks["heartbeats"] = "fail"
            else:
                checks[name] = "fail"
            continue
        if name == "jobs":
            for command, state in result.items():
                checks[f"jobs.{command}"] = state
        else:
            checks[name] = result if result in ("ok", "fail", "stale", "unknown") else "fail"
    return checks


@bp.route("/health/ready")
def ready():
    app = current_app._get_current_object()
    try:
        ttl = float(app.config.get("COIL_READY_CACHE_SECONDS", 5) or 0)
        now = time.monotonic()
        if ttl > 0 and _cache["body"] is not None and now - _cache["at"] < ttl:
            body, code = _cache["body"], _cache["code"]
        else:
            checks = run_checks(app)
            degraded = any(state in ("fail", "stale") for state in checks.values())
            body = {
                "status": "degraded" if degraded else "ready",
                "checks": checks,
                "version": app.config.get("COIL_VERSION", "unknown"),
                "commit": app.config.get("COIL_COMMIT", "unknown"),
            }
            code = 503 if degraded else 200
            if ttl > 0:
                _cache.update(at=now, body=body, code=code)
    except Exception as exc:  # noqa: BLE001
        log.warning("readiness: endpoint error (%s)", type(exc).__name__)
        body, code = {"status": "degraded", "checks": {"readiness": "fail"},
                      "version": "unknown", "commit": "unknown"}, 503
    response = jsonify(body)
    response.headers["Cache-Control"] = "no-store"
    return response, code
