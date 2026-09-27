"""An extraction error must not strand a partial restore in the target."""
import io
import os
from pathlib import Path
import sqlite3
import subprocess
import tarfile

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/restore.sh'


def make_archive(path, database, prefix, broken=False):
    entries = [(prefix + 'practice.db', database),
               ('.env', b'SECRET_KEY=synthetic-extraction-fixture\n'),
               (prefix + 'uploads/fixture.txt', b'synthetic upload')]
    if broken:
        entries.extend([(prefix + 'pdf/collision', b'a file, not a directory'),
                        (prefix + 'pdf/collision/report.pdf', b'synthetic PDF')])
    with tarfile.open(path, 'w:gz') as archive:
        for name, content in entries:
            item = tarfile.TarInfo(name)
            item.size = len(content)
            archive.addfile(item, io.BytesIO(content))


def snapshot(path):
    if not path.exists():
        return None
    return {str(p.relative_to(path)): p.read_bytes() if p.is_file() else None
            for p in path.rglob('*')}


@pytest.mark.parametrize('prefix', ['', './', 'data/', './data/'])
@pytest.mark.parametrize('existing', [False, True])
def test_failed_extraction_preserves_target_and_allows_valid_retry(tmp_path, prefix, existing):
    source = tmp_path / 'source.db'
    with sqlite3.connect(source) as db:
        db.execute('create table fixture(cents integer)')
        db.execute('insert into fixture values(12345)')
    bad = tmp_path / 'bad.tar.gz'
    good = tmp_path / 'good.tar.gz'
    make_archive(bad, source.read_bytes(), prefix, broken=True)
    make_archive(good, source.read_bytes(), prefix)
    target = tmp_path / 'install'
    if existing:
        (target / 'data').mkdir(parents=True)
        target.chmod(0o700)
        (target / 'app.py').write_bytes(b'# synthetic application')
    before = snapshot(target)
    scratch = tmp_path / 'scratch'
    scratch.mkdir()
    env = dict(os.environ, TMPDIR=str(scratch))
    result = subprocess.run(['bash', str(SCRIPT), str(bad), str(target)],
                            capture_output=True, text=True, env=env)
    assert result.returncode != 0
    assert 'restored into' not in result.stdout
    assert snapshot(target) == before, result.stderr
    assert not list(scratch.iterdir())
    result = subprocess.run(['bash', str(SCRIPT), str(good), str(target)],
                            capture_output=True, text=True, env=env)
    assert result.returncode == 0, result.stderr
    with sqlite3.connect(target / 'data/practice.db') as db:
        assert db.execute('select cents from fixture').fetchone() == (12345,)
    assert (target / 'data/uploads/fixture.txt').read_bytes() == b'synthetic upload'
    assert (target / '.env').read_bytes() == b'SECRET_KEY=synthetic-extraction-fixture\n'
    if existing:
        assert (target / 'app.py').read_bytes() == b'# synthetic application'
        assert target.stat().st_mode & 0o777 == 0o700
    assert not list(scratch.iterdir())
