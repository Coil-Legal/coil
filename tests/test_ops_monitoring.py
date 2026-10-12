"""Host operations for C08: the fleet monitor, the restore drill, account state changes and
the per-firm backup status file they rely on.

Every external command these scripts call on the VPS (docker, curl, date, df, mail) is a
stub here, the same way the backup and restore tests stub them, so nothing touches a real
container, network or mailbox. The archives the restore drill restores are real.

Run: .venv/bin/python -m pytest tests/test_ops_monitoring.py -q
"""
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
import tarfile
import time
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "ops"
FIRM = "synthetic.coil.test"


def stub(commands, name, body):
    p = commands / name
    p.write_text("#!" + sys.executable + "\nimport sys, os, pathlib, json\n" + body + "\n")
    p.chmod(0o700)


# ---------------------------------------------------------------------------------------
# monitor.sh
# ---------------------------------------------------------------------------------------
CURL_STUB = r"""
args = sys.argv[1:]
calls = pathlib.Path(os.environ['FIXTURE_CALLS'])
url = args[-1]
if '--data-binary' in args:
    payload = args[args.index('--data-binary') + 1].lstrip('@')
    with calls.open('a') as f:
        f.write('WEBHOOK ' + url + ' ' + pathlib.Path(payload).read_text() + '\n')
    sys.exit(22 if os.environ.get('FIXTURE_WEBHOOK_FAIL') == '1' else 0)
code = os.environ.get('FIXTURE_READY_CODE', '200')
body = json.dumps({'status': 'ready' if code == '200' else 'degraded',
                   'checks': {'database': 'ok', 'jobs.emailin': 'stale' if code != '200' else 'ok'}})
if '-o' in args:
    pathlib.Path(args[args.index('-o') + 1]).write_text(body)
with calls.open('a') as f:
    f.write('CURL ' + url + '\n')
if '-w' in args:
    sys.stdout.write(code)
"""
DOCKER_MONITOR_STUB = r"""
if os.path.basename(os.getcwd()) in os.environ.get('FIXTURE_DOWN', '').split(','):
    sys.exit(0)
print('container-' + os.path.basename(os.getcwd()))
"""
DATE_STUB = r"""
if '+%s' in sys.argv:
    print(os.environ['FIXTURE_NOW'])
else:
    print('2026-10-11 12:00:00')
"""
DF_STUB = r"""
total = 100 * 1024 * 1024        # 100 GB in KB
avail = int(float(os.environ.get('FIXTURE_DISK_FREE_PCT', '50')) * total / 100)
print('Filesystem 1024-blocks Used Available Capacity Mounted on')
print(f'/dev/fake {total} {total - avail} {avail} 50% /')
"""
MAIL_STUB = r"""
with open(os.environ['FIXTURE_CALLS'], 'a') as f:
    f.write('MAIL ' + ' '.join(sys.argv[1:]) + ' ' + sys.stdin.read().replace('\n', ' | ') + '\n')
"""


@pytest.fixture
def fleet(tmp_path):
    now = int(time.time())
    apps, backups = tmp_path / "apps", tmp_path / "backups"
    commands = tmp_path / "commands"
    commands.mkdir()
    for name, body in (("curl", CURL_STUB), ("docker", DOCKER_MONITOR_STUB), ("date", DATE_STUB),
                       ("df", DF_STUB), ("mail", MAIL_STUB)):
        stub(commands, name, body)
    calls = tmp_path / "calls"

    def add_firm(name=FIRM, archive_age_h=2, offsite="ok", status_age_h=2, drill="pass", drill_age_d=3):
        d = apps / name
        (d / "data").mkdir(parents=True)
        (d / "data/practice.db").write_bytes(b"x")
        (d / ".env").write_text(f"SECRET_KEY=abc\nBASE_URL=https://{name}   # public\n")
        b = backups / name
        b.mkdir(parents=True)
        a = b / f"{name}-20261011T022000Z-abc.tar.gz"
        a.write_bytes(b"archive")
        t = now - archive_age_h * 3600
        os.utime(a, (t, t))
        if offsite is not None:
            (b / ".coil-backup-status").write_text(
                f"epoch={now - status_age_h * 3600}\nlocal=ok\noffsite={offsite}\narchive={a.name}\n")
        if drill is not None:
            (b / ".coil-drill-status").write_text(
                f"epoch={now - drill_age_d * 86400}\narchive={a.name}\nresult={drill}\ndetail=checked\n")
        return d

    base_env = dict(os.environ, PATH=str(commands) + ":" + os.environ["PATH"], COIL_APPS_DIR=str(apps),
                    COIL_BACKUP_ROOT=str(backups), COIL_MONITOR_STATE_DIR=str(tmp_path / "state"), COIL_INSTANCE_GLOB="*",
                    COIL_MONITOR_CONFIG=str(tmp_path / "absent.env"), FIXTURE_NOW=str(now),
                    FIXTURE_CALLS=str(calls), COIL_MONITOR_HOST="testhost",
                    COIL_ALERT_WEBHOOK="https://alerts.invalid/hook")
    base_env.pop("COIL_ALERT_EMAIL", None)

    def run(*args, **env):
        e = dict(base_env)
        for k, v in env.items():
            if v is None:
                e.pop(k, None)
            else:
                e[k] = v
        return subprocess.run(["bash", str(OPS / "monitor.sh"), *args], env=e, capture_output=True,
                              text=True, timeout=60)

    def webhook_calls():
        if not calls.exists():
            return []
        return [json.loads(line.split(" ", 2)[2]) for line in calls.read_text().splitlines()
                if line.startswith("WEBHOOK ")]

    return dict(run=run, add_firm=add_firm, calls=calls, webhooks=webhook_calls,
                state=tmp_path / "state/state", tmp=tmp_path)


