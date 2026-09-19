"""Independent Phase 1 acceptance checks. Uses synthetic data, never live integrations.

These assertions describe required behavior. Failures reproduce review findings.
Run from a disposable Coil checkout, with this file under tests/.
"""
import io
import json
import os
from pathlib import Path
import subprocess
from datetime import date, timedelta

import pytest
from flask import template_rendered


@pytest.fixture
def app(tmp_path, monkeypatch):
    for key in ('DATABASE_URL', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'SMTP_HOST',
                'TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY'):
        monkeypatch.delenv(key, raising=False)
    import requests
    def offline(*args, **kwargs):
        raise RuntimeError('Independent review: external HTTP is disabled')
    monkeypatch.setattr(requests.sessions.Session, 'request', offline)
    from app import create_app
    from app.extensions import db
    from app.models import Firm, User, Contact, Matter
    a = create_app({'TESTING': True, 'SECRET_KEY': 'phase1-synthetic',
                    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{tmp_path}/review.db',
                    'UPLOAD_DIR': str(tmp_path / 'uploads'), 'PDF_DIR': str(tmp_path / 'pdf'),
                    'SMTP_HOST': '', 'STRIPE_SECRET_KEY': '', 'STRIPE_WEBHOOK_SECRET': ''})
    with a.app_context():
        Firm.get()
        for role in ('owner', 'attorney', 'paralegal'):
            u = User(email=f'{role}@example.test', name=role, role=role)
            u.set_password('synthetic-password')
            db.session.add(u)
        c = Contact(first_name='Synthetic', last_name='Client', email='client@example.test', is_client=True)
        db.session.add(c)
        db.session.flush()
        db.session.add(Matter(number='M-PHASE1', name='Synthetic matter', client_id=c.id,
                              status='open', billing_type='hourly'))
        db.session.commit()
    yield a
    with a.app_context():
        db.session.remove()
        db.engine.dispose()


def staff(app, role='owner'):
    from tests.helpers import login
    c = app.test_client()
    return c, login(c, f'{role}@example.test', 'synthetic-password')


def settlement(app, deposit_date=None, close=False):
    from app.extensions import db
    from app.models import PiCase, SettlementWorksheet, TrustTransaction, TrustReconciliation
    with app.app_context():
        db.session.add(PiCase(matter_id=1))
        ws = SettlementWorksheet(matter_id=1, gross_cents=10000, fee_pct=0, fee_cents=0,
                                 net_to_client_cents=10000, status='approved', is_current=True)
        db.session.add(ws)
        db.session.add(TrustTransaction(client_id=1, matter_id=1, date=deposit_date or date.today(),
                                        type='deposit', amount_cents=10000, description='Synthetic deposit'))
        if close:
            db.session.add(TrustReconciliation(period_end=date.today(), balanced=True,
                                               book_balance_cents=10000, bank_statement_cents=10000))
        db.session.commit()
        return ws.id


@pytest.mark.parametrize('role', ['attorney', 'paralegal'])
def test_pi_disbursement_requires_trust_permission(app, role):
    from app.models import TrustTransaction
    wid = settlement(app)
    c, csrf = staff(app, role)
    assert c.get('/trust/').status_code == 403
    r = c.post(f'/pi/1/worksheet/{wid}/disburse', data={'_csrf': csrf})
    with app.app_context():
        debits = TrustTransaction.query.filter(TrustTransaction.amount_cents < 0).count()
    assert r.status_code == 403 and debits == 0, f'HTTP {r.status_code}; unauthorized debit rows: {debits}'


