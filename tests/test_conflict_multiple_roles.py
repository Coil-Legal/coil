"""A conflict result must preserve distinct roles even on one matter."""
import pytest
from tests.test_phase1_independent import app, staff

@pytest.mark.parametrize('roles', [('adverse', 'witness'), ('witness', 'adverse')])
def test_saved_check_preserves_both_roles_on_one_matter(app, roles):
    from app.extensions import db
    from app.models import MatterParty, ConflictCheck
    client, csrf = staff(app)
    for role in roles:
        response = client.post('/matters/1/parties', data={
            '_csrf': csrf, 'name': 'Synthetic Ren Vale', 'role': role})
        assert response.status_code == 302
    with app.app_context():
        assert MatterParty.query.filter_by(matter_id=1, name='Synthetic Ren Vale').count() == 2
    response = client.post('/conflicts/run', data={'_csrf': csrf, 'names': 'Synthetic Ren Vale'})
    assert response.status_code == 302
    with app.app_context():
        check = db.session.query(ConflictCheck).order_by(ConflictCheck.id.desc()).first()
        hits = [h for h in check.results if h['source'] == 'party' and h['url'] == '/matters/1']
        assert {h['role'] for h in hits} == {'adverse', 'witness'}
        assert len(hits) == 2
        assert check.outcome == 'unresolved'
    page = client.get(response.location)
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert '<td>adverse</td>' in html and '<td>witness</td>' in html

def test_duplicate_same_role_still_collapses(app):
    from app.extensions import db
    from app.models import MatterParty
    from app.blueprints.conflicts import search_hits
    with app.app_context():
        db.session.add_all([MatterParty(matter_id=1, name='Synthetic Ren Vale', role='adverse') for _ in range(2)])
        db.session.commit()
        hits = [h for h in search_hits(['Synthetic Ren Vale']) if h['source'] == 'party']
        assert len(hits) == 1 and hits[0]['role'] == 'adverse'