def test_default_watches_hosted_firms_only(fleet):
    # Stopped lab and recovery copies also hold a practice.db; by default only <slug>.coil.legal
    # instances are watched, so those copies never alert.
    fleet["add_firm"]("firm-a.coil.legal")
    fleet["add_firm"]("coil-phase1-lab", archive_age_h=500, offsite="failed", drill="fail")
    r = fleet["run"](COIL_INSTANCE_GLOB=None)
    assert r.returncode == 0, r.stdout + r.stderr
    state = fleet["state"].read_text()
    assert "firm-a.coil.legal:ready ok" in state
    assert "coil-phase1-lab" not in state + r.stdout + r.stderr


def test_all_ok_first_run_sends_nothing_and_exits_0(fleet):
    fleet["add_firm"]()
    r = fleet["run"]()
    assert r.returncode == 0, r.stdout + r.stderr
    assert fleet["webhooks"]() == []
    state = fleet["state"].read_text()
    for check in ("container", "ready", "backup", "offsite", "drill"):
        assert f"{FIRM}:{check} ok" in state
    assert "host:disk ok" in state
    assert f"CURL https://{FIRM}/health/ready" in fleet["calls"].read_text()


def test_alerts_only_on_change_and_on_recovery(fleet):
    fleet["add_firm"]()
    assert fleet["run"]().returncode == 0
    r = fleet["run"](FIXTURE_READY_CODE="503")
    assert r.returncode == 1
    hooks = fleet["webhooks"]()
    assert len(hooks) == 1
    assert hooks[0]["changes"] == [{"change": "FAIL", "check": f"{FIRM}:ready",
                                    "detail": "/health/ready answered 503 (jobs.emailin stale)"}]
    assert hooks[0]["host"] == "testhost" and "1 new failure" in hooks[0]["text"]
    # Still failing: no second alert.
    assert fleet["run"](FIXTURE_READY_CODE="503").returncode == 1
    assert len(fleet["webhooks"]()) == 1
    # Recovered: one more alert, then quiet again.
    assert fleet["run"]().returncode == 0
    hooks = fleet["webhooks"]()
    assert len(hooks) == 2 and hooks[1]["changes"][0]["change"] == "RECOVERED"
    assert fleet["run"]().returncode == 0
    assert len(fleet["webhooks"]()) == 2


def test_new_failure_on_first_run_alerts(fleet):
    fleet["add_firm"]()
    r = fleet["run"](FIXTURE_DOWN=FIRM)
    assert r.returncode == 1
    changes = fleet["webhooks"]()[0]["changes"]
    assert {"change": "FAIL", "check": f"{FIRM}:container", "detail": "the web container is not running"} in changes


