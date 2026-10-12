"""ops/export-firm.sh: builds the export inside the firm's container, copies it out with 0600
permissions without replacing anything, and checks the copy with the host's python3.

docker is a stub. Its `compose exec` places a real export, built from a seeded database, where
the container would have written it, and prints the line export_firm prints.

Run: .venv/bin/python -m pytest tests/test_export_firm_script.py -q
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "ops/export-firm.sh"

DOCKER_STUB = """#!/bin/sh
echo "docker $*" >> "$CALL_LOG"
case "$*" in
  *"compose exec -T web python -m app.cli export_firm --slug synthetic"*)
    mkdir -p "$FIXTURE_FIRM/data/exports"
    cp "$FIXTURE_ZIP" "$FIXTURE_FIRM/data/exports/coil-export-synthetic-20261011T000000Z.zip"
    echo "export_firm: 80 tables"
    echo "EXPORT_FILE=${FIXTURE_REPORT:-/app/data/exports/coil-export-synthetic-20261011T000000Z.zip}"
    exit "${FIXTURE_EXIT:-0}" ;;
esac
exit 0
"""


@pytest.fixture(scope="module")
def export_zip(tmp_path_factory):
    root = tmp_path_factory.mktemp("script_export")
    db = root / "practice.db"
    seeded = subprocess.run([sys.executable, str(ROOT / "seed.py")], cwd=ROOT, capture_output=True, text=True,
                            env=dict(os.environ, DATABASE_URL=f"sqlite:///{db}", STRIPE_SECRET_KEY="", SMTP_HOST=""))
    assert seeded.returncode == 0, seeded.stderr
    sys.path.insert(0, str(ROOT))
    from app.firm_export import build_export
    (root / "uploads").mkdir()
    return build_export(db, root / "out", root / "uploads", None, slug="synthetic")


@pytest.fixture
def host(tmp_path, export_zip):
    firm = tmp_path / "apps/synthetic.coil.test"
    (firm / "data").mkdir(parents=True)
    (firm / "data/practice.db").write_bytes(b"live database stays untouched")
    commands = tmp_path / "commands"
    commands.mkdir()
    (commands / "docker").write_text(DOCKER_STUB)
    (commands / "docker").chmod(0o700)
    log = tmp_path / "calls"
    env = dict(os.environ, PATH=str(commands) + ":" + os.environ["PATH"], CALL_LOG=str(log),
               COIL_APPS_DIR=str(tmp_path / "apps"), COIL_BASE_DOMAIN="coil.test",
               COIL_EXPORT_ROOT=str(tmp_path / "exports"), COIL_PYTHON=sys.executable,
               FIXTURE_FIRM=str(firm), FIXTURE_ZIP=str(export_zip))

    def run(*args, **extra):
        return subprocess.run(["bash", str(SCRIPT), *args], env=dict(env, **extra),
                              capture_output=True, text=True, timeout=60)
    return run, firm, tmp_path / "exports/synthetic", log


def test_export_is_copied_private_and_verified(host, export_zip):
    run, firm, dest, log = host
    result = run("synthetic")
    assert result.returncode == 0, result.stdout + result.stderr
    final = dest / "coil-export-synthetic-20261011T000000Z.zip"
    assert final.read_bytes() == export_zip.read_bytes()
    assert oct(final.stat().st_mode & 0o777) == "0o600"
    assert oct(dest.stat().st_mode & 0o777) == "0o700"
    assert "OK coil-export-synthetic" in result.stdout and f"Verified export: {final}" in result.stdout
    assert not list(dest.glob(".*.partial"))
    # The container's copy inside the firm's data folder is removed once the copy passes.
    assert not (firm / "data/exports/coil-export-synthetic-20261011T000000Z.zip").exists()
    assert (firm / "data/practice.db").read_bytes() == b"live database stays untouched"
    assert "compose exec -T web python -m app.cli export_firm --slug synthetic" in log.read_text()


def test_an_existing_export_is_never_replaced(host):
    run, firm, dest, log = host
    dest.mkdir(parents=True)
    existing = dest / "coil-export-synthetic-20261011T000000Z.zip"
    existing.write_bytes(b"earlier export")
    result = run("synthetic")
    assert result.returncode == 1
    assert "already exists" in result.stderr
    assert existing.read_bytes() == b"earlier export"
    assert not list(dest.glob(".*.partial"))


def test_a_copy_that_fails_verification_is_reported_and_the_source_kept(host, export_zip, tmp_path):
    run, firm, dest, log = host
    broken = tmp_path / "broken.zip"
    with zipfile.ZipFile(export_zip) as zin, zipfile.ZipFile(broken, "w") as zout:
        for n in zin.namelist():
            zout.writestr(n, b"tampered" if n == "README.txt" else zin.read(n))
    result = run("synthetic", FIXTURE_ZIP=str(broken))
    assert result.returncode == 1
    assert "did not pass verification" in result.stderr
    assert "README.txt does not match the manifest" in result.stdout
    assert (firm / "data/exports/coil-export-synthetic-20261011T000000Z.zip").exists()


def test_container_failure_or_odd_report_copies_nothing(host):
    run, firm, dest, log = host
    result = run("synthetic", FIXTURE_EXIT="1")
    assert result.returncode == 1 and "Nothing copied" in result.stderr
    assert not dest.exists() or not list(dest.iterdir())
    result = run("synthetic", FIXTURE_REPORT="/etc/passwd")
    assert result.returncode == 1 and "did not report an export file" in result.stderr
    assert not dest.exists() or not list(dest.iterdir())


def test_dry_run_touches_nothing(host):
    run, firm, dest, log = host
    result = run("synthetic", "--dry-run")
    assert result.returncode == 0, result.stderr
    assert "would: (cd" in result.stdout and "export_firm --slug synthetic" in result.stdout
    assert not log.exists()
    assert not dest.exists()


@pytest.mark.parametrize("args", [(), ("../synthetic",), ("/tmp/firm",), ("",), ("-firm",), ("firm-",),
                                  ("Synthetic",), ("syn thetic",), ("synthetic", "--dry-runn"),
                                  ("synthetic", "--dry-run", "extra")])
def test_malformed_arguments_are_refused_before_anything_runs(host, args):
    run, firm, dest, log = host
    assert run(*args).returncode == 2
    assert not log.exists()
    assert not dest.exists()


def test_unknown_firm_is_refused(host):
    run, firm, dest, log = host
    result = run("nosuchfirm")
    assert result.returncode == 1 and "no Coil instance" in result.stderr
    assert not log.exists()


def test_remove_firm_points_at_the_export_but_still_refuses_purge(tmp_path):
    (tmp_path / "apps/synthetic.coil.test/data").mkdir(parents=True)
    env = dict(os.environ, COIL_APPS_DIR=str(tmp_path / "apps"), COIL_BASE_DOMAIN="coil.test")
    r = subprocess.run(["bash", str(ROOT / "ops/remove-firm.sh"), "synthetic", "--purge"], env=env,
                       capture_output=True, text=True, timeout=10)
    assert r.returncode == 1
    assert "REFUSING purge" in r.stderr and "ops/export-firm.sh synthetic" in r.stderr
    assert (tmp_path / "apps/synthetic.coil.test/data").is_dir()
    assert shutil.which("bash")
