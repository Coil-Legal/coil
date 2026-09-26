"""Handled SQLite snapshot failure must not leave journal files filling the source disk."""
import os
from pathlib import Path
import subprocess
import sys

SCRIPT=Path(__file__).resolve().parents[1]/'ops/backup.sh'


def test_failed_snapshot_removes_only_its_own_database_and_sidecars(tmp_path):
    data=tmp_path/'apps/synthetic.coil.test/data'
    data.mkdir(parents=True)
    (data/'practice.db').write_bytes(b'synthetic source unchanged')
    protected=data/'.backup-snapshot.other-journal'
    protected.write_bytes(b'another active job')
    commands=tmp_path/'commands';commands.mkdir()
    docker=commands/'docker'
    docker.write_text('#!'+sys.executable+'''
import os, pathlib, sys
if sys.argv[1]=='compose': print('synthetic-container')
else:
    snap=pathlib.Path(os.environ['FIXTURE_DATA'])/pathlib.Path(sys.argv[-1]).name
    snap.write_bytes(b'partial snapshot')
    for suffix in ('-journal','-wal','-shm'):
        pathlib.Path(str(snap)+suffix).write_bytes(b'synthetic SQLite sidecar')
    sys.exit(1)
''')
    docker.chmod(0o700)
    env=dict(os.environ,PATH=str(commands)+':'+os.environ['PATH'],FIXTURE_DATA=str(data),
             COIL_APPS_DIR=str(tmp_path/'apps'),COIL_BACKUP_ROOT=str(tmp_path/'backups'),
             COIL_BACKUP_REMOTE='synthetic:no-network')
    result=subprocess.run(['bash',str(SCRIPT)],env=env,text=True,capture_output=True,timeout=10)
    assert result.returncode==1,result.stdout+result.stderr
    assert 'snapshot failed' in result.stdout
    assert (data/'practice.db').read_bytes()==b'synthetic source unchanged'
    assert protected.read_bytes()==b'another active job'
    assert list(data.glob('.backup-snapshot*'))==[protected]
    assert not list((tmp_path/'backups').glob('*/*.tar.gz'))