def test_each_backup_check_fails_on_its_own_evidence(fleet):
    fleet["add_firm"]("old.coil.test", archive_age_h=30)
    fleet["add_firm"]("offsite.coil.test", offsite="failed")
    fleet["add_firm"]("stale-status.coil.test", status_age_h=30)
    fleet["add_firm"]("nostatus.coil.test", offsite=None)
    fleet["add_firm"]("drillfail.coil.test", drill="fail")
    fleet["add_firm"]("drillold.coil.test", drill_age_d=40)
    fleet["add_firm"]("nodrill.coil.test", drill=None)
    r = fleet["run"]()
    assert r.returncode == 1
    failed = {c["check"] for c in fleet["webhooks"]()[0]["changes"]}
    assert failed == {"old.coil.test:backup", "offsite.coil.test:offsite", "stale-status.coil.test:offsite",
                      "nostatus.coil.test:offsite", "drillfail.coil.test:drill", "drillold.coil.test:drill",
                      "nodrill.coil.test:drill"}


def test_low_disk_alerts(fleet):
    fleet["add_firm"]()
    r = fleet["run"](FIXTURE_DISK_FREE_PCT="4")
    assert r.returncode == 1
    assert fleet["webhooks"]()[0]["changes"][0]["check"] == "host:disk"


def test_no_alert_channel_says_so_loudly_and_exits_nonzero(fleet):
    fleet["add_firm"]()
    r = fleet["run"](COIL_ALERT_WEBHOOK=None, FIXTURE_READY_CODE="503")
    assert r.returncode == 3
    assert "NO ALERT CHANNEL CONFIGURED" in r.stdout
    assert "NOT sent" in r.stdout
    assert not fleet["state"].exists(), "state must not absorb a change nobody was told about"
    # Even with everything ok, a host with no channel is not a healthy host.
    r = fleet["run"](COIL_ALERT_WEBHOOK=None)
    assert r.returncode == 3 and "NO ALERT CHANNEL CONFIGURED" in r.stdout


def test_failed_delivery_keeps_state_so_the_next_run_retries(fleet):
    fleet["add_firm"]()
    assert fleet["run"]().returncode == 0
    before = fleet["state"].read_text()
    r = fleet["run"](FIXTURE_READY_CODE="503", FIXTURE_WEBHOOK_FAIL="1")
    assert r.returncode == 4
    assert fleet["state"].read_text() == before
    r = fleet["run"](FIXTURE_READY_CODE="503")
    assert r.returncode == 1
    assert fleet["webhooks"]()[-1]["changes"][0]["check"] == f"{FIRM}:ready"


def test_email_channel_uses_mail(fleet):
    fleet["add_firm"]()
    r = fleet["run"](COIL_ALERT_WEBHOOK=None, COIL_ALERT_EMAIL="ops@example.test", FIXTURE_READY_CODE="503")
    assert r.returncode == 1, r.stdout
    mail = [line for line in fleet["calls"].read_text().splitlines() if line.startswith("MAIL ")]
    assert len(mail) == 1 and "ops@example.test" in mail[0] and f"FAIL {FIRM}:ready" in mail[0]


def test_dry_run_sends_and_remembers_nothing(fleet):
    fleet["add_firm"]()
    r = fleet["run"]("--dry-run", FIXTURE_READY_CODE="503")
    assert r.returncode == 1
    assert "would alert" in r.stdout
    assert fleet["webhooks"]() == []
    assert not fleet["state"].exists()


def test_config_file_supplies_the_channel(fleet):
    fleet["add_firm"]()
    conf = fleet["tmp"] / "monitor.env"
    conf.write_text("COIL_ALERT_WEBHOOK=https://alerts.invalid/from-config\n")
    r = fleet["run"](COIL_ALERT_WEBHOOK=None, COIL_MONITOR_CONFIG=str(conf), FIXTURE_READY_CODE="503")
    assert r.returncode == 1
    assert "WEBHOOK https://alerts.invalid/from-config" in fleet["calls"].read_text()


def test_unknown_option_is_refused(fleet):
    assert fleet["run"]("--loop").returncode == 2


