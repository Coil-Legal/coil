"""Independent accounting examples for the Phase 1 completion pass."""
from datetime import date
from tests.test_phase1_independent import app
TODAY = date.today()

def make_billed_time(split=False, cents=10000):
    from app.extensions import db
    from app.models import Contact, Matter, MatterPayer, TimeEntry, User
    from app.blueprints.invoices import build_for_matter
    matter = db.session.get(Matter, 1)
    if split:
        other = Contact(first_name='Second', last_name='Payer', email='second@example.test')
        db.session.add(other); db.session.flush()
        db.session.add_all([MatterPayer(matter_id=1, contact_id=1, percent=50),
                            MatterPayer(matter_id=1, contact_id=other.id, percent=50)])
        db.session.flush()
    entry = TimeEntry(matter_id=1,user_id=1,date=TODAY,minutes=60,rate_cents=cents,billable=True,description='Review')
    db.session.add(entry);db.session.flush()
    invoices = build_for_matter(matter,db.session.get(User,1),TODAY,TODAY)
    for inv in invoices: inv.status='sent'
    db.session.commit()
    return entry,invoices

def test_split_realization_includes_both_payers(app):
    from app.extensions import db
    from app.models import Payment
    from app.blueprints.reports import realization_data
    with app.app_context():
        _, invoices=make_billed_time(split=True)
        for inv in invoices:
            db.session.add(Payment(invoice_id=inv.id,matter_id=1,client_id=inv.client_id,
                                   amount_cents=inv.total_cents,account='operating',method='check',received_on=TODAY))
        db.session.commit()
        _,_,totals=realization_data(TODAY,TODAY)
        assert totals['billed']==10000
        assert totals['collected']==10000, 'Both $50 payer receipts must count toward the $100 time entry'

def test_unbilled_work_on_previously_billed_matter_is_not_written_down(app):
    from app.extensions import db
    from app.models import TimeEntry
    from app.blueprints.reports import realization_data
    with app.app_context():
        make_billed_time()
        db.session.add(TimeEntry(matter_id=1,user_id=1,date=TODAY,minutes=60,rate_cents=6000,
                                 billable=True,description='New unbilled work'))
        db.session.commit()
        _,_,totals=realization_data(TODAY,TODAY)
        assert totals['worked']==16000
        assert totals['billed']==10000
        assert totals['writedown']==0, 'Unbilled WIP does not become a write-down because another entry was invoiced'

def test_split_rounding_preserves_billed_cent(app):
    from app.blueprints.reports import realization_data
    with app.app_context():
        make_billed_time(split=True,cents=10001)
        _,_,totals=realization_data(TODAY,TODAY)
        assert totals['billed']==10001, '$50.01 plus $50.00 must not be reconstructed as $100.02'


def test_split_receipts_count_only_money_received(app):
    from app.extensions import db
    from app.models import Payment
    from app.blueprints.reports import realization_data
    with app.app_context():
        _, invoices = make_billed_time(split=True, cents=10001)
        inv = invoices[1]
        db.session.add(Payment(invoice_id=inv.id, matter_id=1, client_id=inv.client_id,
                               amount_cents=2300, account='operating', method='check', received_on=TODAY))
        db.session.commit()
        _, _, totals = realization_data(TODAY, TODAY)
        assert totals['billed'] == 10001
        assert totals['collected'] == 2300


def test_void_split_invoices_leave_work_unbilled(app):
    from app.extensions import db
    from app.blueprints.reports import realization_data
    with app.app_context():
        _, invoices = make_billed_time(split=True)
        for inv in invoices:
            inv.status = 'void'
        db.session.commit()
        _, _, totals = realization_data(TODAY, TODAY)
        assert totals['worked'] == 10000
        assert totals['billed'] == totals['collected'] == totals['writedown'] == 0