@pytest.mark.parametrize('condition', ['future_deposit', 'closed_period'])
def test_pi_disbursement_obeys_trust_dates(app, condition):
    from app.models import SettlementWorksheet, TrustTransaction
    wid = settlement(app, date.today() + timedelta(days=7) if condition == 'future_deposit' else date.today(),
                     close=condition == 'closed_period')
    c, csrf = staff(app)
    c.post(f'/pi/1/worksheet/{wid}/disburse', data={'_csrf': csrf})
    with app.app_context():
        ws = SettlementWorksheet.query.get(wid)
        today_balance = sum(t.amount_cents for t in TrustTransaction.query.filter(
            TrustTransaction.date <= date.today()).all())
        assert ws.status == 'approved', f'{condition}: status={ws.status}; balance today={today_balance}'


@pytest.mark.parametrize('condition', ['future_deposit', 'closed_period'])
def test_imported_trust_obeys_trust_dates(app, condition):
    from app.models import TrustTransaction, ImportJob
    settlement(app, date.today() + timedelta(days=7) if condition == 'future_deposit' else date.today(),
               close=condition == 'closed_period')
    c, csrf = staff(app)
    body = ('ID,Date,Type,Source/Destination,Client,Matter,Description,Check or reference no.,Funds In,Funds Out,Cleared\n'
            f'review-t1,{date.today().isoformat()},Disbursement,Vendor,Synthetic Client,M-PHASE1,Review import,R1,,100.00,No\n')
    r = c.post('/import/trust/upload', data={'_csrf': csrf, 'source': 'clio',
               'file': (io.BytesIO(body.encode()), 'trust.csv')}, content_type='multipart/form-data')
    assert r.status_code == 302 and '/import/preview/' in r.location
    r = c.post(r.location, data={'_csrf': csrf, 'do': 'commit'})
    assert r.status_code == 302
    with app.app_context():
        job = ImportJob.query.order_by(ImportJob.id.desc()).first()
        debits = TrustTransaction.query.filter(TrustTransaction.amount_cents < 0).count()
        assert debits == 0, f'{condition}: imported {job.created} rows; debit rows={debits}'


@pytest.mark.parametrize('source', ['note', 'message', 'document', 'lead'])
def test_intake_gate_finds_existing_conflicts_in_all_advertised_sources(app, source):
    from app.extensions import db
    from app.models import Note, Message, Document, IntakeLead, ConflictCheck
    from app.blueprints.conflicts import run_check
    name = 'Zelda Quenby'
    with app.app_context():
        if source == 'note':
            db.session.add(Note(matter_id=1, body=f'Adverse party is {name}.'))
        elif source == 'message':
            db.session.add(Message(contact_id=1, matter_id=1, direction='in', channel='portal', body=f'Adverse party is {name}.'))
        elif source == 'document':
            db.session.add(Document(matter_id=1, name='record.txt', path='synthetic.txt', extracted_text=f'Adverse party is {name}.'))
        else:
            db.session.add(IntakeLead(name='Other Prospect', adverse_party=name, email='other@example.test'))
        db.session.commit()
        assert any(h['source'] == source for h in run_check(name).results)
        lead = IntakeLead(name=name, email='new@example.test', matter_type='Litigation')
        db.session.add(lead)
        db.session.commit()
        lid = lead.id
    c, csrf = staff(app)
    c.post(f'/intake/{lid}/convert', data={'_csrf': csrf, 'billing_type': 'hourly', 'matter_name': 'New review matter'})
    with app.app_context():
        lead = db.session.get(IntakeLead, lid)
        latest = db.session.query(ConflictCheck).order_by(ConflictCheck.id.desc()).first()
        assert lead.status != 'converted', f'{source} hit lost; created matter {lead.matter_id}, outcome={latest.outcome}'


def test_conflict_waiver_requires_a_reason(app):
    from app.extensions import db
    from app.models import IntakeLead, ConflictCheck
    with app.app_context():
        lead = IntakeLead(name='Synthetic Client', email='new@example.test')
        db.session.add(lead)
        db.session.commit()
        lid = lead.id
    c, csrf = staff(app)
    c.post(f'/intake/{lid}/convert', data={'_csrf': csrf, 'conflict_ack': '1', 'conflict_reason': '',
                                          'matter_name': 'Waiver test', 'billing_type': 'hourly'})
    with app.app_context():
        check = db.session.query(ConflictCheck).order_by(ConflictCheck.id.desc()).first()
        assert db.session.get(IntakeLead, lid).status != 'converted', f'Waived with empty reason: {check.notes}'