# ---------------------------------------------------------------------------------------
# restore-drill.sh
# ---------------------------------------------------------------------------------------
def make_archive(path, tables=None, manifest_extra=None, corrupt=False, manifest_schema=None):
    tables = tables or {"matters": 3, "contacts": 2}
    work = path.parent / ("src-" + path.name)
    work.mkdir(parents=True)
    db = work / "practice.db"
    conn = sqlite3.connect(db)
    for t, n in tables.items():
        conn.execute(f'CREATE TABLE "{t}" (id INTEGER PRIMARY KEY, name TEXT)')
        conn.executemany(f'INSERT INTO "{t}" (name) VALUES (?)', [(f"QA row {i}",) for i in range(n)])
    conn.commit()
    conn.close()
    if corrupt:
        data = bytearray(db.read_bytes())
        data[100:4096] = b"\x00" * (4096 - 100)
        db.write_bytes(bytes(data))
    schema = manifest_schema or {t: ["id", "name"] for t in tables}
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    manifest = {"format": 1, "producer": "nightly", "coil_version": "test", "coil_commit": "abc1234",
                "created_at": "2026-10-11T02:20:00Z", "schema": schema,
                "schema_fingerprint": hashlib.sha256(canonical.encode()).hexdigest()}
    manifest.update(manifest_extra or {})
    (work / "coil-backup.json").write_text(json.dumps(manifest))
    (work / ".env").write_text("SECRET_KEY=synthetic-secret\nBASE_URL=https://synthetic.coil.test\n")
    with tarfile.open(path, "w:gz") as tar:
        for name in ("practice.db", "coil-backup.json", ".env"):
            tar.add(work / name, arcname=name)
    return path


DOCKER_DRILL_STUB = r"""
args = sys.argv[1:]
with open(os.environ['FIXTURE_CALLS'], 'a') as f:
    f.write('docker ' + ' '.join(args) + '\n')
if args[:1] == ['compose'] and 'config' in args:
    print(json.dumps({'name': 'synthetic', 'services': {'web': {'build': {'context': '.'}}}}))
elif args[:2] == ['image', 'inspect']:
    sys.exit(0)
elif args[:1] == ['run']:
    print(json.dumps({'format': 1, 'coil_version': 'test', 'coil_commit': 'abc1234',
                      'schema': json.loads(os.environ['FIXTURE_KNOWN'])}))
"""


@pytest.fixture
def drill(tmp_path):
    apps, backups = tmp_path / "apps", tmp_path / "backups"
    (apps / FIRM).mkdir(parents=True)
    (backups / FIRM).mkdir(parents=True)
    commands = tmp_path / "commands"
    commands.mkdir()
    stub(commands, "docker", DOCKER_DRILL_STUB)
    calls = tmp_path / "calls"
    env = dict(os.environ, PATH=str(commands) + ":" + os.environ["PATH"], COIL_APPS_DIR=str(apps),
               COIL_BACKUP_ROOT=str(backups), COIL_BASE_DOMAIN="coil.test", COIL_INSTANCE_GLOB="*", FIXTURE_CALLS=str(calls),
               COIL_DRILL_TMP=str(tmp_path / "drill-work"),
               FIXTURE_KNOWN=json.dumps({"matters": ["id", "name"], "contacts": ["id", "name"]}))

    def run(*args, **extra):
        return subprocess.run(["bash", str(OPS / "restore-drill.sh"), *args], env=dict(env, **extra),
                              capture_output=True, text=True, timeout=120)

    def status():
        p = backups / FIRM / ".coil-drill-status"
        return dict(line.split("=", 1) for line in p.read_text().splitlines()) if p.exists() else None

    def leftovers():
        root = tmp_path / "drill-work"
        return [str(p) for p in root.rglob("*")] if root.exists() else []

    return dict(run=run, status=status, leftovers=leftovers, apps=apps, archive_dir=backups / FIRM,
                calls=calls)


def test_drill_passes_on_a_good_archive_and_cleans_up(drill):
    old = make_archive(drill["archive_dir"] / f"{FIRM}-20261010T022000Z-a.tar.gz")
    os.utime(old, (time.time() - 86400, time.time() - 86400))
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz")
    r = drill["run"]("synthetic", COIL_DRILL_SCHEMA_CHECK="0")
    assert r.returncode == 0, r.stdout + r.stderr
    s = drill["status"]()
    assert s["result"] == "pass"
    assert s["archive"] == f"{FIRM}-20261011T022000Z-b.tar.gz", "the newest archive is the one drilled"
    assert "2 tables, 5 rows" in s["detail"] and "schema check against the firm's image: skipped" in s["detail"]
    assert int(s["epoch"]) > 0
    assert drill["leftovers"]() == [], "the restored firm data must not outlive the drill"
    assert "synthetic-secret" not in r.stdout + r.stderr


