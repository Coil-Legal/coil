"""ops/restore.sh must refuse to put a backup under code older than the code that made it (#115).

Codex restored a current backup under commit e007fa9. It started healthy and reported
$100.00 owed instead of $90.00, because that code does not understand newer credit rows.
"Older" means the backup's database holds a table or column the target code does not
know; version names like demo-20261006 do not sort, so they are only shown.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'ops/restore.sh'


@pytest.fixture(scope='module')
def seeded_db(tmp_path_factory):
    path = tmp_path_factory.mktemp('seeded') / 'practice.db'
    out = subprocess.run([sys.executable, str(ROOT / 'seed.py')], cwd=ROOT, capture_output=True, text=True,
                         env=dict(os.environ, DATABASE_URL=f'sqlite:///{path}'))
    assert out.returncode == 0, out.stderr
    return path


@pytest.fixture
def lab(tmp_path):
    """PATH whose python3 can import the app, and a private TMPDIR to prove cleanup."""
    commands = tmp_path / 'commands'
    commands.mkdir()
    wrapper = commands / 'python3'
    wrapper.write_text(f'#!/bin/sh\nexec {sys.executable} "$@"\n')
    wrapper.chmod(0o755)
    scratch = tmp_path / 'scratch'
    scratch.mkdir()
    env = dict(os.environ, PATH=f'{commands}:{os.environ["PATH"]}', TMPDIR=str(scratch))
    for name in ('COIL_VERSION', 'COIL_COMMIT', 'DATABASE_URL'):
        env.pop(name, None)
    return {'root': tmp_path, 'commands': commands, 'scratch': scratch, 'env': env}


def database(tmp_path, seeded_db, newer=False, name='practice.db'):
    path = tmp_path / name
    path.write_bytes(seeded_db.read_bytes())
    if newer:
        with sqlite3.connect(path) as db:
            # The real case: newer code keeps credit rows the older code would not subtract.
            db.execute('ALTER TABLE invoices ADD COLUMN newer_credit_kind TEXT')
            for n in range(9):
                db.execute(f'ALTER TABLE invoices ADD COLUMN zz_newer_{n} TEXT')
            db.execute('CREATE TABLE credit_allocations_newer (id INTEGER PRIMARY KEY, cents INTEGER)')
        db.close()
    return path


def manifest_for(db_path, producer, version):
    """Built here rather than through app.backup_manifest, so the test also pins the format."""
    with sqlite3.connect(db_path) as db:
        rows = db.execute("SELECT m.name, p.name FROM sqlite_master m, pragma_table_info(m.name) p "
                          "WHERE m.type = 'table' AND m.name NOT LIKE 'sqlite%'").fetchall()
    db.close()
    schema = {}
    for table, column in rows:
        schema.setdefault(table, []).append(column)
    schema = {table: sorted(columns) for table, columns in schema.items()}
    canonical = json.dumps(schema, sort_keys=True, separators=(',', ':'))
    return {'format': 1, 'coil_version': version, 'coil_commit': 'c0ffee1', 'created_at': '2026-10-06T17:00:00Z',
            'producer': producer, 'schema': schema,
            'schema_fingerprint': hashlib.sha256(canonical.encode()).hexdigest()}


def archive(tmp_path, db_path, manifest=True, layout='cli', version='qa-new-20261006'):
    path = tmp_path / f'backup-{layout}-{int(manifest)}.tar.gz'
    prefix = 'data/' if layout == 'cli' else ''
    with tarfile.open(path, 'w:gz') as tar:
        if manifest:
            data = json.dumps(manifest_for(db_path, layout, version)).encode()
            item = tarfile.TarInfo('coil-backup.json')
            item.size = len(data)
            tar.addfile(item, io.BytesIO(data))
        tar.add(db_path, arcname=prefix + 'practice.db')
        upload = b'synthetic upload'
        item = tarfile.TarInfo(prefix + 'uploads/1/evidence.txt')
        item.size = len(upload)
        tar.addfile(item, io.BytesIO(upload))
    return path


def install_with_code(lab, broken=False):
    target = lab['root'] / 'install'
    target.mkdir()
    if broken:
        # Code is there, but nothing can import it: the check must fail closed.
        (target / 'app').mkdir()
        (target / 'app/__init__.py').write_text('raise ImportError("synthetic broken checkout")\n')
        (target / 'app/models.py').write_text('')
    else:
        (target / 'app').symlink_to(ROOT / 'app', target_is_directory=True)
    return target


def listing(target):
    return sorted(str(p.relative_to(target)) for p in target.iterdir())


def restore(lab, *args):
    return subprocess.run(['bash', str(SCRIPT), *map(str, args)], env=lab['env'], capture_output=True,
                          text=True, timeout=120)


def restored_ok(target):
    with sqlite3.connect(target / 'data/practice.db') as db:
        assert db.execute('PRAGMA integrity_check').fetchone() == ('ok',)
        assert db.execute('SELECT count(*) FROM matters').fetchone()[0] > 0
    db.close()
    assert (target / 'data/uploads/1/evidence.txt').read_bytes() == b'synthetic upload'
    assert not (target / 'coil-backup.json').exists(), 'the manifest is not part of the install'
    assert not (target / 'data/coil-backup.json').exists()


@pytest.mark.parametrize('layout', ['cli', 'nightly'])
def test_same_schema_code_restores_and_prints_the_manifest(lab, seeded_db, layout):
    target = install_with_code(lab)
    path = archive(lab['root'], database(lab['root'], seeded_db), layout=layout)
    out = restore(lab, path, target)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'Coil version: qa-new-20261006' in out.stdout
    assert 'commit:       c0ffee1' in out.stdout
    assert 'created:' in out.stdout
    assert ('the Coil backup command' if layout == 'cli' else 'the nightly host backup') in out.stdout
    assert 'Version check passed' in out.stdout
    assert 'WARNING' not in out.stderr
    restored_ok(target)
    assert not list(lab['scratch'].iterdir())


@pytest.mark.parametrize('layout', ['cli', 'nightly'])
def test_backup_from_newer_code_is_refused_before_touching_the_target(lab, seeded_db, layout):
    target = install_with_code(lab)
    before = listing(target)
    path = archive(lab['root'], database(lab['root'], seeded_db, newer=True), layout=layout)
    out = restore(lab, path, target)
    assert out.returncode != 0
    assert 'refusing: this backup came from newer Coil code' in out.stderr
    assert 'Coil qa-new-20261006 (commit c0ffee1)' in out.stderr
    assert 'target: Coil dev (commit unknown)' in out.stderr
    assert 'credit_allocations_newer' in out.stderr
    assert 'invoices.newer_credit_kind' in out.stderr
    assert 'and 2 more' in out.stderr, 'a long column list must be cut short'
    assert 'Restore with Coil qa-new-20261006 or newer' in out.stderr
    assert '--allow-downgrade' in out.stderr
    assert '—' not in out.stderr
    assert listing(target) == before, 'nothing may be written into the target'
    assert not list(lab['scratch'].iterdir())


@pytest.mark.parametrize('position', ['first', 'last'])
def test_allow_downgrade_restores_with_a_loud_warning(lab, seeded_db, position):
    target = install_with_code(lab)
    path = archive(lab['root'], database(lab['root'], seeded_db, newer=True))
    args = ['--allow-downgrade', path, target] if position == 'first' else [path, target, '--allow-downgrade']
    out = restore(lab, *args)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'WARNING: --allow-downgrade given' in out.stderr
    assert 'invoices.newer_credit_kind' in out.stderr
    assert 'restored into' in out.stdout
    restored_ok(target)


def test_unknown_option_is_a_usage_error(lab, seeded_db):
    path = archive(lab['root'], database(lab['root'], seeded_db))
    out = restore(lab, '--allow-downgrad', path, lab['root'] / 'install')
    assert out.returncode == 2
    assert 'usage:' in out.stdout
    assert not (lab['root'] / 'install').exists()


@pytest.mark.parametrize('with_code', [False, True])
def test_backup_without_manifest_still_restores_with_a_warning(lab, seeded_db, with_code):
    target = install_with_code(lab) if with_code else lab['root'] / 'install'
    path = archive(lab['root'], database(lab['root'], seeded_db), manifest=False, layout='nightly')
    out = restore(lab, path, target)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'no coil-backup.json manifest' in out.stderr
    assert 'cannot be checked' in out.stderr
    if with_code:
        assert 'Version check passed' in out.stdout
    else:
        assert 'holds no Coil code yet' in out.stdout
    restored_ok(target)


def test_no_code_in_target_prints_manifest_and_skips_the_check(lab, seeded_db):
    target = lab['root'] / 'install'
    path = archive(lab['root'], database(lab['root'], seeded_db, newer=True))
    out = restore(lab, path, target)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'Coil version: qa-new-20261006' in out.stdout
    assert 'Version check skipped' in out.stdout
    assert 'use Coil qa-new-20261006 or newer' in out.stdout


def test_code_whose_schema_cannot_be_read_is_refused_without_the_flag(lab, seeded_db):
    target = install_with_code(lab, broken=True)
    before = listing(target)
    path = archive(lab['root'], database(lab['root'], seeded_db))
    out = restore(lab, path, target)
    assert out.returncode != 0
    assert 'holds Coil code, but the tables and columns that code knows could not be read' in out.stderr
    assert 'synthetic broken checkout' in out.stderr
    assert '--allow-downgrade' in out.stderr
    assert listing(target) == before
    assert not list((target / 'app').glob('__pycache__')), 'the check must not write bytecode into the target'
    assert not list(lab['scratch'].iterdir())

    out = restore(lab, path, target, '--allow-downgrade')
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'was NOT checked' in out.stderr
    restored_ok(target)


def test_code_older_than_the_check_itself_is_refused(lab, seeded_db):
    """Commit e007fa9 and everything before #115 has no known_schema command at all."""
    target = lab['root'] / 'install'
    (target / 'app').mkdir(parents=True)
    (target / 'app/__init__.py').write_text('')
    (target / 'app/models.py').write_text('')
    # What the old app/cli.py main() does with a command it does not have.
    (target / 'app/cli.py').write_text('import sys\nprint("unknown command: known_schema")\n'
                                       'print("usage: python -m app.cli <command>")\nsys.exit(2)\n')
    before = listing(target)
    path = archive(lab['root'], database(lab['root'], seeded_db))
    out = restore(lab, path, target)
    assert out.returncode != 0
    assert 'has no known_schema command, so it predates this check' in out.stderr
    assert 'put Coil qa-new-20261006 or newer there' in out.stderr
    assert listing(target) == before


