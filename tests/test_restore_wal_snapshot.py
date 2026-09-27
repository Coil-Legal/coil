"""Real WAL-mode snapshots must restore without pre-existing sidecars."""
import io
import sqlite3
import subprocess
import tarfile
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/restore.sh'

@pytest.mark.parametrize('prefix', ['', 'data/'])
def test_wal_snapshot_restores_without_sidecars(tmp_path, prefix):
    source = tmp_path / 'source.db'
    snapshot = tmp_path / 'snapshot.db'
    with sqlite3.connect(source) as src:
        assert src.execute('PRAGMA journal_mode=WAL').fetchone() == ('wal',)
        src.execute('CREATE TABLE fixture(cents INTEGER)')
        src.execute('INSERT INTO fixture VALUES (12345)')
        src.commit()
        with sqlite3.connect(snapshot) as dst:
            src.backup(dst)
    original = snapshot.read_bytes()
    assert original[18:20] == b'\x02\x02'
    archive = tmp_path / 'backup.tar.gz'
    with tarfile.open(archive, 'w:gz') as arc:
        item = tarfile.TarInfo(prefix + 'practice.db')
        item.size = len(original)
        arc.addfile(item, io.BytesIO(original))
    target = tmp_path / 'restored'
    result = subprocess.run(['bash', str(SCRIPT), str(archive), str(target)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    restored = target / 'data/practice.db'
    assert restored.read_bytes() == original
    with sqlite3.connect(restored) as db:
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert db.execute('SELECT cents FROM fixture').fetchone() == (12345,)
