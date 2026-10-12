"""When each cron job last finished, so /health/ready can tell a stopped job from a quiet one.

Every `python -m app.cli <command>` run records its outcome here (see app/cli.py main). The
store is one small JSON file in the data directory, replaced atomically, rather than a
database table, for three reasons:

* A job that fails because the database is unreachable or locked must still be able to
  record that failure. A table would lose exactly the failures that matter most.
* A new table becomes part of the backup manifest's schema, and ops/restore.sh refuses to
  restore a backup holding a table the target code does not know (#115). A heartbeat
  table would make every backup taken after this change unrestorable under the previous
  release, which is the rollback path.
* The readiness check reads it on every poll. A file read is cheaper than a query and does
  not compete with the app for the SQLite write lock.

Nothing in the file is firm data: command names, UTC timestamps, and on failure the
exception class name only (an exception message can quote a client name or an address).
The file is not in backups on purpose. A restored firm starts with every job "unknown",
which is the truth until its cron runs again.
"""
import fcntl
import json
import logging
import os
import tempfile
from datetime import datetime, timedelta, timezone

from .config import DATA_DIR

log = logging.getLogger("heartbeat")

FILE_NAME = "job-heartbeats.json"
FORMAT = 1

DAY = 26 * 60            # a daily job may drift a little, so a day plus two hours
MONTH = 32 * 24 * 60     # monthly jobs, a month plus a day

# Minutes after its last success that a job counts as stale. Matches the cron lines that
# ops/new-firm.sh installs: emailin every 10 minutes and webhooks every 15, so 45 minutes
# is three missed runs; the daily jobs once a day; interest on the 1st of each month.
# monthly_invoicing runs daily but only bills on the firm's billing day, so a month is
# the real limit. backup runs from the self-updater on self-hosted installs (hosted
# firms are backed up from the host by ops/backup.sh and never call it, so it stays
# "unknown" there, which does not fail readiness).
DEFAULT_STALE_MINUTES = {
    "emailin": 45,
    "webhooks": 45,
    "agenda": DAY,
    "reminders": DAY,
    "sequences": DAY,
    "case_audit": DAY,
    "payment_plans": DAY,
    "voice_reminders": DAY,
    "backup": DAY,
    "interest": MONTH,
    "monthly_invoicing": MONTH,
}


def _utcnow():
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def heartbeat_path(config=None):
    """Where the store lives: COIL_HEARTBEAT_FILE (config, then environment), else data/."""
    explicit = (config or {}).get("COIL_HEARTBEAT_FILE") or os.environ.get("COIL_HEARTBEAT_FILE")
    return explicit or os.path.join(DATA_DIR, FILE_NAME)


def stale_thresholds(config=None):
    """{command: minutes}. Override with COIL_JOB_STALE_MINUTES="emailin=60,voice_reminders=0".

    The config key of the same name may be a dict or the same string. 0 (or "off") drops a
    job from readiness altogether, for a firm that does not schedule it.
    """
    out = dict(DEFAULT_STALE_MINUTES)
    raw = (config or {}).get("COIL_JOB_STALE_MINUTES")
    if raw is None:
        raw = os.environ.get("COIL_JOB_STALE_MINUTES", "")
    items = raw.items() if isinstance(raw, dict) else (
        part.split("=", 1) for part in str(raw).split(",") if "=" in part)
    for name, minutes in items:
        name = str(name).strip()
        if not name:
            continue
        value = str(minutes).strip().lower()
        if value in ("0", "off", "none", ""):
            out.pop(name, None)
            continue
        try:
            out[name] = max(1, int(float(value)))
        except ValueError:
            log.warning("COIL_JOB_STALE_MINUTES: ignoring %s=%s, not a number of minutes", name, minutes)
    return out


def load(path):
    """The stored jobs as {command: {...}}. Missing file means {}; a damaged file raises ValueError."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"heartbeat file unreadable: {type(exc).__name__}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("jobs"), dict):
        raise ValueError("heartbeat file is not in the expected format")
    return data["jobs"]


def record(command, ok, note="", error="", path=None, when=None):
    """Record one finished run. Locked and atomically replaced, so two overlapping cron jobs
    never lose each other's entry and a reader never sees half a file."""
    path = path or heartbeat_path()
    when = when or _utcnow()
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    lock_path = os.path.join(directory, "." + os.path.basename(path) + ".lock")
    with open(lock_path, "a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            try:
                jobs = load(path)
            except ValueError:
                log.warning("heartbeat: %s was unreadable, starting it again", path)
                jobs = {}
            entry = dict(jobs.get(command) or {})
            if ok:
                entry["last_success"] = _iso(when)
                entry["last_note"] = (note or "")[:200]
            else:
                entry["last_failure"] = _iso(when)
                entry["last_error"] = (error or "failed")[:100]
            jobs[command] = entry
            fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", dir=directory)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as out:
                    json.dump({"format": FORMAT, "jobs": jobs}, out, indent=1, sort_keys=True)
                    out.flush()
                    os.fsync(out.fileno())
                os.chmod(tmp, 0o644)
                os.replace(tmp, path)
            except BaseException:
                try:
                    os.unlink(tmp)
                except FileNotFoundError:
                    pass
                raise
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def safe_record(command, ok, **kw):
    """record(), but a heartbeat problem is logged and never fails the job itself."""
    try:
        record(command, ok, **kw)
    except Exception as exc:  # noqa: BLE001
        log.warning("heartbeat: could not record %s (%s)", command, type(exc).__name__)


def run_recorded(command, fn, beat=None):
    """Run fn() and record how it ended. A return of 0 or None is success; any other
    return, or any exception (re-raised), is a failure. `beat` is a dict fn may fill with
    a "note" (for example why it skipped)."""
    beat = beat if beat is not None else {}
    try:
        rc = fn()
    except SystemExit as exc:
        code = exc.code
        if code in (0, None):
            safe_record(command, True, note=beat.get("note", ""))
        else:
            safe_record(command, False, error=f"exit {code}")
        raise
    except BaseException as exc:
        safe_record(command, False, error=type(exc).__name__)
        raise
    if rc in (0, None):
        safe_record(command, True, note=beat.get("note", ""))
    else:
        safe_record(command, False, error=f"exit {rc}")
    return rc


def job_states(path, thresholds, now=None):
    """{command: "ok" | "stale" | "fail" | "unknown"} for every command in thresholds.

    unknown: never recorded (a fresh install, or the job is not scheduled here).
    fail:    the last failure is more recent than the last success.
    stale:   the last success is older than the command's threshold.
    Raises ValueError when the file exists but cannot be read.
    """
    now = now or _utcnow()
    jobs = load(path)
    out = {}
    for command, minutes in thresholds.items():
        entry = jobs.get(command) if isinstance(jobs.get(command), dict) else {}
        success = _parse(entry.get("last_success"))
        failure = _parse(entry.get("last_failure"))
        if success is None and failure is None:
            out[command] = "unknown"
        elif failure is not None and (success is None or failure > success):
            out[command] = "fail"
        elif now - success > timedelta(minutes=minutes):
            out[command] = "stale"
        else:
            out[command] = "ok"
    return out