@pytest.mark.parametrize('name', ['王伟', 'Иван Иванов', 'Γιάννης Παπαδόπουλος', 'محمد علي'])
def test_conflict_search_matches_identical_non_latin_names(app, name):
    from app.extensions import db
    from app.models import Contact
    from app.blueprints.conflicts import run_check
    with app.app_context():
        contact = Contact(first_name=name, is_client=True)
        db.session.add(contact)
        db.session.commit()
        url = f'/contacts/{contact.id}'
        check = run_check(name)
        assert any(h['url'] == url for h in check.results), f'Identical name returned {check.outcome}: {name}'


def test_failed_automatic_followup_stays_retryable(app, monkeypatch):
    from app.extensions import db
    from app.models import IntakeLead, FollowUpSequence, LeadSequence, Message
    from app.blueprints.intake import process_lead_sequence
    monkeypatch.setattr('app.blueprints.intake.send_email', lambda *a, **k: False)
    with app.app_context():
        lead = IntakeLead(name='Prospect', email='prospect@example.test')
        seq = FollowUpSequence(name='Synthetic', steps_json=json.dumps([{'day': 0, 'subject': 'Hello', 'body': 'Test'}]))
        db.session.add_all([lead, seq])
        db.session.flush()
        ls = LeadSequence(lead_id=lead.id, sequence_id=seq.id, started_on=date.today())
        db.session.add(ls)
        db.session.commit()
        outcome = process_lead_sequence(ls, date.today(), True)
        msg = Message.query.filter_by(channel='email').one()
        assert msg.status != 'sent' and ls.status != 'done', f'Failed delivery: {outcome}, message={msg.status}, sequence={ls.status}'


def test_failed_manual_followup_remains_a_draft(app, monkeypatch):
    from app.extensions import db
    from app.models import Message
    monkeypatch.setattr('app.blueprints.intake.send_email', lambda *a, **k: False)
    with app.app_context():
        msg = Message(direction='out', channel='email', to_addr='prospect@example.test', subject='Hello', body='Test', status='draft')
        db.session.add(msg)
        db.session.commit()
        mid = msg.id
    c, csrf = staff(app)
    c.post(f'/intake/drafts/{mid}/send', data={'_csrf': csrf})
    with app.app_context():
        assert db.session.get(Message, mid).status == 'draft'


def test_time_totals_equal_displayed_entry_amounts(app):
    from app.extensions import db
    from app.models import TimeEntry
    with app.app_context():
        for n in range(2):
            db.session.add(TimeEntry(matter_id=1, user_id=1, date=date.today(), minutes=2,
                                     rate_cents=35000, description=f'Entry {n}', billable=True))
        db.session.commit()
        expected = sum(e.amount_cents for e in TimeEntry.query.all())
    c, _ = staff(app)
    contexts = []
    def capture(sender, template, context, **extra):
        contexts.append(context)
    with template_rendered.connected_to(capture, app):
        assert c.get('/time?matter_id=1').status_code == 200
    assert contexts[-1]['total_amount'] == expected, f'Table total {contexts[-1]["total_amount"]}, row sum {expected}'


def test_public_intake_allows_its_advertised_iframe(app):
    r = app.test_client().get('/intake/form')
    assert r.status_code == 200
    assert r.headers.get('X-Frame-Options', '').upper() not in ('DENY', 'SAMEORIGIN'), dict(r.headers)


