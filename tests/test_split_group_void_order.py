"""QA #124: voiding one invoice in a split group must list all members in id order,
not the voided invoice first."""
from tests.test_phase1_independent import app, staff


def test_void_middle_of_split_group_lists_members_in_id_order(app):
    from app.extensions import db
    from app.models import Invoice

    with app.app_context():
        first = Invoice(number="QA-SPLIT-1", client_id=1, matter_id=1, status="draft",
                         split_group="QA-SPLIT-ORDER", split_pct=40.0)
        second = Invoice(number="QA-SPLIT-2", client_id=1, matter_id=1, status="draft",
                         split_group="QA-SPLIT-ORDER", split_pct=30.0)
        third = Invoice(number="QA-SPLIT-3", client_id=1, matter_id=1, status="draft",
                         split_group="QA-SPLIT-ORDER", split_pct=30.0)
        db.session.add_all([first, second, third])
        db.session.commit()
        middle_id = second.id
        numbers_in_id_order = sorted([first, second, third], key=lambda i: i.id)
        expected = ", ".join(i.number for i in numbers_in_id_order)

    client, tok = staff(app)
    r = client.post(f"/invoices/{middle_id}/void", data={"_csrf": tok}, follow_redirects=True)
    assert r.status_code == 200
    assert f"Voided the split group: {expected}.".encode() in r.data
