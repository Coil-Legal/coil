"""Overlapping backup jobs must retain their own SQLite snapshot."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import time

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/backup.sh'


@pytest.mark.parametrize('fail_second', [False, True])
def test_overlapping_jobs_preserve_each_snapshot(tmp_path, fail_second):
    firm = tmp_path / 'apps/synthetic.coil.test'
    data = firm / 'data'
    data.mkdir(parents=True)
    source = data / 'practice.db'
    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE fixture (id TEXT, cents INTEGER)')
        db.execute('INSERT INTO fixture VALUES (?, ?)', ('QA-BACKUP-OVERLAP-20260926', 100))
    commands = tmp_path / 'commands'
    commands.mkdir()
    stubs = {
        'docker': '''
if sys.argv[1] == 'compose':
    print('synthetic-container')
else:
    args = sys.argv[sys.argv.index('-c') + 1:]
    code = args[0].replace('/app/data', os.environ['FIXTURE_DATA'])
    sys.argv = ['-c'] + [arg.replace('/app/data', os.environ['FIXTURE_DATA']) for arg in args[1:]]
    if os.environ.get('COIL_PROBE_IMAGE'):
        subprocess.run([os.environ['COIL_PROBE_DOCKER_BIN'], 'run', '--rm', '--network', 'none',
                        '-v', os.environ['FIXTURE_DATA'] + ':/app/data', '--entrypoint', 'python',
                        os.environ['COIL_PROBE_IMAGE'], '-c', args[0], *args[1:]],
                       check=True, capture_output=True)
    else:
        exec(code)
    if os.environ['JOB'] == 'first':
        pathlib.Path(os.environ['READY']).touch()
        deadline = time.monotonic() + 20
        while not pathlib.Path(os.environ['RELEASE']).exists():
            if time.monotonic() > deadline: sys.exit(8)
            time.sleep(.02)
    elif os.environ['FAIL_SECOND'] == '1':
        sys.exit(7)
''',
        'rclone': 'pass',
    }
    # Linux acceptance sets this to use the actual production archive utility.
    if not os.environ.get('COIL_PROBE_REAL_TAR'):
        stubs['tar'] = '''
args = sys.argv
member = args[args.index('--transform') + 2]
with tarfile.open(args[args.index('-czf') + 1], 'w:gz') as out:
    out.add(pathlib.Path(args[args.index('-C') + 1], member), arcname='practice.db')
'''
    for name, body in stubs.items():
        path = commands / name
        path.write_text('#!' + sys.executable + '\nimport os, pathlib, sys, time, tarfile, subprocess\n' + body)
        path.chmod(0o700)
    ready, release = tmp_path / 'ready', tmp_path / 'release'
    env = dict(os.environ, PATH=str(commands) + ':' + os.environ['PATH'],
               COIL_APPS_DIR=str(tmp_path / 'apps'), COIL_BACKUP_ROOT=str(tmp_path / 'backups'),
               COIL_BACKUP_REMOTE='synthetic:no-network', FIXTURE_DATA=str(data),
               READY=str(ready), RELEASE=str(release), JOB='first', FAIL_SECOND=str(int(fail_second)))
    first = subprocess.Popen(['bash', str(SCRIPT)], env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.monotonic() + 10
        while not ready.exists():
            assert first.poll() is None, first.communicate()
            assert time.monotonic() < deadline, 'first snapshot did not reach barrier'
            time.sleep(.02)
        with sqlite3.connect(source) as db:
            db.execute('UPDATE fixture SET cents=200')
        second = subprocess.run(['bash', str(SCRIPT)], env=dict(env, JOB='second'),
                                text=True, capture_output=True, timeout=10)
        assert (second.returncode != 0) == fail_second, second.stdout + second.stderr
        release.touch()
        out, err = first.communicate(timeout=10)
        assert first.returncode == 0, out + err
    finally:
        release.touch()
        if first.poll() is None:
            first.kill()
            first.communicate()
    archives = list((tmp_path / 'backups').glob('*/*.tar.gz'))
    assert len(archives) == (1 if fail_second else 2)
    amounts = []
    for index, path in enumerate(archives):
        with tarfile.open(path) as archive:
            # The stub tar copies only the database; real GNU tar also carries the manifest (#115).
            assert [n for n in archive.getnames() if n != 'coil-backup.json'] == ['practice.db']
            restored = tmp_path / f'restored-{index}.db'
            restored.write_bytes(archive.extractfile('practice.db').read())
        with sqlite3.connect(restored) as db:
            assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
            marker, cents = db.execute('SELECT id, cents FROM fixture').fetchone()
            assert marker == 'QA-BACKUP-OVERLAP-20260926'
            amounts.append(cents)
    assert sorted(amounts) == ([100] if fail_second else [100, 200])
    assert not list(data.glob('.backup-snapshot*'))
    assert not list((tmp_path / 'backups').glob('*/.*partial*'))
