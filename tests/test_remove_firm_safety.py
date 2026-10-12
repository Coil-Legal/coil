"""Offboarding must not destroy data on stale backup evidence or malformed input."""
import os
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/remove-firm.sh'


@pytest.fixture
def removal(tmp_path):
    app = tmp_path / 'apps/synthetic.coil.test'
    (app / 'data').mkdir(parents=True)
    (app / 'data/practice.db').write_bytes(b'preserved firm data')
    commands = tmp_path / 'commands'
    commands.mkdir()
    log = tmp_path / 'calls'
    for name in ('docker', 'crontab', 'curl'):
        stub = commands / name
        stub.write_text('#!/bin/sh\necho "' + name + ' $*" >> "$CALL_LOG"\nexit 0\n')
        stub.chmod(0o700)
    env = dict(os.environ, PATH=str(commands) + ':' + os.environ['PATH'],
               CALL_LOG=str(log), COIL_APPS_DIR=str(tmp_path / 'apps'),
               COIL_BASE_DOMAIN='coil.test', COIL_CF_TOKEN_FILE=str(tmp_path / 'absent'))

    def run(*args):
        return subprocess.run(['bash', str(SCRIPT), *args], env=env,
                              capture_output=True, text=True, timeout=10)
    return run, app, log


def test_purge_refused_before_container_cron_or_dns_changes(removal):
    run, app, log = removal
    # Even a plausible archive must not authorize deletion without verified recovery.
    (app / 'data/old-backup.tar.gz').write_bytes(b'not a verified backup')
    result = run('synthetic', '--purge')
    assert result.returncode == 1
    assert 'REFUSING purge' in result.stderr
    assert not log.exists()
    assert (app / 'data/practice.db').read_bytes() == b'preserved firm data'
    assert (app / 'data/old-backup.tar.gz').exists()


@pytest.mark.parametrize('args', [(), ('../synthetic',), ('/tmp/firm',),
    ('',), ('-firm',), ('firm-',), ('synthetic', '--purgee'),
    ('synthetic', '--purge', 'extra')])
def test_invalid_arguments_cannot_change_anything(removal, args):
    run, app, log = removal
    assert run(*args).returncode == 2
    assert not log.exists()
    assert (app / 'data/practice.db').read_bytes() == b'preserved firm data'


def test_normal_removal_retains_firm_data(removal):
    run, app, log = removal
    result = run('synthetic')
    assert result.returncode == 0, result.stderr
    assert 'directory KEPT' in result.stdout
    assert (app / 'data/practice.db').read_bytes() == b'preserved firm data'
    assert 'docker compose down' in log.read_text()
    assert 'crontab' in log.read_text()
