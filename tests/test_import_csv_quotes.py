"""Valid CSV doubled quotes must survive delimiter sniffing and contact import."""
import csv
import io

import pytest
from tests.test_phase1_independent import app, staff


def csv_bytes(address, delimiter=','):
    buf = io.StringIO(newline='')
    writer = csv.writer(buf, delimiter=delimiter)
    writer.writerow(['Id', 'Name', 'Type', 'Email Address (Work)', 'Primary Address', 'Tags'])
    writer.writerow(['QA2-C1', 'QA2 Import Δοκιμή', 'Person', 'qa2-csv@example.test', address, 'QA2'])
    writer.writerow(['QA2-C2', 'QA2 Plain', 'Person', '', 'Plain address', 'QA2'])
    return buf.getvalue().encode('utf-8-sig')


@pytest.mark.parametrize('delimiter', [',', ';', '\t'])
@pytest.mark.parametrize('address', [
    'QA2 Line 1\nQA2 Line 2, suite "A"',
    'QA2 first line\r\n"quoted" second line',
    'QA2 suite "A", street; district\tunit',
    'QA2 plain address',
])
def test_csv_preserves_quoted_fields(delimiter, address):
    from app.blueprints.importer import _parse_csv
    headers, rows = _parse_csv(csv_bytes(address, delimiter))
    assert headers == ['Id', 'Name', 'Type', 'Email Address (Work)', 'Primary Address', 'Tags']
    assert len(rows) == 2
    assert rows[0]['Primary Address'] == address
    assert rows[0]['Tags'] == rows[1]['Tags'] == 'QA2'
    assert rows[0]['Name'] == 'QA2 Import Δοκιμή'
    assert rows[1]['Primary Address'] == 'Plain address'


def test_contact_import_and_export_preserve_embedded_quotes(app):
    from app.models import Contact
    owner, csrf = staff(app)
    address = 'QA2 Line 1\nQA2 Line 2, suite "A"'
    upload = owner.post('/import/contacts/upload', data={
        '_csrf': csrf, 'source': 'clio',
        'file': (io.BytesIO(csv_bytes(address)), 'qa2-quotes.csv'),
    }, content_type='multipart/form-data')
    assert upload.status_code == 302 and '/import/preview/' in upload.location
    commit = owner.post(upload.location, data={'_csrf': csrf, 'do': 'commit', 'duplicates': 'update'})
    assert commit.status_code == 302 and '/import/jobs/' in commit.location
    with app.app_context():
        contact = Contact.query.filter_by(email='qa2-csv@example.test').one()
        assert contact.address == address
        cid = contact.id
    export = owner.get('/exports/contacts.csv')
    assert export.status_code == 200
    rows = list(csv.DictReader(io.StringIO(export.data.decode('utf-8-sig'))))
    row = next(r for r in rows if r['Id'] == str(cid))
    assert row['Address'] == 'QA2 Line 1, QA2 Line 2, suite "A"'
