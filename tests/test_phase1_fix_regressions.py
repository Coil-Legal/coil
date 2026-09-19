"""Successful operations and retries accompanying the independent defect checks."""
import json
from datetime import date, timedelta

import pytest
from werkzeug.datastructures import MultiDict

from tests.test_phase1_independent import app, staff, settlement


def test_twilio_official_signature_vectors():
    from app.services.twilio_verify import valid_signature
    url = 'https://mycompany.com/myapp.php?foo=1&bar=2'
    form = MultiDict({'CallSid': 'CA1234567890ABCDE', 'Digits': '1234', 'From': '+14158675309',
                      'To': '+18005551212', 'Caller': '+14158675309'})
    assert valid_signature('12345', url, form, 'RSOYDt4T1cUTdK1PDd93/VVr8B8=')
    repeated = MultiDict([('Sid', 'CA123'), ('SidAccount', 'AC123'), ('Digits', '5678'),
                          ('Digits', '1234'), ('Digits', '1234')])
    assert valid_signature('12345', url, repeated, 'IK+Dwps556ElfBT0I3Rgjkr1wJU=')
    assert not valid_signature('12345', url + '&extra=1', form, 'RSOYDt4T1cUTdK1PDd93/VVr8B8=')
    assert not valid_signature('12345', url, form, 'invalid 王')


def test_twilio_delivery_matches_contact_and_deduplicates(app):
    from app.extensions import db
    from app.models import Contact, Message
    from tests.helpers import post_twilio_form
    with app.app_context():
        db.session.get(Contact, 1).phone = '+15550001111'
        db.session.commit()
    payload = {'From': '+15550001111', 'To': '+15550002222', 'MessageSid': 'SM-test-valid', 'Body': 'Hello 王'}
    c = app.test_client()
    assert post_twilio_form(c, app, payload).status_code == 200
    assert post_twilio_form(c, app, payload).status_code == 200
    with app.app_context():
        msg = Message.query.filter_by(provider_id='SM-test-valid').one()
        assert msg.contact_id == 1 and msg.body == 'Hello 王'
    app.config['TWILIO_AUTH_TOKEN'] = ''
    assert c.post('/webhooks/twilio', data=payload).status_code == 503


def test_pi_owner_can_disburse_once_with_available_funds(app):
    from app.models import TrustTransaction, SettlementWorksheet
    from app.extensions import db
    wid = settlement(app)
    c, csrf = staff(app)
    for _ in range(2):
        assert c.post(f'/pi/1/worksheet/{wid}/disburse', data={'_csrf': csrf}).status_code == 302
    with app.app_context():
        assert db.session.get(SettlementWorksheet, wid).status == 'disbursed'
        assert sum(t.amount_cents for t in TrustTransaction.query.all()) == 0
        assert TrustTransaction.query.filter(TrustTransaction.amount_cents < 0).count() == 1


def test_automatic_email_retries_same_draft_and_advances_once(app, monkeypatch):
    from app.extensions import db
    from app.models import IntakeLead, FollowUpSequence, LeadSequence, Message
    from app.blueprints.intake import process_lead_sequence
    outcomes = iter([False, True])
    calls = []
    def deliver(*args, **kwargs):
        calls.append(args)
        return next(outcomes)
    monkeypatch.setattr('app.blueprints.intake.send_email', deliver)
    with app.app_context():
        lead = IntakeLead(name='Prospect', email='prospect@example.test')
        seq = FollowUpSequence(name='Retry', steps_json=json.dumps([{'day': 0, 'subject': 'Hello', 'body': 'Test'}]))
        db.session.add_all([lead, seq])
        db.session.flush()
        ls = LeadSequence(lead_id=lead.id, sequence_id=seq.id, started_on=date.today())
        db.session.add(ls)
        db.session.commit()
        assert process_lead_sequence(ls, date.today(), True) == (0, 0)
        msg_id = Message.query.one().id
        assert ls.next_step == 0 and ls.status == 'active'
        assert process_lead_sequence(ls, date.today(), True) == (1, 0)
        assert process_lead_sequence(ls, date.today(), True) == (0, 0)
        msg = Message.query.one()
        assert msg.id == msg_id and msg.status == 'sent'
        assert ls.next_step == 1 and ls.status == 'done' and len(calls) == 2


