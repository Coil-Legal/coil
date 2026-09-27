"""Bad archives must be rejected before changing the restore target."""
import io
import os
import sqlite3
import subprocess
import tarfile
from pathlib import Path
import pytest
SCRIPT = Path(__file__).resolve().parents[1] / 'ops/restore.sh'

def archive(path, prefix, content, duplicate=False):
    with tarfile.open(path, 'w:gz') as tar:
        for name, data in [(prefix+'practice.db', content), (prefix+'uploads/fixture.txt', b'synthetic upload'), ('.env',b'SECRET_KEY=synthetic-only\n')]:
            item=tarfile.TarInfo(name);item.size=len(data);tar.addfile(item,io.BytesIO(data))
        if duplicate:
            item=tarfile.TarInfo(prefix+'practice.db');item.size=len(content);tar.addfile(item,io.BytesIO(content))
    return path

def run(path,target,scratch):
    return subprocess.run(['bash',str(SCRIPT),str(path),str(target)],capture_output=True,text=True,env=dict(os.environ,TMPDIR=str(scratch)))

@pytest.mark.parametrize('prefix',['','./','data/','./data/'])
def test_corrupt_archive_leaves_target_unchanged_and_good_retry_works(tmp_path,prefix):
    target=tmp_path/'install';target.mkdir();(target/'app.py').write_bytes(b'# synthetic app')
    scratch=tmp_path/'scratch';scratch.mkdir()
    bad=archive(tmp_path/'bad.tar.gz',prefix,b'synthetic corrupt database')
    result=run(bad,target,scratch)
    assert result.returncode!=0 and 'FAILED' in result.stderr
    assert sorted(p.name for p in target.iterdir())==['app.py']
    assert (target/'app.py').read_bytes()==b'# synthetic app'
    assert not list(scratch.iterdir()), 'validation scratch files leaked'
    source=tmp_path/'source.db'
    with sqlite3.connect(source) as db:
        db.execute('create table fixture(cents integer)');db.execute('insert into fixture values(12345)')
    good=archive(tmp_path/'good.tar.gz',prefix,source.read_bytes())
    result=run(good,target,scratch)
    assert result.returncode==0,result.stderr
    assert (target/'data/practice.db').read_bytes()==source.read_bytes()
    with sqlite3.connect(target/'data/practice.db') as db:assert db.execute('select cents from fixture').fetchone()==(12345,)
    assert (target/'data/uploads/fixture.txt').read_bytes()==b'synthetic upload'
    assert not list(scratch.iterdir())

@pytest.mark.parametrize('prefix',['','data/'])
@pytest.mark.parametrize('kind',['empty','duplicate'])
def test_empty_or_duplicate_database_members_are_rejected_before_target_creation(tmp_path,prefix,kind):
    source=tmp_path/'source.db'
    with sqlite3.connect(source) as db:db.execute('create table fixture(cents integer)')
    path=archive(tmp_path/'bad.tar.gz',prefix,b'' if kind=='empty' else source.read_bytes(),duplicate=kind=='duplicate')
    scratch=tmp_path/'scratch';scratch.mkdir();target=tmp_path/'install'
    result=run(path,target,scratch)
    assert result.returncode!=0
    assert not target.exists()
    assert not list(scratch.iterdir())
