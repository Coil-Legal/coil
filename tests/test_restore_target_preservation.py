"""Restore must not merge a backup into leftover firm files without a database."""
import subprocess
from pathlib import Path
import pytest
from tests.test_restore_nightly import archive

SCRIPT = Path(__file__).resolve().parents[1] / 'ops/restore.sh'

def run(source, target):
    return subprocess.run(['bash', str(SCRIPT), str(source), str(target)], capture_output=True, text=True)

@pytest.mark.parametrize('prefix', ['', 'data/'])
@pytest.mark.parametrize('name', ['uploads/1/evidence.txt', 'pdf/invoice.pdf', '.existing-marker'])
def test_existing_data_files_are_preserved_before_any_extraction(tmp_path, prefix, name):
    source = archive(tmp_path, prefix=prefix)
    target = tmp_path / 'install'
    protected = target / 'data' / name
    protected.parent.mkdir(parents=True)
    protected.write_bytes(b'existing synthetic firm data')
    before = {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()}
    result = run(source, target)
    after = {p.relative_to(target): p.read_bytes() for p in target.rglob('*') if p.is_file()}
    assert result.returncode != 0, 'reported success while merging into existing data'
    assert 'refusing' in result.stderr.lower()
    assert before == after, 'restore changed existing target contents'

@pytest.mark.parametrize('prefix', ['', 'data/'])
def test_data_symlink_is_refused_without_writing_its_target(tmp_path, prefix):
    source = archive(tmp_path, prefix=prefix)
    outside = tmp_path / 'other-firm'
    outside.mkdir()
    target = tmp_path / 'install'
    target.mkdir()
    (target / 'data').symlink_to(outside, target_is_directory=True)
    result = run(source, target)
    assert result.returncode != 0
    assert 'refusing' in result.stderr.lower()
    assert not list(outside.iterdir())
    assert not (target / '.env').exists()
    assert (target / 'data').is_symlink()

@pytest.mark.parametrize('prefix', ['', 'data/'])
def test_empty_data_directory_and_existing_app_code_are_allowed(tmp_path, prefix):
    source = archive(tmp_path, prefix=prefix)
    target = tmp_path / 'install'
    (target / 'data').mkdir(parents=True)
    (target / 'app.py').write_bytes(b'# existing synthetic app code')
    result = run(source, target)
    assert result.returncode == 0, result.stderr
    assert (target / 'app.py').read_bytes() == b'# existing synthetic app code'
    assert (target / 'data/uploads/1/evidence.txt').read_bytes() == b'synthetic upload'
    assert (target / 'data/pdf/invoice.pdf').read_bytes() == b'synthetic PDF bytes'