def compose_install(lab):
    """A target holding only a compose file, answered by a docker stub that runs the app's CLI."""
    target = lab['root'] / 'install'
    target.mkdir()
    (target / 'docker-compose.yml').write_text('services:\n  web:\n    image: synthetic\n')
    docker = lab['commands'] / 'docker'
    docker.write_text('#!' + sys.executable + f'''
import os, pathlib, subprocess, sys
args = sys.argv[1:]
with open({str(lab['root'] / 'docker-calls')!r}, 'a') as f:
    f.write(' '.join(args) + '\\n')
if args[:3] == ['compose', 'config', '--services']:
    print('web')
elif args[:2] == ['compose', 'run']:
    # Docker creates a missing bind-mount source on the host.
    pathlib.Path('data').mkdir(exist_ok=True)
    print('Creating network synthetic_default')
    sys.exit(subprocess.run([{sys.executable!r}, *args[args.index('web') + 2:]], cwd={str(ROOT)!r},
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', COIL_VERSION='qa-old-20261001',
                                     COIL_COMMIT='e007fa9')).returncode)
else:
    sys.exit(1)
''')
    docker.chmod(0o755)
    return target


def test_compose_target_is_checked_through_docker(lab, seeded_db):
    target = compose_install(lab)
    path = archive(lab['root'], database(lab['root'], seeded_db, newer=True))
    out = restore(lab, path, target)
    assert out.returncode != 0
    assert 'target: Coil qa-old-20261001 (commit e007fa9)' in out.stderr
    assert 'invoices.newer_credit_kind' in out.stderr
    assert 'compose run --rm --no-deps -T web python -m app.cli known_schema' in (lab['root'] / 'docker-calls').read_text()
    assert listing(target) == ['docker-compose.yml'], 'the data dir docker created must not be left behind'


def test_compose_target_with_same_schema_restores(lab, seeded_db):
    target = compose_install(lab)
    path = archive(lab['root'], database(lab['root'], seeded_db))
    out = restore(lab, path, target)
    assert out.returncode == 0, out.stdout + out.stderr
    assert 'Version check passed' in out.stdout
    assert 'Coil qa-old-20261001' in out.stdout
    restored_ok(target)
