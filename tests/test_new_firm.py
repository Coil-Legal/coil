"""ops/new-firm.sh provisioning (C08): release pin, owner setup, backup enrollment, isolation.

The image used to be built from copied source with no commit or version, so /health on a
new firm said "unknown" and nobody could tell which release it ran. Now the build carries
explicit --build-arg COIL_COMMIT and COIL_VERSION from the source checkout, a dirty
source is refused, and after start the script proves the pin, readiness, owner setup,
backup enrollment and isolation from every other instance, then prints a report.

docker, curl, crontab, chown, getent and openssl are stubs. git and rsync are real, on a
throwaway source checkout.

Run: .venv/bin/python -m pytest tests/test_new_firm.py -q
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/new-firm.sh"
DOMAIN = "rehearsal.coil.test"

DOCKER = r"""
args = sys.argv[1:]
cwd = pathlib.Path(os.getcwd())
state = pathlib.Path(os.environ['FIXTURE_STATE'])
with open(state / 'docker.log', 'a') as f:
    f.write(' '.join(args) + ' in ' + str(cwd) + '\n')
if args[:2] == ['compose', 'build']:
    built = {a.split('=', 1)[0]: a.split('=', 1)[1] for a in args if '=' in a}
    (state / 'built.json').write_text(json.dumps(built))
elif args[:2] == ['compose', 'up']:
    (cwd / 'data').mkdir(exist_ok=True)
    (cwd / 'data' / 'practice.db').write_bytes(b'fresh')
elif args[:2] == ['compose', 'ps']:
    print('cid-' + cwd.name)
elif args[:1] == ['inspect']:
    fmt = args[args.index('-f') + 1]
    name = args[-1].removeprefix('cid-')
    if 'compose.project' in fmt:
        print(name.replace('.', ''))
    else:
        print(os.environ.get('FIXTURE_MOUNT') or os.path.realpath(os.path.join(os.environ['COIL_APPS_DIR'], name, 'data')))
elif args[:1] == ['ps']:
    print(os.path.join(os.environ['COIL_APPS_DIR'], 'rehearsal.coil.test'))
    if os.environ.get('FIXTURE_EXTRA_WD'):
        print(os.environ['FIXTURE_EXTRA_WD'])
"""
CURL = r"""
args = sys.argv[1:]
url = [a for a in args if a.startswith('https://')][-1]
state = pathlib.Path(os.environ['FIXTURE_STATE'])
with open(state / 'curl.log', 'a') as f:
    f.write(' '.join(args) + '\n')
if url.endswith('/login'):
    sys.stdout.write('302')
elif url.endswith('/health'):
    built = json.loads((state / 'built.json').read_text())
    commit = os.environ.get('FIXTURE_HEALTH_COMMIT') or built.get('COIL_COMMIT', 'unknown')
    print(json.dumps({'status': 'healthy', 'commit': commit, 'version': built.get('COIL_VERSION')}))
elif url.endswith('/health/ready'):
    sys.stdout.write(os.environ.get('FIXTURE_READY', '200'))
elif url.endswith('/setup'):
    sys.stdout.write('200')
else:
    sys.stdout.write('000')
"""
CRONTAB = r"""
tab = pathlib.Path(os.environ['FIXTURE_STATE']) / 'crontab'
if sys.argv[1:] == ['-l']:
    if tab.exists():
        sys.stdout.write(tab.read_text())
    else:
        sys.exit(1)
else:
    tab.write_text(pathlib.Path(sys.argv[1]).read_text())