def test_portal_unshared_document_cannot_be_downloaded(app, tmp_path):
    from app.extensions import db
    from app.models import Document
    p = tmp_path / 'synthetic.txt'
    p.write_text('Synthetic confidential record')
    with app.app_context():
        d = Document(matter_id=1, name='record.txt', path=str(p), mime='text/plain', shared_to_portal=False)
        db.session.add(d)
        db.session.commit()
        did = d.id
    c = app.test_client()
    with c.session_transaction() as session:
        session['portal_contact_id'] = 1
    assert c.get(f'/portal/documents/{did}/download').status_code in (403, 404)


def test_expired_magic_link_does_not_log_in(app):
    from app.extensions import db
    from app.models import PortalToken, now
    with app.app_context():
        token = PortalToken(contact_id=1, expires_at=now() - timedelta(seconds=1))
        db.session.add(token)
        db.session.commit()
        value = token.token
    c = app.test_client()
    assert c.get(f'/portal/auth/{value}').status_code == 410
    with c.session_transaction() as session:
        assert 'portal_contact_id' not in session


@pytest.mark.parametrize('failure', ['restart', 'backup_while_pinned', 'healthy_update', 'holding_failed_build'])
def test_self_update_preserves_rollback_on_command_failure(tmp_path, failure):
    """Execute the actual updater with fake local Docker/curl, never a real daemon."""
    root = tmp_path / 'install'
    root.mkdir()
    (root / 'data').mkdir()
    (root / 'docker-compose.yml').write_text('services:\n  coil:\n    image: synthetic:stable\n')
    override = root / 'docker-compose.override.yml'
    if failure != 'restart':
        override.write_text('services:\n  coil:\n    image: sha256:old\n')
        (root / 'data' / '.update-bad').write_text('sha256:new' if failure == 'holding_failed_build' else 'sha256:bad')
    bindir = tmp_path / 'bin'
    bindir.mkdir()
    fake = bindir / 'docker'
    fake.write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$COIL_DIR/docker-calls.log"
case "$*" in
  "compose version") exit 0 ;;
  "compose images -q coil") echo sha256:old; exit 0 ;;
  "pull -q synthetic:stable") echo sha256:new; exit 0 ;;
  "image inspect "*) echo sha256:new; exit 0 ;;
  "compose exec "*) [ "$REVIEW_FAILURE" = backup_while_pinned ] && exit 42; exit 0 ;;
  "compose up -d") [ "$REVIEW_FAILURE" = healthy_update ] && exit 0; [ -f "$COIL_DIR/docker-compose.override.yml" ] && exit 0; exit 42 ;;