def test_drill_runs_the_schema_check_against_the_firms_image(drill):
    (drill["apps"] / FIRM / "docker-compose.yml").write_text("services:\n  web:\n    build: .\n")
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz")
    r = drill["run"]("synthetic")
    assert r.returncode == 0, r.stdout + r.stderr
    assert drill["status"]()["result"] == "pass"
    assert "schema check against the firm's image: checked" in drill["status"]()["detail"]
    calls = drill["calls"].read_text()
    assert "--network none" in calls and "known_schema" in calls
    assert drill["leftovers"]() == []


def test_drill_fails_when_the_image_is_older_than_the_backup(drill):
    (drill["apps"] / FIRM / "docker-compose.yml").write_text("services:\n  web:\n    build: .\n")
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz")
    r = drill["run"]("synthetic", FIXTURE_KNOWN=json.dumps({"matters": ["id", "name"]}))
    assert r.returncode == 1
    s = drill["status"]()
    assert s["result"] == "fail" and "restore.sh exited" in s["detail"]
    assert drill["leftovers"]() == []


def test_drill_fails_on_a_corrupt_database(drill):
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz", tables={"matters": 400}, corrupt=True)
    r = drill["run"]("synthetic", COIL_DRILL_SCHEMA_CHECK="0")
    assert r.returncode == 1
    assert drill["status"]()["result"] == "fail"
    assert drill["leftovers"]() == []


def test_drill_fails_when_manifest_tables_are_missing_or_counts_differ(drill):
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz",
                 manifest_schema={"matters": ["id", "name"], "contacts": ["id", "name"],
                                  "trust_transactions": ["id"]})
    r = drill["run"]("synthetic", COIL_DRILL_SCHEMA_CHECK="0")
    assert r.returncode == 1
    assert "missing after restore: trust_transactions" in drill["status"]()["detail"]


def test_drill_compares_manifest_row_counts_when_present(drill):
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz",
                 manifest_extra={"row_counts": {"matters": 3, "contacts": 7}})
    r = drill["run"]("synthetic", COIL_DRILL_SCHEMA_CHECK="0")
    assert r.returncode == 1
    assert "row counts differ from manifest in 1 table(s): contacts" in drill["status"]()["detail"]


def test_drill_without_any_archive_records_a_failure(drill):
    r = drill["run"]("synthetic")
    assert r.returncode == 1
    assert drill["status"]()["result"] == "fail"


def test_drill_all_and_dry_run(drill):
    make_archive(drill["archive_dir"] / f"{FIRM}-20261011T022000Z-b.tar.gz")
    r = drill["run"]("--dry-run", "--all")
    assert r.returncode == 0 and "would drill synthetic.coil.test" in r.stdout
    assert drill["status"]() is None
    r = drill["run"]("--all", COIL_DRILL_SCHEMA_CHECK="0")
    assert r.returncode == 0, r.stdout + r.stderr
    assert drill["status"]()["result"] == "pass"


@pytest.mark.parametrize("args", [(), ("../x",), ("Bad",), ("-x",), ("a", "b"), ("--all", "a"), ("--nope",)])
def test_drill_rejects_bad_arguments(drill, args):
    assert drill["run"](*args).returncode == 2


# ---------------------------------------------------------------------------------------
# firm-state.sh
# ---------------------------------------------------------------------------------------
DOCKER_STATE_STUB = r"""
args = sys.argv[1:]
with open(os.environ['FIXTURE_CALLS'], 'a') as f:
    f.write('docker ' + ' '.join(args) + ' in ' + os.getcwd() + '\n')
if 'printenv' in args:
    if os.environ.get('FIXTURE_STALE_ENV') == '1':
        print('active'); sys.exit(0)
    for line in open('.env'):
        if line.startswith('COIL_ACCOUNT_STATE='):
            print(line.split('=', 1)[1].strip())
"""
CURL_STATE_STUB = r"""
with open(os.environ['FIXTURE_CALLS'], 'a') as f:
    f.write('curl ' + sys.argv[-1] + '\n')
sys.stdout.write(os.environ.get('FIXTURE_READY_CODE', '200'))
"""
ENV_TEXT = ("# Synthetic Firm. Provisioned 2026-10-01 by ops/new-firm.sh\n"
            "SECRET_KEY=synthetic-secret-value\n"
            "BASE_URL=https://synthetic.coil.test\n"
            "COIL_HOSTING=hosted       # a trailing comment\n"
            "SMTP_PASS=p@ss=word\n")


