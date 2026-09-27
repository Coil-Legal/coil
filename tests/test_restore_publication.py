"""Destination failures cannot leave a partially published restore."""
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

def fixture(tmp_path, prefix, existing=True, include_env=True):
    source = tmp_path/'source.db'
    with sqlite3.connect(source) as db:
        db.execute('create table fixture(cents integer)')
        db.execute('insert into fixture values(12345)')
    archive = tmp_path/'fixture.tar.gz'
    items = [(prefix+'practice.db', source.read_bytes()), (prefix+'uploads/a', b'synthetic upload')]
    if include_env:
        items.append(('.env', b'SECRET_KEY=synthetic-publication\n'))
    with tarfile.open(archive, 'w:gz') as tar:
        for name, data in items:
            info = tarfile.TarInfo(name); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    target = tmp_path/'install'
    if existing:
        (target/'data').mkdir(parents=True)
        target.chmod(0o700)
        (target/'app.py').write_bytes(b'# existing application')
    scratch = tmp_path/'scratch'; scratch.mkdir()
    return archive,target,scratch

def snapshot(target):
    if not target.exists(): return None
    return {str(p.relative_to(target)): (p.stat().st_mode & 0o777, p.read_bytes() if p.is_file() else None)
            for p in target.rglob('*')}

def run(archive,target,scratch,commands=None):
    env=dict(os.environ,TMPDIR=str(scratch))
    if commands: env['PATH']=str(commands)+os.pathsep+os.environ['PATH']
    return subprocess.run(['bash',str(SCRIPT),str(archive),str(target)],env=env,capture_output=True,text=True,timeout=15)

def check_good(target, include_env=True):
    with sqlite3.connect(target/'data/practice.db') as db:
        assert db.execute('select cents from fixture').fetchone()==(12345,)
    assert (target/'data/uploads/a').read_bytes()==b'synthetic upload'
    assert (target/'.env').exists()==include_env
    assert not list(target.glob('.coil-restore.*'))

@pytest.mark.parametrize('prefix',['','data/'])
@pytest.mark.parametrize('existing',[False,True])
@pytest.mark.parametrize('include_env',[False,True])
def test_destination_write_failure_leaves_target_unchanged(tmp_path,prefix,existing,include_env):
    archive,target,scratch=fixture(tmp_path,prefix,existing,include_env)
    before=snapshot(target)
    commands=tmp_path/'commands';commands.mkdir()
    program='''import os,subprocess,sys
from pathlib import Path
name=Path(sys.argv[0]).name
args=sys.argv[1:]
real=REAL[name]
dest=args[args.index('-C')+1] if name=='tar' and '-xzf' in args else args[-1] if name=='cp' else None
if dest and Path(dest).resolve().is_relative_to(Path(TARGET).resolve()):
    if name=='cp': subprocess.run([real,'-a',args[1],args[-1]],check=True)
    else: subprocess.run([real,*args,DB_MEMBER],check=True)
    print('synthetic destination write failure',file=sys.stderr)
    sys.exit(28)
os.execv(real,[real,*args])
'''
    for name in ['tar','cp']:
        p=commands/name
        p.write_text('#!'+sys.executable+'\nREAL='+repr({n:shutil.which(n) for n in ['tar','cp']})+'\nTARGET='+repr(str(target))+'\nDB_MEMBER='+repr(prefix+'practice.db')+'\n'+program)
        p.chmod(0o755)
    result=run(archive,target,scratch,commands)
    assert result.returncode!=0,result.stdout
    assert snapshot(target)==before,result.stderr
    assert not list(scratch.iterdir())
    assert run(archive,target,scratch).returncode==0
    check_good(target,include_env)

@pytest.mark.parametrize('prefix',['','data/'])
@pytest.mark.parametrize('boundary',['refuse','term_before','term_after'])
def test_data_publication_boundaries(tmp_path,prefix,boundary):
    archive,target,scratch=fixture(tmp_path,prefix)
    before=snapshot(target)
    commands=tmp_path/'commands';commands.mkdir()
    p=commands/'mv'
    p.write_text('#!'+sys.executable+'\nimport os,signal,subprocess,sys\n'
        +'boundary='+repr(boundary)+'\n'
        +"if boundary=='term_after': subprocess.run(["+repr(shutil.which('mv'))+",*sys.argv[1:]],check=True)\n"
        +"if boundary.startswith('term'): os.kill(os.getppid(),signal.SIGTERM)\n"
        +'sys.exit(1)\n')
    p.chmod(0o755)
    result=run(archive,target,scratch,commands)
    assert result.returncode!=0
    assert not list(scratch.iterdir())
    if boundary=='term_after':
        check_good(target)
        assert run(archive,target,scratch).returncode!=0
    else:
        assert snapshot(target)==before,result.stderr
        assert run(archive,target,scratch).returncode==0
        check_good(target)