esac
exit 70
''')
    fake.chmod(0o755)
    curl = bindir / 'curl'
    curl.write_text('#!/bin/sh\nprintf 200\n')
    curl.chmod(0o755)
    env = dict(os.environ, PATH=str(bindir) + os.pathsep + os.environ['PATH'], COIL_DIR=str(root),
               REVIEW_FAILURE=failure, COIL_HEALTH_DEADLINE='3')
    script = Path(__file__).resolve().parents[1] / 'ops' / 'self-update.sh'
    result = subprocess.run(['sh', str(script)], env=env, capture_output=True, text=True, timeout=10)
    calls = (root / 'docker-calls.log').read_text()
    if failure == 'healthy_update':
        assert result.returncode == 0 and not override.exists(), result.stdout
        assert 'compose exec' in calls and calls.count('compose up -d') == 1
        assert not (root / 'data' / '.update-bad').exists()
    elif failure == 'holding_failed_build':
        assert result.returncode == 0 and override.exists(), result.stdout
        assert 'compose exec' not in calls and 'compose up -d' not in calls
    else:
        assert result.returncode != 0
        assert override.exists() and 'sha256:old' in override.read_text(), result.stdout
        if failure == 'restart':
            assert calls.count('compose up -d') == 2
        else:
            assert 'compose up -d' not in calls


def test_webhook_retries_wait_then_stop_at_limit(app, monkeypatch):
    from types import SimpleNamespace
    from app.blueprints.webhooks_out import attempt_delivery, due_for_retry, MAX_ATTEMPTS
    from app.models import Webhook, WebhookDelivery, now
    monkeypatch.setattr('app.blueprints.webhooks_out.requests.post', lambda *a, **k: SimpleNamespace(status_code=500))
    with app.app_context():
        hook = Webhook(url='https://example.test/hook', secret='synthetic', events='task.completed')
        d = WebhookDelivery(id=1, event='task.completed', payload_json='{}', attempts=0)
        for n in range(MAX_ATTEMPTS):
            assert attempt_delivery(d, hook) is False
            assert d.attempts == n + 1
            assert due_for_retry(d, at=d.last_at) is False
            assert due_for_retry(d, at=d.last_at + timedelta(days=1)) == (n + 1 < MAX_ATTEMPTS)
        assert d.status == 'failed' and d.last_error == 'HTTP 500'


@pytest.mark.parametrize('report', ['ar-aging', 'wip', 'revenue', 'trust-balances', 'productivity',
                                    'origination', 'realization', 'profitability', 'compensation'])
def test_each_report_has_an_actual_csv_response(app, report):
    c, _ = staff(app)
    r = c.get(f'/reports/{report}?format=csv')
    assert r.status_code == 200
    assert r.mimetype == 'text/csv'
    assert 'attachment;' in r.headers['Content-Disposition']
    assert '<html' not in r.get_data(as_text=True).lower()


def test_unsigned_twilio_webhook_cannot_forge_client_message(app):
    from app.extensions import db
    from app.models import Contact, Message
    app.config['TWILIO_AUTH_TOKEN'] = 'synthetic-auth-token'
    with app.app_context():
        db.session.get(Contact, 1).phone = '+15550001111'
        db.session.commit()
    r = app.test_client().post('/webhooks/twilio', data={
        'From': '+15550001111', 'To': '+15550002222', 'MessageSid': 'SM-synthetic-review',
        'Body': 'Synthetic message that was never sent by this client'})
    with app.app_context():
        forged = Message.query.filter_by(contact_id=1, provider_id='SM-synthetic-review').count()
        assert r.status_code in (400, 403) and forged == 0, f'HTTP {r.status_code}, forged messages={forged}'


def test_failed_document_signature_email_does_not_claim_delivery(app, tmp_path, monkeypatch):
    from app.extensions import db
    from app.models import Document, DocumentSignature
    p = tmp_path / 'synthetic.txt'
    p.write_text('Synthetic document to sign')
    monkeypatch.setattr('app.blueprints.signatures.send_email', lambda *a, **k: False)
    with app.app_context():
        d = Document(matter_id=1, name='record.txt', path=str(p), mime='text/plain')
        db.session.add(d)
        db.session.flush()
        s = DocumentSignature(document_id=d.id, contact_id=1, title='Review signature', status='draft')
        db.session.add(s)
        db.session.commit()
        sid = s.id
    c, csrf = staff(app)
    c.post(f'/signatures/{sid}/send', data={'_csrf': csrf})
    with c.session_transaction() as session:
        flashes = session.get('_flashes', [])
    assert any(kind == 'error' or 'failed' in msg.lower() for kind, msg in flashes), flashes


@pytest.mark.parametrize('case', ['empty', 'over_limit', 'at_limit', 'plain_text_named_pdf'])
def test_document_file_boundaries_and_type_validation(app, case):
    from app.blueprints.documents import store_bytes, MAX_BYTES
    size = {'empty': 0, 'over_limit': MAX_BYTES + 1, 'at_limit': MAX_BYTES,
            'plain_text_named_pdf': 50}[case]
    name = 'not-a-pdf.pdf' if case == 'plain_text_named_pdf' else 'synthetic.txt'
    with app.app_context():
        doc, error = store_bytes(1, name, b'x' * size, user_id=1)
        if case == 'at_limit':
            assert doc is not None and error is None
        else:
            assert doc is None and error, f'{case}: invalid file was accepted as {doc.mime}'