@pytest.fixture
def firm_state(tmp_path):
    d = tmp_path / "apps" / FIRM
    d.mkdir(parents=True)
    env_file = d / ".env"
    env_file.write_text(ENV_TEXT)
    env_file.chmod(0o600)
    (d / "docker-compose.yml").write_text("services: {}\n")
    commands = tmp_path / "commands"
    commands.mkdir()
    stub(commands, "docker", DOCKER_STATE_STUB)
    stub(commands, "curl", CURL_STATE_STUB)
    calls = tmp_path / "calls"
    env = dict(os.environ, PATH=str(commands) + ":" + os.environ["PATH"], COIL_APPS_DIR=str(tmp_path / "apps"),
               COIL_BASE_DOMAIN="coil.test", FIXTURE_CALLS=str(calls), COIL_STATE_WAIT_SECONDS="6")

    def run(*args, **extra):
        return subprocess.run(["bash", str(OPS / "firm-state.sh"), *args], env=dict(env, **extra),
                              capture_output=True, text=True, timeout=60)
    return dict(run=run, env_file=env_file, calls=calls)


def _others(text):
    return [l for l in text.splitlines() if not l.startswith("COIL_ACCOUNT_") and "firm-state.sh" not in l and l]


def test_suspend_edits_only_the_state_line_and_recreates(firm_state):
    r = firm_state["run"]("synthetic", "suspended")
    assert r.returncode == 0, r.stdout + r.stderr
    text = firm_state["env_file"].read_text()
    assert "COIL_ACCOUNT_STATE=suspended" in text
    assert "COIL_ACCOUNT_CLOSED_RETAIN_UNTIL" not in text
    assert _others(text) == [l for l in ENV_TEXT.splitlines() if l]
    assert stat.S_IMODE(firm_state["env_file"].stat().st_mode) == 0o600
    calls = firm_state["calls"].read_text()
    assert "docker compose up -d --force-recreate" in calls
    assert "curl https://synthetic.coil.test/health/ready" in calls
    assert "account state in the running container: suspended" in r.stdout
    assert "synthetic-secret-value" not in r.stdout + r.stderr
    assert not [p for p in firm_state["env_file"].parent.iterdir() if p.name.startswith(".env.")]


def test_close_defaults_to_ninety_days_then_reactivate_removes_it(firm_state):
    r = firm_state["run"]("synthetic", "closed")
    assert r.returncode == 0, r.stdout + r.stderr
    expected = (date.today() + timedelta(days=90)).isoformat()
    text = firm_state["env_file"].read_text()
    assert f"COIL_ACCOUNT_CLOSED_RETAIN_UNTIL={expected}" in text
    assert text.count("COIL_ACCOUNT_STATE=") == 1
    r = firm_state["run"]("synthetic", "closed", "--retain-until", "2027-03-01")
    assert r.returncode == 0
    text = firm_state["env_file"].read_text()
    assert "COIL_ACCOUNT_CLOSED_RETAIN_UNTIL=2027-03-01" in text and text.count("RETAIN_UNTIL") == 1
    r = firm_state["run"]("synthetic", "active")
    assert r.returncode == 0
    text = firm_state["env_file"].read_text()
    assert "COIL_ACCOUNT_STATE=active" in text and "RETAIN_UNTIL" not in text
    assert _others(text) == [l for l in ENV_TEXT.splitlines() if l]
    assert text.count("firm-state.sh") == 1, "the explanatory comment is added once, not per change"


def test_dry_run_changes_nothing(firm_state):
    r = firm_state["run"]("--dry-run", "synthetic", "suspended")
    assert r.returncode == 0
    assert "would: set COIL_ACCOUNT_STATE=suspended" in r.stdout
    assert firm_state["env_file"].read_text() == ENV_TEXT
    assert not firm_state["calls"].exists()


def test_reports_failure_when_container_does_not_see_the_state(firm_state):
    r = firm_state["run"]("synthetic", "suspended", FIXTURE_STALE_ENV="1")
    assert r.returncode == 1
    assert "does not see COIL_ACCOUNT_STATE=suspended" in r.stderr


def test_reports_failure_when_not_ready(firm_state):
    r = firm_state["run"]("synthetic", "suspended", FIXTURE_READY_CODE="503")
    assert r.returncode == 1
    assert "/health/ready did not answer 200" in r.stderr


