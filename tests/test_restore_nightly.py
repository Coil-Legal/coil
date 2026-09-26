"""Restore the root-layout archives emitted by ops/backup.sh."""
import io
import sqlite3
import subprocess
import tarfile
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops' / 'restore.sh'


def archive(tmp_path, prefix='', env=True):
    source = tmp_path / 'source.db'
    with sqlite3.connect(source) as conn:
        conn.execute('create table marker (value text)')
        conn.execute("insert into marker values ('synthetic nightly recovery')")
    result = tmp_path / 'nightly.tar.gz'
    with tarfile.open(result, 'w:gz') as tar:
        tar.add(source, arcname=prefix + 'practice.db')
        for name, data in [('uploads/1/evidence.txt', b'synthetic upload'),
                           ('pdf/invoice.pdf', b'synthetic PDF bytes')]:
            item = tarfile.TarInfo(prefix + name)
            item.size = len(data)
            tar.addfile(item, io.BytesIO(data))
        if env:
            data = b'SECRET_KEY=synthetic-test-only\n'
            item = tarfile.TarInfo('.env')
            item.size = len(data)
            tar.addfile(item, io.BytesIO(data))
    return result


def test_nightly_root_archive_restores_all_expected_paths(tmp_path):
    target = tmp_path / 'install'
    out = subprocess.run(['bash', str(SCRIPT), str(archive(tmp_path)), str(target)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    with sqlite3.connect(target / 'data' / 'practice.db') as conn:
        assert conn.execute('select value from marker').fetchone()[0] == 'synthetic nightly recovery'
    assert (target / 'data/uploads/1/evidence.txt').read_bytes() == b'synthetic upload'
    assert (target / 'data/pdf/invoice.pdf').read_bytes() == b'synthetic PDF bytes'
    assert (target / '.env').read_bytes() == b'SECRET_KEY=synthetic-test-only\n'
    assert not (target / 'practice.db').exists()
    assert 'does NOT contain .env' not in out.stdout


@pytest.mark.parametrize('prefix', ['', 'data/'])
def test_existing_environment_is_never_overwritten(tmp_path, prefix):
    target = tmp_path / 'install'
    target.mkdir()
    (target / '.env').write_text('SECRET_KEY=existing-synthetic-value\n')
    out = subprocess.run(['bash', str(SCRIPT), str(archive(tmp_path, prefix=prefix)), str(target)], capture_output=True, text=True)
    assert out.returncode != 0
    assert (target / '.env').read_text() == 'SECRET_KEY=existing-synthetic-value\n'
    assert not (target / 'data/practice.db').exists()


@pytest.mark.parametrize('prefix', ['', './'])
def test_nightly_without_environment_keeps_original_key_warning(tmp_path, prefix):
    target = tmp_path / 'install'
    out = subprocess.run(['bash', str(SCRIPT), str(archive(tmp_path, prefix=prefix, env=False)), str(target)], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert (target / 'data/practice.db').is_file()
    assert not (target / '.env').exists()
    assert 'does NOT contain .env' in out.stdout
    assert 'SECRET_KEY' in out.stdout


def test_both_database_layouts_are_refused_before_extraction(tmp_path):
    source = archive(tmp_path)
    mixed = tmp_path / 'mixed.tar.gz'
    with tarfile.open(source, 'r:gz') as src, tarfile.open(mixed, 'w:gz') as dst:
        for item in src:
            dst.addfile(item, src.extractfile(item))
        dst.add(tmp_path / 'source.db', arcname='data/practice.db')
    target = tmp_path / 'install'
    out = subprocess.run(['bash', str(SCRIPT), str(mixed), str(target)], capture_output=True, text=True)
    assert out.returncode != 0
    assert not (target / 'data/practice.db').exists()