def test_signature_send_and_reminder_retry_do_not_invent_events(app, tmp_path, monkeypatch):
    from app.extensions import db
    from app.models import Document, DocumentSignature, DocumentSignatureEvent
    p = tmp_path / 'agreement.txt'
    p.write_text('Please sign this synthetic agreement.')
    with app.app_context():
        doc = Document(matter_id=1, name='agreement.txt', path=str(p), mime='text/plain')
        db.session.add(doc)
        db.session.flush()
        sig = DocumentSignature(document_id=doc.id, contact_id=1, status='draft')
        db.session.add(sig)
        db.session.commit()
        sid = sig.id
    c, csrf = staff(app)
    for delivered in (False, True):
        monkeypatch.setattr('app.blueprints.signatures.send_email', lambda *a, **k: delivered)
        c.post(f'/signatures/{sid}/send', data={'_csrf': csrf})
        with app.app_context():
            sig = db.session.get(DocumentSignature, sid)
            assert sig.status == ('sent' if delivered else 'draft')
            assert bool(sig.sent_at) == delivered
            assert DocumentSignatureEvent.query.filter_by(signature_id=sid, event='sent').count() == int(delivered)
    for delivered in (False, True):
        monkeypatch.setattr('app.blueprints.signatures.send_email', lambda *a, **k: delivered)
        c.post(f'/signatures/{sid}/remind', data={'_csrf': csrf})
        with app.app_context():
            assert DocumentSignatureEvent.query.filter_by(signature_id=sid, event='reminder').count() == int(delivered)


def import_trust(rows, dry=False, duplicates='update'):
    from app.blueprints.importer import run_import
    from app.blueprints._importmap import field_defs
    from app.models import User
    from app.extensions import db
    fields = ('external_id', 'date', 'client_name', 'matter_number', 'amount', 'type', 'description')
    raw = [dict(zip(fields, r), _row=i + 2) for i, r in enumerate(rows)]
    return run_import({'entity': 'trust', 'source': 'generic', 'rows': raw}, {k: k if k in fields else '' for k, *_ in field_defs('trust')},
                      {'duplicates': duplicates}, db.session.get(User, 1), dry)


def trust_row(ext, amount, when=None):
    return (ext, (when or date.today()).isoformat(), 'Synthetic Client', 'M-PHASE1', str(amount),
            'deposit' if amount > 0 else 'disbursement', 'Synthetic trust import')


def test_trust_import_preview_commit_and_reimport_agree(app):
    from app.models import TrustTransaction
    with app.app_context():
        rows = [trust_row('deposit', 100), trust_row('withdrawal', -80)]
        for dry in (True, False):
            result = import_trust(rows, dry)
            assert result['counts']['created'] == 2 and not result['errors'], result
        # A safe increase in the deposit is an update, never a duplicate.
        for dry in (True, False):
            result = import_trust([trust_row('deposit', 120)], dry)
            assert result['counts']['updated'] == 1 and not result['errors'], result
        assert TrustTransaction.query.count() == 2
        assert sum(t.amount_cents for t in TrustTransaction.query.all()) == 4000


@pytest.mark.parametrize('change', ['reduce', 'move_later', 'change_client'])
def test_trust_import_cannot_remove_funding_used_by_a_later_withdrawal(app, change):
    from app.extensions import db
    from app.models import Contact, TrustTransaction
    with app.app_context():
        today = date.today()
        assert not import_trust([trust_row('deposit', 100, today - timedelta(days=2)),
                                 trust_row('withdrawal', -80, today)])['errors']
        row = trust_row('deposit', 50 if change == 'reduce' else 100,
                        today + timedelta(days=1) if change == 'move_later' else today - timedelta(days=2))
        if change == 'change_client':
            db.session.add(Contact(first_name='Other', last_name='Client', is_client=True))
            db.session.commit()
            row = (*row[:2], 'Other Client', '', *row[4:])
        for dry in (True, False):
            result = import_trust([row], dry)
            assert result['counts']['errors'] == 1, result
        assert sum(t.amount_cents for t in TrustTransaction.query.filter_by(client_id=1)) == 2000


