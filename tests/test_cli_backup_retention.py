"""A second completed backup may prune files while the first inspects them."""
import os
from pathlib import Path
import sqlite3
import tarfile

import pytest
from flask import Flask


@pytest.mark.parametrize('stage', ['size', 'scan', 'unlink'])
def test_concurrent_retention_tolerates_already_pruned_archives(tmp_path, monkeypatch, stage):
    from app import cli
    data = tmp_path / 'data'
    data.mkdir()
    source = data / 'practice.db'
    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE fixture (name TEXT, cents INTEGER)')
        db.execute('INSERT INTO fixture VALUES (?,100)', ('QA-CLI-RETENTION-20260927',))
    db.close()
    (data / 'uploads').mkdir()
    (data / 'uploads/control.txt').write_text('synthetic retention upload')
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(source)
    monkeypatch.setattr(cli, 'DATA_DIR', str(data))
    keep = 1 if stage == 'size' else 2
    monkeypatch.setenv('COIL_BACKUP_KEEP', str(keep))
    with app.app_context():
        old = [cli.backup() for _ in range(keep)]
    for i, path in enumerate(old):
        os.utime(path, (i + 1, i + 1))
    original_stat, original_unlink = Path.stat, Path.unlink
    fired = False
    second = None

    def interleave():
        nonlocal fired, second
        fired = True
        with sqlite3.connect(source) as db:
            db.execute('UPDATE fixture SET cents=200')
        db.close()
        second = cli.backup()

    def stat(path, *args, **kwargs):
        if not fired and ((stage == 'size' and path.parent == data / 'backups'
                           and path.name.endswith('.tar.gz') and path not in old)
                          or (stage == 'scan' and path == old[0])):
            interleave()
        return original_stat(path, *args, **kwargs)

    def unlink(path, *args, **kwargs):
        if not fired and stage == 'unlink' and path == old[0]:
            interleave()
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'stat', stat)
    monkeypatch.setattr(Path, 'unlink', unlink)
    with app.app_context():
        first = cli.backup()
    assert fired, 'second backup never reached the intended interleaving'
    remaining = list((data / 'backups').glob('coil-backup-*.tar.gz'))
    assert len(remaining) == keep
    assert second in remaining
    assert all(p not in remaining for p in old)
    amounts = []
    for i, archive in enumerate(remaining):
        with tarfile.open(archive) as tar:
            restored = tmp_path / f'restored-{i}.db'
            restored.write_bytes(tar.extractfile('data/practice.db').read())
            assert tar.extractfile('data/uploads/control.txt').read() == b'synthetic retention upload'
        with sqlite3.connect(restored) as db:
            assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
            name, cents = db.execute('SELECT name,cents FROM fixture').fetchone()
            assert name == 'QA-CLI-RETENTION-20260927'
            amounts.append(cents)
        db.close()
    assert sorted(amounts) == ([200] if keep == 1 else [100, 200])
    assert not list(data.glob('.backup-snapshot*'))
    assert not list((data / 'backups').glob('.*partial*'))
