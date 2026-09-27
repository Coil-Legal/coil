"""Real process-lifetime tests with SQLite and synthetic command transports."""
import hashlib
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tarfile
import time

import pytest

SCRIPT = Path(os.getenv('NIGHTLY_REVIEW_SCRIPT', Path(__file__).resolve().parents[1] / 'ops/backup.sh'))


def wait(path):
    end = time.monotonic() + 15
    while not path.exists():
        assert time.monotonic() < end, f'barrier missing: {path}'
        time.sleep(.02)


class Lab:
    def __init__(self, root):
        self.root = root
        self.data = root / 'apps/synthetic.test/data'
        (self.data / 'uploads').mkdir(parents=True)
        (self.data / 'uploads/control').write_bytes(b'synthetic upload')
        with sqlite3.connect(self.data / 'practice.db') as db:
            db.execute('CREATE TABLE fixture(cents INTEGER)')
            db.execute('INSERT INTO fixture VALUES (100)')
        commands = root / 'commands'
        commands.mkdir()
        preamble = '#!' + sys.executable + '''
import os,sys,pathlib,subprocess,time,tarfile
root=pathlib.Path(os.environ['LAB'])

def barrier():
    (root/'ready').touch()
    while not (root/'release').exists(): time.sleep(.02)
'''
        programs = {
            'docker': '''
if sys.argv[1]=='compose': print('fixture-container')
else:
    code=sys.argv[sys.argv.index('-c')+1].replace('/app/data',os.environ['DATA'])
    target=sys.argv[-1].replace('/app/data',os.environ['DATA'])
    # Like Docker exec, this process is not in the host launcher's process group.
    stage=os.environ.get('STAGE')
    prefix="import pathlib,time,os; root=pathlib.Path(os.environ['LAB'])\\n"
    barrier_code="(root/'ready').touch()\\nwhile not (root/'release').exists(): time.sleep(.02)\\n"
    code=prefix+(barrier_code if stage=='delayed_child' else '')+code
    if stage=='active_child': code+='\\n'+barrier_code
    code+="\\n(root/'child-finished').touch()\\n"
    code=prefix+"try:\\n    exec("+repr(code)+")\\nexcept BaseException as error:\\n    (root/'child-error').write_text(type(error).__name__)\\n    raise\\n"
    child=subprocess.Popen([sys.executable,'-c',code,target],start_new_session=True)
    (root/'child-pid').write_text(str(child.pid))
    sys.exit(child.wait())
''',
            'tar': '''
if os.environ.get('STAGE')=='before_tar': barrier()
args=sys.argv
with tarfile.open(args[args.index('-czf')+1],'w:gz') as arc:
    source=pathlib.Path(args[args.index('-C')+1],args[args.index('--transform')+2])
    arc.add(source,arcname='practice.db')
    arc.add(pathlib.Path(os.environ['DATA'])/'uploads',arcname='uploads')
if os.environ.get('STAGE')=='after_tar': barrier()
''',
            'ln': '''
os.link(sys.argv[1],sys.argv[2])
if os.environ.get('STAGE')=='after_publish': barrier()
''',
            'rclone': 'pass\n',
        }
        for name, body in programs.items():
            p = commands / name
            p.write_text(preamble + body)
            p.chmod(0o700)
        self.env = dict(os.environ, PATH=str(commands) + ':' + os.environ['PATH'], LAB=str(root),
                        DATA=str(self.data), COIL_APPS_DIR=str(root / 'apps'),
                        COIL_BACKUP_ROOT=str(root / 'backups'), COIL_BACKUP_REMOTE='synthetic:no-network',
                        COIL_KEEP_DAILY='100')

    def amount(self, cents):
        with sqlite3.connect(self.data / 'practice.db') as db:
            db.execute('UPDATE fixture SET cents=?', (cents,))

    def start(self, stage=''):
        return subprocess.Popen(['bash', str(SCRIPT)], env=dict(self.env, STAGE=stage),
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)

    def run(self):
        job = self.start()
        assert job.wait(timeout=15) == 0

    def archives(self):
        return sorted((self.root / 'backups').glob('*/*.tar.gz'))

    def inspect(self):
        values = []
        for i, p in enumerate(self.archives()):
            assert p.stat().st_mode & 0o777 == 0o600
            with tarfile.open(p) as arc:
                restored = self.root / f'restored-{i}.db'
                restored.write_bytes(arc.extractfile('practice.db').read())
                assert arc.extractfile('uploads/control').read() == b'synthetic upload'
            with sqlite3.connect(restored) as db:
                assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
                values.append(db.execute('SELECT cents FROM fixture').fetchone()[0])
        return sorted(values)

    def leftovers(self):
        return (list(self.data.glob('.coil-nightly-job-*')) + list(self.data.glob('.backup-snapshot.*'))
                + list((self.root / 'backups').glob('*/.*partial*')))


