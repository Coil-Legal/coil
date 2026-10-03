"""A matter edit that fails validation must re-show the form, not 500 (Coil QA #96).

Bot 1 saved matter 3111's edit form with no client selected and got HTTP 500:
`NOT NULL constraint failed: matters.client_id`. edit() fills the stored matter from the
form first, so rendering the form for "Pick a client." ran a query that autoflushed the
NULL client. The user should see the message, keep their input on screen, and find the
stored matter untouched.

Run: .venv/bin/python -m pytest tests/test_matter_edit_validation.py -q
"""
import pytest

from tests.test_phase1_independent import app, staff  # noqa: F401


def _matter(app):
    from app.models import Matter
    with app.app_context():
        m = Matter.query.filter_by(number='M-PHASE1').one()
        return m.id, m.client_id, m.name, m.description


@pytest.mark.parametrize('form, message', [
    ({'client_id': '', 'name': 'QA renamed 96'}, 'Pick a client.'),
    ({'client_id': '999999', 'name': 'QA renamed 96'}, 'Pick a client.'),
    ({'name': ''}, 'A matter name is required.'),
])
def test_invalid_matter_edit_shows_the_message_and_saves_nothing(app, form, message):
    mid, client_id, name, description = _matter(app)
    owner, csrf = staff(app)
    data = {'_csrf': csrf, 'client_id': str(client_id), 'name': name, 'status': 'open',
            'billing_type': 'hourly', 'description': 'QA description 96'}
    data.update(form)
    r = owner.post(f'/matters/{mid}/edit', data=data)
    assert r.status_code == 200, r.status_code
    assert message in r.get_data(as_text=True)
    assert _matter(app) == (mid, client_id, name, description), 'a refused edit must not be saved'


def test_valid_matter_edit_still_saves(app):
    mid, client_id, name, _ = _matter(app)
    owner, csrf = staff(app)
    r = owner.post(f'/matters/{mid}/edit', data={
        '_csrf': csrf, 'client_id': str(client_id), 'name': name, 'status': 'open',
        'billing_type': 'hourly', 'description': 'QA saved 96 Καλημέρα'})
    assert r.status_code == 302
    assert _matter(app)[3] == 'QA saved 96 Καλημέρα'
