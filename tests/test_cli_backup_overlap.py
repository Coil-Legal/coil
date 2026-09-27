"""The CLI and pre-update backup must own snapshots and publish only complete archives."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import sqlite3
import tarfile
import threading

import pytest
from flask import Flask


def fixture_app(tmp_path, monkeypatch):
    from app import cli
    data = tmp_path / 'data'
    data.mkdir()
    source = data / 'practice.db'
    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE fixture (name TEXT, cents INTEGER)')
        db.execute('INSERT INTO fixture VALUES (?,100)', ('QA-CLI-BACKUP-20260927',))
    db.close()
    (data / 'uploads').mkdir()
    (data / 'uploads/control.txt').write_text('synthetic upload')
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(source)
    monkeypatch.setattr(cli, 'DATA_DIR', str(data))
    monkeypatch.setattr(cli, 'now', lambda: datetime(2026, 9, 27, 1, 45))
    return app, data, source


@pytest.mark.parametrize('fail_second', [False, True])
def test_cli_overlap_preserves_first_snapshot_and_prior_archive(tmp_path, monkeypatch, fail_second):
    from app import cli
    app, data, source = fixture_app(tmp_path, monkeypatch)
    ready, release = threading.Event(), threading.Event()
    role = threading.local()
    original_open = tarfile.open

    def archive_open(*args, **kwargs):
        if getattr(role, 'job', '') == 'first':
            ready.set()
            assert release.wait(10), 'snapshot release timed out'
        elif fail_second and getattr(role, 'job', '') == 'second':
            raise OSError('controlled archive creation failure')
        return original_open(*args, **kwargs)

    monkeypatch.setattr(cli.tarfile, 'open', archive_open)

    def run(job):
        role.job = job
        with app.app_context():
            return cli.backup()

    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(run, 'first')
        try:
            assert ready.wait(10), 'first snapshot did not reach barrier'
            with sqlite3.connect(source) as db:
                db.execute('UPDATE fixture SET cents=200')
            db.close()
            if fail_second:
                with pytest.raises(OSError, match='controlled archive'):
                    run('second')
            else:
                run('second')
        finally:
            release.set()
        first.result(timeout=10)

    archives = list((data / 'backups').glob('coil-backup-*.tar.gz'))
    assert len(archives) == (1 if fail_second else 2)
    amounts = []
    for i, path in enumerate(archives):
        with original_open(path) as archive:
            restored = tmp_path / f'restored-{i}.db'
            restored.write_bytes(archive.extractfile('data/practice.db').read())
            assert archive.extractfile('data/uploads/control.txt').read() == b'synthetic upload'
        with sqlite3.connect(restored) as db:
            assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
            name, cents = db.execute('SELECT name,cents FROM fixture').fetchone()
            assert name == 'QA-CLI-BACKUP-20260927'
            amounts.append(cents)
        db.close()
    assert sorted(amounts) == ([100] if fail_second else [100, 200])
    assert not list(data.glob('.backup-snapshot*'))
    assert not list((data / 'backups').glob('.*partial*'))


def test_cli_failed_archive_is_not_published_and_preserves_previous(tmp_path, monkeypatch):
    from app import cli
    app, data, source = fixture_app(tmp_path, monkeypatch)
    with app.app_context():
        previous = cli.backup()
    saved = previous.read_bytes()
    original_add = tarfile.TarFile.add

    def fail_on_upload(self, name, *args, **kwargs):
        if kwargs.get('arcname') == 'data/uploads':
            raise OSError('controlled upload read failure')
        return original_add(self, name, *args, **kwargs)

    monkeypatch.setattr(tarfile.TarFile, 'add', fail_on_upload)
    with app.app_context(), pytest.raises(OSError, match='controlled upload'):
        cli.backup()
    assert previous.read_bytes() == saved
    assert list((data / 'backups').glob('coil-backup-*.tar.gz')) == [previous]
    assert not list(data.glob('.backup-snapshot*'))
    assert not list((data / 'backups').glob('.*partial*'))