@pytest.mark.parametrize('stage', ['before_tar', 'after_tar', 'after_publish'])
@pytest.mark.parametrize('kill', [True, False])
def test_killed_jobs_reclaimed_live_jobs_preserved(tmp_path, stage, kill):
    lab = Lab(tmp_path)
    lab.run()
    prior = lab.archives()[0]
    digest = hashlib.sha256(prior.read_bytes()).hexdigest()
    lab.amount(200)
    job = lab.start(stage)
    try:
        wait(tmp_path / 'ready')
        if kill:
            os.killpg(job.pid, signal.SIGKILL)
            assert job.wait(timeout=5) == -9
        lab.amount(300)
        lab.run()
        if kill:
            assert not lab.leftovers(), 'abandoned job remains after retry'
        else:
            assert lab.leftovers(), 'active workspace removed'
            (tmp_path / 'release').touch()
            assert job.wait(timeout=10) == 0
        assert lab.inspect() == ([100, 300] if kill and stage != 'after_publish' else [100, 200, 300])
        assert not lab.leftovers()
        assert hashlib.sha256(prior.read_bytes()).hexdigest() == digest
    finally:
        (tmp_path / 'release').touch()
        if job.poll() is None:
            os.killpg(job.pid, signal.SIGKILL)
            job.wait()


@pytest.mark.parametrize('stage', ['active_child', 'delayed_child'])
def test_detached_child_lease_and_delayed_start(tmp_path, stage):
    lab = Lab(tmp_path)
    lab.run()
    (tmp_path / 'child-finished').unlink()
    lab.amount(200)
    job = lab.start(stage)
    try:
        wait(tmp_path / 'ready')
        child = int((tmp_path / 'child-pid').read_text())
        os.killpg(job.pid, signal.SIGKILL)
        job.wait(timeout=5)
        lab.amount(300)
        lab.run()
        if stage == 'active_child':
            assert lab.leftovers(), 'detached child lost its active workspace'
        else:
            assert not lab.leftovers(), 'delayed child has no lease and must be reclaimed'
        # Retry's child also writes this marker; remove it before release.
        (tmp_path / 'child-finished').unlink()
        (tmp_path / 'release').touch()
        if stage == 'active_child':
            wait(tmp_path / 'child-finished')
        else:
            # Child fails closed when the existing workspace lease is missing.
            wait(tmp_path / 'child-error')
            assert (tmp_path / 'child-error').read_text() == 'FileNotFoundError'
            assert not (tmp_path / 'child-finished').exists()
        lab.amount(400)
        lab.run()
        assert lab.inspect() == [100, 300, 400]
        assert not lab.leftovers()
    finally:
        (tmp_path / 'release').touch()
        if job.poll() is None:
            os.killpg(job.pid, signal.SIGKILL)
            job.wait()
        if 'child' in locals():
            try: os.kill(child, signal.SIGKILL)
            except ProcessLookupError: pass


def test_incomplete_initialization_legacy_and_symlink(tmp_path):
    lab = Lab(tmp_path)
    (lab.data / '.coil-nightly-job-incomplete').mkdir()
    legacy = lab.data / '.backup-snapshot.legacy'
    legacy.write_bytes(b'unowned legacy')
    external = tmp_path / 'external'
    external.mkdir()
    (external / 'keep').write_bytes(b'not ours')
    (lab.data / '.coil-nightly-job-symlink').symlink_to(external, target_is_directory=True)
    lab.run()
    assert not (lab.data / '.coil-nightly-job-incomplete').exists()
    assert legacy.read_bytes() == b'unowned legacy'
    assert (external / 'keep').read_bytes() == b'not ours'
    assert lab.inspect() == [100]