def test_skipped_import_deposit_cannot_fund_another_row(app):
    with app.app_context():
        assert not import_trust([trust_row('deposit', 100)])['errors']
        rows = [trust_row('deposit', 1000), trust_row('withdrawal', -200)]
        for dry in (True, False):
            result = import_trust(rows, dry, 'skip')
            assert result['counts']['skipped'] == 1 and result['counts']['errors'] == 1, result


def test_trust_import_commit_rechecks_since_preview(app):
    from app.extensions import db
    from app.models import TrustTransaction
    with app.app_context():
        import_trust([trust_row('deposit', 100)])
        assert not import_trust([trust_row('withdrawal', -80)], True)['errors']
        db.session.add(TrustTransaction(client_id=1, matter_id=1, date=date.today(), type='disbursement', amount_cents=-5000))
        db.session.commit()
        result = import_trust([trust_row('withdrawal', -80)])
        assert result['counts']['errors'] == 1 and TrustTransaction.query.count() == 2


def test_conflict_checker_requires_waiver_reason_and_valid_query(app):
    from app.extensions import db
    from app.models import ConflictCheck
    from app.blueprints.conflicts import run_check
    with app.app_context():
        chk = run_check('Synthetic Client')
        cid = chk.id
        with pytest.raises(ValueError):
            run_check('!!!')
    c, csrf = staff(app)
    c.post(f'/conflicts/{cid}/resolve', data={'_csrf': csrf, 'outcome': 'waived', 'notes': ' '})
    with app.app_context():
        assert db.session.get(ConflictCheck, cid).outcome == 'unresolved'
    c.post(f'/conflicts/{cid}/resolve', data={'_csrf': csrf, 'outcome': 'waived', 'notes': 'Reviewed by owner.'})
    with app.app_context():
        assert db.session.get(ConflictCheck, cid).outcome == 'waived'


def test_only_public_intake_has_embeddable_headers(app):
    c, _ = staff(app)
    public = c.get('/intake/form')
    assert public.status_code == 200 and 'X-Frame-Options' not in public.headers
    assert 'frame-ancestors *' in public.headers['Content-Security-Policy']
    for path in ('/', '/login', '/intake', '/portal'):
        assert c.get(path).headers['X-Frame-Options'] == 'DENY'


def test_failed_import_row_does_not_reduce_available_preview_funds(app):
    with app.app_context():
        rows = [trust_row('deposit', 100), trust_row('bad', -200), trust_row('valid', -80)]
        for dry in (True, False):
            result = import_trust(rows, dry)
            assert result['counts']['created'] == 2 and result['counts']['errors'] == 1, result


def test_import_cannot_move_an_existing_closed_period_row(app):
    from app.extensions import db
    from app.models import TrustReconciliation, TrustTransaction
    with app.app_context():
        yesterday = date.today() - timedelta(days=1)
        assert not import_trust([trust_row('deposit', 100, yesterday)])['errors']
        db.session.add(TrustReconciliation(period_end=yesterday, balanced=True,
                                           book_balance_cents=10000, bank_statement_cents=10000))
        db.session.commit()
        for dry in (True, False):
            result = import_trust([trust_row('deposit', 100)], dry)
            assert result['counts']['errors'] == 1, result
        assert TrustTransaction.query.one().date == yesterday


def test_twilio_uses_firm_token_and_rejects_tampering(app):
    from app.extensions import db
    from app.integrations import save_firm_values
    from app.models import Message
    from tests.helpers import post_twilio_form
    payload = {'From': '+15550001111', 'To': '+15550002222', 'MessageSid': 'SM-firm-token', 'Body': 'Hello'}
    with app.app_context():
        save_firm_values({'TWILIO_AUTH_TOKEN': 'local-twilio-test-token'})
        db.session.commit()
    # The helper supplies the signature; capture it to replay a changed body.
    c = app.test_client()
    response = post_twilio_form(c, app, payload)
    assert response.status_code == 200
    signature = response.request.headers['X-Twilio-Signature']
    app.config['TWILIO_AUTH_TOKEN'] = ''
    assert c.post('/webhooks/twilio', data=payload, headers={'X-Twilio-Signature': signature}).status_code == 200
    payload.update(MessageSid='SM-tampered', Body='Changed')
    assert c.post('/webhooks/twilio', data=payload, headers={'X-Twilio-Signature': signature}).status_code == 403
    with app.app_context():
        assert Message.query.count() == 1