@pytest.mark.parametrize("args", [
    ("synthetic",), ("synthetic", "paused"), ("../etc", "active"), ("Synthetic", "active"),
    ("synthetic", "active", "--retain-until", "2027-01-01"), ("synthetic", "closed", "--retain-until", "2027-02-30"),
    ("synthetic", "closed", "--retain-until", "next week"), ("synthetic", "active", "extra"), ("synthetic", "active", "--force"),
])
def test_bad_arguments_change_nothing(firm_state, args):
    r = firm_state["run"](*args)
    assert r.returncode == 2, (args, r.stdout, r.stderr)
    assert firm_state["env_file"].read_text() == ENV_TEXT
    assert not firm_state["calls"].exists()


def test_missing_firm_is_refused(firm_state):
    assert firm_state["run"]("nosuchfirm", "suspended").returncode == 1


# ---------------------------------------------------------------------------------------
# backup.sh writes the per-firm status file monitor.sh reads
# ---------------------------------------------------------------------------------------
def run_backup(tmp_path, rclone_fail="0", archive_fail="0"):
    firm = tmp_path / "apps" / FIRM
    (firm / "data").mkdir(parents=True, exist_ok=True)
    (firm / "data/practice.db").write_bytes(b"synthetic source")
    commands = tmp_path / "commands"
    commands.mkdir(exist_ok=True)
    stubs = {
        "date": "print('20260926T200000Z' if '+%Y%m%dT%H%M%SZ' in sys.argv else ('1790000000' if '+%s' in sys.argv else '6'))",
        "docker": """
if sys.argv[1] == 'compose': print('synthetic-container')
else:
    import hashlib
    snap = pathlib.Path(sys.argv[-1].replace('/app/data', os.environ['FIXTURE_FIRM'] + '/data'))
    snap.write_bytes(b'snapshot')
    schema = {'fixture': ['cents']}
    canonical = json.dumps(schema, sort_keys=True, separators=(',', ':'))
    (snap.parent / 'coil-backup.json').write_text(json.dumps({
        'format': 1, 'producer': 'nightly', 'coil_version': 'dev', 'coil_commit': 'unknown',
        'created_at': '2026-09-26T20:00:00Z', 'schema': schema,
        'schema_fingerprint': hashlib.sha256(canonical.encode()).hexdigest()}))""",
        "tar": "\np=pathlib.Path(sys.argv[sys.argv.index('-czf')+1]); p.write_bytes(b'archive'); sys.exit(int(os.environ['FAIL_ARCHIVE']))",
        "rclone": "\nsys.exit(int(os.environ['FAIL_RCLONE']) if sys.argv[1] == 'copy' else 0)",
    }
    for name, body in stubs.items():
        stub(commands, name, body)
    env = dict(os.environ, PATH=str(commands) + ":" + os.environ["PATH"], COIL_APPS_DIR=str(tmp_path / "apps"),
               COIL_BACKUP_ROOT=str(tmp_path / "backups"), COIL_BACKUP_REMOTE="synthetic:no-network",
               FIXTURE_FIRM=str(firm), FAIL_ARCHIVE=archive_fail, FAIL_RCLONE=rclone_fail)
    r = subprocess.run(["bash", str(OPS / "backup.sh")], env=env, text=True, capture_output=True)
    p = tmp_path / "backups" / FIRM / ".coil-backup-status"
    return r, (dict(line.split("=", 1) for line in p.read_text().splitlines()) if p.exists() else None)


def test_backup_records_a_successful_offsite_copy(tmp_path):
    r, status = run_backup(tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert status["local"] == "ok" and status["offsite"] == "ok"
    assert status["epoch"] == "1790000000"
    assert status["archive"].startswith(f"{FIRM}-20260926T200000Z-") and status["archive"].endswith(".tar.gz")


def test_backup_records_a_failed_offsite_copy(tmp_path):
    r, status = run_backup(tmp_path, rclone_fail="1")
    assert r.returncode == 1
    assert status["local"] == "ok" and status["offsite"] == "failed"


def test_backup_records_a_failed_archive(tmp_path):
    r, status = run_backup(tmp_path, archive_fail="1")
    assert r.returncode == 1
    assert status["local"] == "failed" and status["offsite"] == "skipped"
    assert status["archive"] == ""


def test_status_file_is_not_mistaken_for_an_archive(tmp_path):
    run_backup(tmp_path)
    archives = list((tmp_path / "backups").glob("*/*.tar.gz"))
    assert len(archives) == 1
