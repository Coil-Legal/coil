"""Recovery must validate SQLite even on hosts without the sqlite3 CLI."""
import io
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tarfile

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/restore.sh'


def restore(tmp_path, content, prefix='', python=True):
    archive = tmp_path / 'fixture.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        item = tarfile.TarInfo(prefix + 'practice.db')
        item.size = len(content)
        tar.addfile(item, io.BytesIO(content))
    commands = tmp_path / 'commands'
    commands.mkdir()
    for name in ['tar', 'sed', 'grep', 'mkdir', 'du', 'cut', 'find', 'wc', 'tr', 'head', 'mktemp', 'rm', 'cp']:
        (commands / name).symlink_to(shutil.which(name))
    if python:
        (commands / 'python3').symlink_to(sys.executable)
    target = tmp_path / 'restore'
    result = subprocess.run([shutil.which('bash'), str(SCRIPT), str(archive), str(target)],
                            env=dict(os.environ, PATH=str(commands)), capture_output=True, text=True)
    return result, target


@pytest.mark.parametrize('prefix', ['', 'data/'])
def test_corrupt_database_without_sqlite_cli_is_refused(tmp_path, prefix):
    result, _ = restore(tmp_path, b'corrupt synthetic database contents', prefix)
    assert result.returncode != 0, result.stdout
    assert 'FAILED' in result.stderr
    assert 'restored into' not in result.stdout


def test_python_fallback_checks_and_preserves_a_valid_database(tmp_path):
    source = tmp_path / 'source.db'
    with sqlite3.connect(source) as db:
        db.execute('create table fixture (cents integer)')
        db.execute('insert into fixture values (12345)')
    original = source.read_bytes()
    result, target = restore(tmp_path, original)
    assert result.returncode == 0, result.stderr
    assert (target / 'data/practice.db').read_bytes() == original


def test_missing_integrity_validator_refuses_before_extraction(tmp_path):
    result, target = restore(tmp_path, b'synthetic contents', python=False)
    assert result.returncode != 0, result.stdout
    assert 'FAILED' in result.stderr
    assert not target.exists()
