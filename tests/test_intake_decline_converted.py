"""A stale Decline form must not undo an already completed lead conversion."""
import pytest
from tests.test_phase1_independent import app, staff


@pytest.mark.parametrize("role", ["owner", "attorney", "paralegal"])
def test_stale_decline_preserves_converted_lead(app, role):
    from app.extensions import db
    from app.models import IntakeLead, Matter, AuditLog
    with app.app_context():
        lead = IntakeLead(name="QA2 Converted 20261003", email="qa2-converted@example.test",
                          status="converted", stage="won", contact_id=1, matter_id=1)
        db.session.add(lead)
        db.session.commit()
        lid = lead.id
    client, csrf = staff(app, role)
    response = client.post(f"/intake/{lid}/decline", data={"_csrf": csrf, "reason": "QA2 stale form"},
                           follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        lead = db.session.get(IntakeLead, lid)
        assert (lead.status, lead.stage, lead.matter_id, lead.contact_id) == ("converted", "won", 1, 1)
        assert not lead.lost_reason
        assert not AuditLog.query.filter_by(action="decline", entity="intake_lead", entity_id=lid).first()
        assert Matter.query.count() == 1
    assert b"Converted leads keep their status." in response.data
    # The refusal must also preserve the guard against converting the same lead again.
    response = client.post(f"/intake/{lid}/convert", data={"_csrf": csrf}, follow_redirects=True)
    assert b"This lead was already converted." in response.data
    with app.app_context():
        assert Matter.query.count() == 1


@pytest.mark.parametrize("status,stage", [("new", "new"), ("contacted", "contacted")])
def test_unconverted_lead_can_still_be_declined(app, status, stage):
    from app.extensions import db
    from app.models import IntakeLead, AuditLog
    with app.app_context():
        lead = IntakeLead(name="QA2 Decline 20261003", status=status, stage=stage)
        db.session.add(lead)
        db.session.commit()
        lid = lead.id
    client, csrf = staff(app)
    response = client.post(f"/intake/{lid}/decline", data={"_csrf": csrf, "reason": "QA2 reason"},
                           follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        lead = db.session.get(IntakeLead, lid)
        assert (lead.status, lead.stage, lead.lost_reason) == ("declined", "lost", "QA2 reason")
        assert AuditLog.query.filter_by(action="decline", entity="intake_lead", entity_id=lid).count() == 1
