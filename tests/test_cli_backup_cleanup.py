"""Real process death must not leak workspaces or remove another live backup."""
import hashlib
import multiprocessing
import os
import signal
import stat
import sqlite3
import tarfile

import pytest
from tests.test_cli_backup_overlap import fixture_app


def restored_cents(path, tmp_path):
    target = tmp_path / (path.name + '.db')
    with tarfile.open(path) as tar:
        target.write_bytes(tar.extractfile('data/practice.db').read())
        assert tar.extractfile('data/uploads/control.txt').read() == b'synthetic upload'
    with sqlite3.connect(target) as con:
        assert con.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        return con.execute('SELECT cents FROM fixture').fetchone()[0]


@pytest.mark.parametrize('stage,kill', [
    ('initialization', True),
    ('before_archive', True), ('after_upload', True), ('after_publish', True),
    ('before_archive', False), ('after_upload', False), ('after_publish', False),
])
def test_cleanup_reclaims_dead_jobs_but_preserves_live_jobs(tmp_path, monkeypatch, stage, kill):
    from app import cli
    app, data, source = fixture_app(tmp_path, monkeypatch)
    monkeypatch.setenv('COIL_BACKUP_KEEP', '0')
    with app.app_context(): prior = cli.backup()
    prior_hash = hashlib.sha256(prior.read_bytes()).hexdigest()
    with sqlite3.connect(source) as con: con.execute('UPDATE fixture SET cents=200')
    ctx = multiprocessing.get_context('fork')
    ready, release = ctx.Event(), ctx.Event()

    def barrier():
        ready.set()
        assert release.wait(15), 'parent did not release child'

    def child():
        if stage == 'initialization':
            original = cli.tempfile.mkdtemp
            def wrapped(*a, **kw): result = original(*a, **kw); barrier(); return result
            cli.tempfile.mkdtemp = wrapped
        elif stage == 'before_archive':
            original = cli.tarfile.open
            def wrapped(*a, **kw): barrier(); return original(*a, **kw)
            cli.tarfile.open = wrapped
        elif stage == 'after_upload':
            original = cli.tarfile.TarFile.add
            def wrapped(self, name, *a, **kw):
                result = original(self, name, *a, **kw)
                if kw.get('arcname') == 'data/uploads': barrier()
                return result
            cli.tarfile.TarFile.add = wrapped
        else:
            original = cli.os.link
            def wrapped(*a, **kw): result = original(*a, **kw); barrier(); return result
            cli.os.link = wrapped
        with app.app_context(): cli.backup()

    proc = ctx.Process(target=child); proc.start()
    try:
        assert ready.wait(10)
        if kill:
            os.kill(proc.pid, signal.SIGKILL); proc.join(10)
            assert proc.exitcode == -signal.SIGKILL
        with sqlite3.connect(source) as con: con.execute('UPDATE fixture SET cents=300')
        with app.app_context(): later = cli.backup()
        assert restored_cents(later, tmp_path) == 300
        if not kill:
            assert proc.is_alive()
            release.set(); proc.join(10); assert proc.exitcode == 0
    finally:
        if proc.is_alive(): proc.kill(); proc.join(5)
    assert hashlib.sha256(prior.read_bytes()).hexdigest() == prior_hash
    archives = list((data / 'backups').glob('coil-backup-*.tar.gz'))
    assert all(stat.S_IMODE(p.stat().st_mode) == 0o600 for p in archives)
    amounts = sorted(restored_cents(p, tmp_path) for p in archives)
    assert amounts == ([100, 300] if kill and stage != 'after_publish' else [100, 200, 300])
    assert not list(data.glob('.backup-snapshot*'))
    assert not list((data / 'backups').glob('.*.partial'))
    assert not list((data / 'backups').glob('.coil-backup-job-*'))


def test_cleanup_leaves_legacy_files_and_symlink_targets_alone(tmp_path, monkeypatch):
    from app import cli
    app, data, source = fixture_app(tmp_path, monkeypatch)
    backups = data / 'backups'; backups.mkdir()
    legacy = [data / '.backup-snapshot.legacy', backups / '.coil-backup-legacy.partial']
    for path in legacy: path.write_bytes(b'possibly owned by an older running process')
    outside = tmp_path / 'outside'; outside.mkdir()
    (outside / 'keep').write_bytes(b'unrelated data')
    (backups / '.coil-backup-job-link').symlink_to(outside, target_is_directory=True)
    with app.app_context(): archive = cli.backup()
    assert restored_cents(archive, tmp_path) == 100
    assert all(p.read_bytes() == b'possibly owned by an older running process' for p in legacy)
    assert (outside / 'keep').read_bytes() == b'unrelated data'
    assert (backups / '.coil-backup-job-link').is_symlink()
