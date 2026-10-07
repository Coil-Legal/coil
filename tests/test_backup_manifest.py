"""Every backup names the code that made it and the schema it holds (#115).

A current backup restored under older code started healthy and showed $100.00 owed
instead of $90.00, because that code does not understand newer credit rows. The archive
manifest is what lets ops/restore.sh refuse that, and the startup warning is what catches
it when the restore went around the script.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile

import pytest
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'ops/backup.sh'


def fingerprint(schema):
    return hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def assert_recent(stamp):
    made = datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    assert abs(datetime.now(timezone.utc) - made) < timedelta(minutes=5)


@pytest.fixture(scope='module')
def seeded_db(tmp_path_factory):
    path = tmp_path_factory.mktemp('seeded') / 'practice.db'
    out = subprocess.run([sys.executable, str(ROOT / 'seed.py')], cwd=ROOT, capture_output=True, text=True,
                         env=dict(os.environ, DATABASE_URL=f'sqlite:///{path}'))
    assert out.returncode == 0, out.stderr
    return path


# --- CLI backup ----------------------------------------------------------------------

def test_cli_backup_writes_manifest_describing_the_snapshot(tmp_path, monkeypatch):
    from app import cli
    data = tmp_path / 'data'
    data.mkdir()
    source = data / 'practice.db'
    with sqlite3.connect(source) as db:
        db.execute('CREATE TABLE fixture (name TEXT, cents INTEGER)')
        db.execute('CREATE TABLE credit_rows (id INTEGER PRIMARY KEY, invoice_id INTEGER, cents INTEGER)')
        db.execute("INSERT INTO fixture VALUES ('QA-MANIFEST-20261006', 9000)")
    db.close()
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///' + str(source),
                      COIL_VERSION='qa-20261006', COIL_COMMIT='0123abc')
    monkeypatch.setattr(cli, 'DATA_DIR', str(data))
    with app.app_context():
        archive = cli.backup()
    with tarfile.open(archive) as tar:
        assert 'coil-backup.json' in tar.getnames(), 'the manifest belongs at the archive root'
        assert 'data/coil-backup.json' not in tar.getnames()
        manifest = json.load(tar.extractfile('coil-backup.json'))
    assert manifest['format'] == 1
    assert manifest['producer'] == 'cli'
    assert manifest['coil_version'] == 'qa-20261006'
    assert manifest['coil_commit'] == '0123abc'
    assert_recent(manifest['created_at'])
    assert manifest['schema'] == {'credit_rows': ['cents', 'id', 'invoice_id'], 'fixture': ['cents', 'name']}
    assert manifest['schema_fingerprint'] == fingerprint(manifest['schema'])
    assert not list((data / 'backups').glob('.coil-backup-job-*'))


def test_cli_manifest_schema_matches_a_real_coil_database(tmp_path, monkeypatch, seeded_db):
    from app import cli
    from app.backup_manifest import known_schema
    data = tmp_path / 'data'
    data.mkdir()
    (data / 'practice.db').write_bytes(seeded_db.read_bytes())
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + str(data / 'practice.db')
    monkeypatch.setattr(cli, 'DATA_DIR', str(data))
    with app.app_context():
        archive = cli.backup()
    with tarfile.open(archive) as tar:
        manifest = json.load(tar.extractfile('coil-backup.json'))
    # A bare Flask app has no COIL_VERSION, which is what a source checkout reports.
    assert (manifest['coil_version'], manifest['coil_commit']) == ('dev', 'unknown')
    assert manifest['schema'] == known_schema()
    assert not any(name.startswith('sqlite_') for name in manifest['schema'])


def test_known_schema_command_prints_the_models_without_building_the_app(tmp_path):
    from app.backup_manifest import known_schema
    install = tmp_path / 'install'
    install.mkdir()
    (install / 'app').symlink_to(ROOT / 'app', target_is_directory=True)
    out = subprocess.run([sys.executable, '-m', 'app.cli', 'known_schema'], cwd=install, capture_output=True,
                         text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1',
                                             COIL_VERSION='qa-20261006', COIL_COMMIT='0123abc'))
    assert out.returncode == 0, out.stderr
    printed = json.loads(out.stdout)
    assert printed['schema'] == known_schema()
    assert (printed['coil_version'], printed['coil_commit']) == ('qa-20261006', '0123abc')
    # ops/restore.sh runs this inside the restore target before writing anything there.
    assert sorted(p.name for p in install.iterdir()) == ['app']


# --- nightly host backup -------------------------------------------------------------

def nightly(tmp_path, manifest=True):
    """Run ops/backup.sh with a docker stub that runs the real snapshot code on the host."""
    firm = tmp_path / 'apps/synthetic.coil.test'
    data = firm / 'data'
    data.mkdir(parents=True)
    with sqlite3.connect(data / 'practice.db') as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('CREATE TABLE invoices (id INTEGER PRIMARY KEY, total_cents INTEGER)')
        db.execute('CREATE TABLE credit_rows (id INTEGER PRIMARY KEY, invoice_id INTEGER, cents INTEGER)')
        db.execute('INSERT INTO invoices VALUES (1, 10000)')
        db.execute('INSERT INTO credit_rows VALUES (1, 1, 1000)')
    db.close()
    commands = tmp_path / 'commands'
    commands.mkdir()
    stubs = {
        # Like `docker exec`: the container's environment carries COIL_VERSION/COIL_COMMIT.
        'docker': '''
if sys.argv[1] == 'compose':
    print('synthetic-container')
else:
    args = sys.argv[sys.argv.index('-c') + 1:]
    sys.argv = ['-c'] + [arg.replace('/app/data', os.environ['FIXTURE_DATA']) for arg in args[1:]]
    os.environ.update(COIL_VERSION='qa-nightly-20261006', COIL_COMMIT='feedbee')
    exec(args[0].replace('/app/data', os.environ['FIXTURE_DATA']))
    if os.environ['DROP_MANIFEST'] == '1':
        (pathlib.Path(sys.argv[1]).parent / 'coil-backup.json').unlink()
''',
        # GNU tar's -C and --transform, which the host script relies on and bsdtar lacks.
        'tar': '''
args = sys.argv[1:]
out = args[args.index('-czf') + 1]
cwd, i = None, args.index('-czf') + 2
with tarfile.open(out, 'w:gz') as arc:
    while i < len(args):
        if args[i] == '-C':
            cwd, i = args[i + 1], i + 2
        elif args[i] == '--transform':
            i += 2
        else:
            name = args[i]
            arcname = 'practice.db' if name.startswith('.backup-snapshot.') else name
            arc.add(pathlib.Path(cwd, name), arcname=arcname)
            i += 1
''',
        'rclone': 'pass',
    }
    for name, body in stubs.items():
        path = commands / name
        path.write_text('#!' + sys.executable + '\nimport os, pathlib, sys, tarfile\n' + body)
        path.chmod(0o700)
    env = dict(os.environ, PATH=str(commands) + ':' + os.environ['PATH'],
               COIL_APPS_DIR=str(tmp_path / 'apps'), COIL_BACKUP_ROOT=str(tmp_path / 'backups'),
               COIL_BACKUP_REMOTE='synthetic:no-network', FIXTURE_DATA=str(data),
               DROP_MANIFEST='0' if manifest else '1')
    env.pop('COIL_VERSION', None)
    env.pop('COIL_COMMIT', None)
    result = subprocess.run(['bash', str(SCRIPT)], env=env, text=True, capture_output=True, timeout=30)
    return result, sorted((tmp_path / 'backups').glob('*/*.tar.gz')), data


def test_nightly_archive_carries_manifest_from_container_and_snapshot(tmp_path):
    result, archives, data = nightly(tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(archives) == 1
    with tarfile.open(archives[0]) as tar:
        assert sorted(tar.getnames()) == ['coil-backup.json', 'practice.db']
        manifest = json.load(tar.extractfile('coil-backup.json'))
        snapshot = tmp_path / 'snapshot.db'
        snapshot.write_bytes(tar.extractfile('practice.db').read())
    assert manifest['format'] == 1
    assert manifest['producer'] == 'nightly'
    assert manifest['coil_version'] == 'qa-nightly-20261006'
    assert manifest['coil_commit'] == 'feedbee'
    assert_recent(manifest['created_at'])
    expected = {'credit_rows': ['cents', 'id', 'invoice_id'], 'invoices': ['id', 'total_cents']}
    assert manifest['schema'] == expected
    assert manifest['schema_fingerprint'] == fingerprint(expected)
    # The nightly definition must agree with the app's, or restore would misread it.
    from app.backup_manifest import build_manifest
    assert build_manifest(snapshot, 'nightly', 'x', 'y')['schema_fingerprint'] == manifest['schema_fingerprint']
    assert not list(data.glob('.coil-nightly-job-*'))


def test_nightly_without_manifest_is_a_failure_not_a_bare_archive(tmp_path):
    result, archives, data = nightly(tmp_path, manifest=False)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'manifest missing or unreadable' in result.stdout
    assert '1 failure(s)' in result.stdout
    assert archives == []
    assert not list((tmp_path / 'backups').glob('*/.*partial*'))
    assert not list(data.glob('.coil-nightly-job-*'))


# --- startup warning -----------------------------------------------------------------

def start(db_path, caplog):
    from app import create_app
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger='schema'):
        create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}'})
    return [r.getMessage() for r in caplog.records if r.name == 'schema' and r.levelno >= logging.WARNING]


def test_no_startup_warning_for_a_normal_seeded_database(tmp_path, caplog, seeded_db):
    db_path = tmp_path / 'practice.db'
    db_path.write_bytes(seeded_db.read_bytes())
    assert start(db_path, caplog) == []


def test_startup_warns_about_tables_and_columns_from_newer_code(tmp_path, caplog, seeded_db):
    db_path = tmp_path / 'practice.db'
    db_path.write_bytes(seeded_db.read_bytes())
    with sqlite3.connect(db_path) as db:
        db.execute('ALTER TABLE invoices ADD COLUMN newer_credit_kind TEXT')
        for n in range(12):
            db.execute(f'ALTER TABLE payments ADD COLUMN zz_newer_{n:02d} TEXT')
        db.execute('CREATE TABLE credit_allocations_newer (id INTEGER PRIMARY KEY)')
    db.close()
    warnings = start(db_path, caplog)
    assert len(warnings) == 1, warnings
    message = warnings[0]
    assert 'newer Coil version' in message
    assert 'credit_allocations_newer' in message
    assert 'invoices.newer_credit_kind' in message
    assert 'and 5 more' in message, 'a long list must be cut short'
    assert '—' not in message


def test_startup_check_never_stops_the_app(tmp_path, caplog, monkeypatch):
    from app import backup_manifest

    def broken(conn):
        raise RuntimeError('synthetic schema read failure')

    monkeypatch.setattr(backup_manifest, 'database_schema', broken)
    assert start(tmp_path / 'practice.db', caplog) == []
