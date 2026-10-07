"""A failed or repeated backup must not replace an existing good archive."""
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/backup.sh'


def run_backup(tmp_path, mode, real_tar=False):
    firm = tmp_path / 'apps/synthetic.coil.test'
    (firm / 'data').mkdir(parents=True, exist_ok=True)
    (firm / 'data/practice.db').write_bytes(b'synthetic source')
    commands = tmp_path / 'commands'
    commands.mkdir(exist_ok=True)
    stubs = {
        'date': "print('20260926T200000Z' if '+%Y%m%dT%H%M%SZ' in sys.argv else '6')",
        # The container also writes the archive manifest beside its snapshot (#115).
        'docker': """
if sys.argv[1] == 'compose': print('synthetic-container')
else:
    import hashlib, json
    snap = pathlib.Path(sys.argv[-1].replace('/app/data', os.environ['FIXTURE_FIRM'] + '/data'))
    snap.write_bytes(b'snapshot')
    schema = {'fixture': ['cents']}
    canonical = json.dumps(schema, sort_keys=True, separators=(',', ':'))
    (snap.parent / 'coil-backup.json').write_text(json.dumps({
        'format': 1, 'producer': 'nightly', 'coil_version': 'dev', 'coil_commit': 'unknown',
        'created_at': '2026-09-26T20:00:00Z', 'schema': schema,
        'schema_fingerprint': hashlib.sha256(canonical.encode()).hexdigest()}))""",
        'tar': "\np=pathlib.Path(sys.argv[sys.argv.index('-czf')+1]); p.write_bytes(b'partial' if os.environ['FAIL_ARCHIVE']=='1' else b'complete synthetic archive'); sys.exit(int(os.environ['FAIL_ARCHIVE']))",
        'rclone': "\nwith open(os.environ['FIXTURE_CALLS'],'a') as f: f.write(sys.argv[1]+'\\n')",
    }
    if real_tar:
        stubs.pop('tar')
    for name, body in stubs.items():
        p = commands / name
        p.write_text('#!' + sys.executable + '\nimport sys, os, pathlib\n' + body + '\n')
        p.chmod(0o700)
    env = dict(os.environ, PATH=str(commands) + ':' + os.environ['PATH'],
               COIL_APPS_DIR=str(tmp_path / 'apps'), COIL_BACKUP_ROOT=str(tmp_path / 'backups'),
               COIL_BACKUP_REMOTE='synthetic:no-network', FIXTURE_FIRM=str(firm),
               FIXTURE_CALLS=str(tmp_path / 'calls'), FAIL_ARCHIVE=mode)
    return subprocess.run(['bash', str(SCRIPT)], env=env, text=True, capture_output=True)


def test_failed_retry_preserves_previous_good_archive(tmp_path):
    first = run_backup(tmp_path, '0')
    assert first.returncode == 0, first.stderr
    archives = list((tmp_path / 'backups').glob('*/*.tar.gz'))
    assert len(archives) == 1
    original = archives[0].read_bytes()
    calls = (tmp_path / 'calls').read_bytes()
    failed = run_backup(tmp_path, '1')
    assert failed.returncode != 0
    assert archives[0].exists(), 'failed retry deleted the successful archive'
    assert archives[0].read_bytes() == original
    assert (tmp_path / 'calls').read_bytes() == calls, 'failed archive reached offsite copy'
    assert list((tmp_path / 'backups').glob('*/*.tar.gz')) == archives


def test_two_successes_with_same_timestamp_get_distinct_archives(tmp_path):
    for _ in range(2):
        result = run_backup(tmp_path, '0')
        assert result.returncode == 0, result.stderr
    archives = list((tmp_path / 'backups').glob('*/*.tar.gz'))
    assert len(archives) == 2
    assert all(p.read_bytes() == b'complete synthetic archive' for p in archives)


def test_archive_without_optional_environment_on_gnu_tar(tmp_path):
    version = subprocess.run(['tar', '--version'], capture_output=True, text=True)
    if 'GNU tar' not in version.stdout:
        pytest.skip('host backup requires GNU tar; also covered by Linux acceptance probe')
    result = run_backup(tmp_path, '0', real_tar=True)
    assert result.returncode == 0, result.stdout + result.stderr
    archives = list((tmp_path / 'backups').glob('*/*.tar.gz'))
    assert len(archives) == 1
    with tarfile.open(archives[0]) as archive:
        assert archive.getnames() == ['practice.db', 'coil-backup.json']
        assert archive.extractfile('practice.db').read() == b'snapshot'