"""
OPENSSL = r"""
print(os.environ.get('FIXTURE_SECRET') or os.urandom(32).hex())
"""


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="QA", GIT_AUTHOR_EMAIL="qa@example.test",
                            GIT_COMMITTER_NAME="QA", GIT_COMMITTER_EMAIL="qa@example.test"))


@pytest.fixture
def env(tmp_path):
    apps = tmp_path / "apps"
    source = apps / "demo.coil.test"
    (source / "app").mkdir(parents=True)
    (source / "app/__init__.py").write_text("# synthetic\n")
    (source / "Dockerfile").write_text("FROM scratch\n")
    (source / ".gitignore").write_text(".env\ndata/\n")
    (source / "docker-compose.yml").write_text("services: {}\n")
    _git(source, "init", "-q")
    _git(source, "add", ".")
    _git(source, "commit", "-q", "-m", "release")
    _git(source, "tag", "v-test-1")
    # The live source instance: its own .env (SMTP block), data and a locally edited compose file.
    (source / ".env").write_text("SECRET_KEY=demo-secret\nBASE_URL=https://demo.coil.test\nSMTP_HOST=smtp.example.test\n")
    (source / "data").mkdir()
    (source / "data/practice.db").write_bytes(b"demo")
    (source / "docker-compose.yml").write_text("services: {web: {build: .}}\n")
    state = tmp_path / "state"
    state.mkdir()
    (state / "crontab").write_text("20 2 * * * /home/deploy/scripts/coil-backup.sh >> /var/log/coil-backup.log 2>&1\n")
    commands = tmp_path / "commands"
    commands.mkdir()
    for name, body in (("docker", DOCKER), ("curl", CURL), ("crontab", CRONTAB), ("openssl", OPENSSL),
                       ("chown", ""), ("getent", "")):
        p = commands / name
        p.write_text("#!" + sys.executable + "\nimport sys, os, pathlib, json\n" + body + "\n")
        p.chmod(0o700)
    e = dict(os.environ, PATH=str(commands) + ":" + os.environ["PATH"], COIL_APPS_DIR=str(apps),
             COIL_SOURCE_APP=str(source), COIL_BASE_DOMAIN="coil.test",
             COIL_CF_TOKEN_FILE=str(tmp_path / "absent"), COIL_BACKUP_SCRIPT=str(ROOT / "ops/backup.sh"),
             FIXTURE_STATE=str(state))
    for k in ("COIL_COMMIT", "COIL_VERSION"):
        e.pop(k, None)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True).stdout.strip()

    def run(*args, **extra):
        return subprocess.run(["bash", str(SCRIPT), *args], env=dict(e, **extra), capture_output=True,
                              text=True, timeout=120)
    return dict(run=run, apps=apps, source=source, state=state, commit=commit, dir=apps / DOMAIN)


ARGS = ("rehearsal", "QA Rehearsal Firm", "owner@example.test")


def test_clean_source_builds_with_exact_pin_and_reports(env):
    r = env["run"](*ARGS)
    assert r.returncode == 0, r.stdout + r.stderr
    built = json.loads((env["state"] / "built.json").read_text())
    assert built == {"COIL_COMMIT": env["commit"], "COIL_VERSION": "v-test-1"}
    docker_log = (env["state"] / "docker.log").read_text()
    assert f"--build-arg COIL_COMMIT={env['commit']}" in docker_log
    assert "up -d --build" not in docker_log, "build args must not be skipped by an implicit compose build"
    out = r.stdout
    assert f"release pin:   /health reports {env['commit']}" in out
    assert "readiness:     /health/ready 200" in out
    assert "owner setup:   /setup is open for owner@example.test" in out
    assert f"backups:       enrolled, the nightly backup discovers {DOMAIN}" in out
    assert "isolation:     own data dir" in out
    assert "FAILED" not in out
    env_text = (env["dir"] / ".env").read_text()
    secret = [l for l in env_text.splitlines() if l.startswith("SECRET_KEY=")][0].split("=", 1)[1]
    assert secret and secret not in out + r.stderr and "demo-secret" not in env_text
    assert not (env["dir"] / ".git").exists()


def test_dirty_source_is_refused_before_anything_is_created(env):
    (env["source"] / "app/__init__.py").write_text("# edited, not committed\n")
    r = env["run"](*ARGS)
    assert r.returncode == 1
    assert "uncommitted changes" in r.stderr
    assert not env["dir"].exists()
    assert not (env["state"] / "docker.log").exists()


def test_untracked_code_counts_as_dirty(env):
    (env["source"] / "app/new_module.py").write_text("x = 1\n")
    assert env["run"](*ARGS).returncode == 1


def test_allow_dirty_builds_and_says_so(env):
    (env["source"] / "app/__init__.py").write_text("# edited, not committed\n")
    r = env["run"]("--allow-dirty", *ARGS)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "built from a DIRTY source with --allow-dirty" in r.stdout


def test_env_commit_must_match_the_checkout(env):
    r = env["run"](*ARGS, COIL_COMMIT="0" * 40)
    assert r.returncode == 1 and "COIL_COMMIT" in r.stderr
    assert not env["dir"].exists()
    r = env["run"](*ARGS, COIL_COMMIT=env["commit"], COIL_VERSION="hosted-20261011")
    assert r.returncode == 0, r.stdout + r.stderr
    assert json.loads((env["state"] / "built.json").read_text())["COIL_VERSION"] == "hosted-20261011"


def test_source_without_git_needs_an_explicit_pin(env):
    import shutil
    shutil.rmtree(env["source"] / ".git")
    r = env["run"](*ARGS)
    assert r.returncode == 1 and "not a git checkout" in r.stderr
    r = env["run"](*ARGS, COIL_COMMIT="abc1234def", COIL_VERSION="hosted-1")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "release pin:   /health reports abc1234def" in r.stdout


def test_wrong_commit_in_health_fails_the_report(env):
    r = env["run"](*ARGS, FIXTURE_HEALTH_COMMIT="unknown")
    assert r.returncode == 1
    assert "release pin:   FAILED, /health reports 'unknown'" in r.stdout
    assert "Do not hand this firm over" in r.stderr


def test_not_ready_fails_the_report(env):
    r = env["run"](*ARGS, FIXTURE_READY="503")
    assert r.returncode == 1 and "readiness:     FAILED" in r.stdout


def test_backup_enrollment_needs_the_nightly_cron(env):
    (env["state"] / "crontab").write_text("# nothing\n")
    r = env["run"](*ARGS)
    assert r.returncode == 1
    assert "no nightly backup line is in root's crontab" in r.stdout


def test_shared_secret_key_is_detected_without_printing_it(env):
    other = env["apps"] / "other.coil.test"
    (other / "data").mkdir(parents=True)
    (other / ".env").write_text("SECRET_KEY=deadbeefcafe\n")
    r = env["run"](*ARGS, FIXTURE_SECRET="deadbeefcafe")
    assert r.returncode == 1
    assert "SECRET_KEY with other.coil.test" in r.stdout
    assert "deadbeefcafe" not in r.stdout + r.stderr


def test_shared_data_dir_and_compose_project_are_detected(env):
    other = env["apps"] / "other.coil.test"
    other.mkdir()
    (other / "data").symlink_to(env["dir"] / "data")     # dangling until the new firm exists
    r = env["run"](*ARGS, FIXTURE_EXTRA_WD=str(other))
    assert r.returncode == 1
    assert "data directory with other.coil.test" in r.stdout
    assert f"compose project rehearsalcoiltest with {other}" in r.stdout


def test_dry_run_reports_the_pin_and_changes_nothing(env):
    r = env["run"]("--dry-run", *ARGS)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"would: docker compose build --build-arg COIL_COMMIT={env['commit']} --build-arg COIL_VERSION=v-test-1" in r.stdout
    assert "would: check /health reports commit" in r.stdout
    assert not env["dir"].exists()
    assert not (env["state"] / "docker.log").exists()


def test_dry_run_still_refuses_a_dirty_source(env):
    (env["source"] / "app/__init__.py").write_text("# edited\n")
    assert env["run"]("--dry-run", *ARGS).returncode == 1


@pytest.mark.parametrize("args", [(), ("rehearsal",), ("Bad", "F", "e@x.test"), ("rehearsal", "F", "e@x.test", "extra"),
                                  ("--nope", "rehearsal", "F", "e@x.test")])
def test_bad_arguments(env, args):
    assert env["run"](*args).returncode == 2
