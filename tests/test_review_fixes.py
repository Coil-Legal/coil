"""Regression checks for the independent review, using disposable data and fake delivery."""
import hashlib
import hmac
import json
import time
from datetime import date, timedelta

import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    for key in ('DATABASE_URL', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'SMTP_HOST'):
        monkeypatch.delenv(key, raising=False)
    from app import create_app
    from app.extensions import db
    from app.models import User, Contact, Matter, Invoice, InvoiceLine, Firm
    from app.blueprints.api import reset_rate_limits
    reset_rate_limits()
    a = create_app({'TESTING': True, 'SECRET_KEY': 'isolated-review',
                    'SQLALCHEMY_DATABASE_URI': f'sqlite:///{tmp_path}/review.db',
                    'UPLOAD_DIR': str(tmp_path / 'uploads'), 'PDF_DIR': str(tmp_path / 'pdf'),
                    'STRIPE_SECRET_KEY': '', 'STRIPE_WEBHOOK_SECRET': '', 'SMTP_HOST': ''})
    with a.app_context():
        Firm.get()
        for role in ('owner', 'attorney', 'paralegal', 'billing', 'readonly'):
            u = User(email=f'{role}@example.test', name=role, role=role)
            u.set_password('review-password')
            db.session.add(u)
        c = Contact(first_name='Synthetic', last_name='Client', is_client=True, email='client@example.test')
        db.session.add(c)
        db.session.flush()
        m = Matter(number='M-REVIEW', name='Synthetic matter', client_id=c.id, status='open')
        db.session.add(m)
        db.session.flush()
        inv = Invoice(number='INV-REVIEW', matter_id=m.id, client_id=c.id, status='draft',
                      total_cents=10000, subtotal_cents=10000, issued_on=date.today(), due_on=date.today())
        inv.lines.append(InvoiceLine(kind='flat', description='Synthetic services', amount_cents=10000,
                                     unit_cents=10000, quantity=1))
        db.session.add(inv)
        db.session.commit()
    yield a
    with a.app_context():
        db.session.remove()
        db.engine.dispose()


def staff(app, role='owner'):
    from tests.helpers import login
    c = app.test_client()
    csrf = login(c, f'{role}@example.test', 'review-password')
    return c, csrf


def test_stripe_requires_configuration_and_valid_signature(app):
    from app.extensions import db
    from app.models import Firm, Payment, TrustTransaction
    c = app.test_client()
    body = json.dumps({'type': 'review.noop', 'data': {'object': {}}})
    assert c.post('/webhooks/stripe', data=body, content_type='application/json').status_code == 503
    with app.app_context():
        Firm.get().integration_json = json.dumps({'STRIPE_WEBHOOK_SECRET': 'whsec_review'})
        db.session.commit()
    assert c.post('/webhooks/stripe', data=body, content_type='application/json').status_code == 400
    stamp = str(int(time.time()))
    digest = hmac.new(b'whsec_review', f'{stamp}.{body}'.encode(), hashlib.sha256).hexdigest()
    headers = {'Stripe-Signature': f't={stamp},v1={digest}'}
    assert c.post('/webhooks/stripe', data=body, content_type='application/json', headers=headers).status_code == 200
    headers['Stripe-Signature'] = f't={stamp},v1=invalid'
    assert c.post('/webhooks/stripe', data=body, content_type='application/json', headers=headers).status_code == 400
    with app.app_context():
        assert Payment.query.count() == TrustTransaction.query.count() == 0


def test_token_issuance_omits_forbidden_scopes(app):
    from app.models import ApiToken
    c, csrf = staff(app, 'paralegal')
    page = c.get('/settings/api').get_data(as_text=True)
    assert 'value="invoices:read"' not in page
    assert 'value="time:write"' in page
    c.post('/settings/api', data={'_csrf': csrf, 'name': 'review', 'scopes': 'invoices:read'})
    with app.app_context():
        assert ApiToken.query.count() == 0


def test_existing_token_follows_changed_role_in_rest_and_mcp(app):
    from app.extensions import db
    from app.models import User
    from app.blueprints.api import create_token
    with app.app_context():
        u = User.query.filter_by(role='attorney').one()
        token, raw = create_token(u, 'review', 'invoices:read,invoices:write,time:write')
        db.session.commit()
        u.role = 'paralegal'
        db.session.commit()
    c = app.test_client()
    headers = {'Authorization': f'Bearer {raw}'}
    assert c.get('/api/v1/invoices', headers=headers).status_code == 403
    assert c.post('/api/v1/invoices', headers=headers, json={}).status_code == 403
    me = c.get('/api/v1/me', headers=headers).get_json()
    assert me['token']['scopes'] == ['time:write']
    tools = c.post('/mcp', headers=headers, json={'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}).get_json()
    assert 'list_invoices' not in {t['name'] for t in tools['result']['tools']}
    assert 'draft_invoice' not in {t['name'] for t in tools['result']['tools']}


@pytest.mark.parametrize('role', ['owner', 'paralegal'])
def test_deactivation_revokes_browser_reads_and_writes(app, role):
    from app.extensions import db
    from app.models import User, ApiToken
    c, csrf = staff(app, role)
    with app.app_context():
        User.query.filter_by(role=role).one().is_active = False
        db.session.commit()
    # Exercise the write before the read clears the cookie.
    r = c.post('/settings/api', data={'_csrf': csrf, 'name': 'disabled'})
    assert r.status_code == 302 and '/login' in r.location
    r = c.get('/contacts')
    assert r.status_code == 302 and '/login' in r.location
    with c.session_transaction() as s:
        assert 'user_id' not in s
    with app.app_context():
        assert ApiToken.query.count() == 0


def test_merge_environment_keeps_fields_and_blocks_object_access():
    from app.merge_templates import MergeEnvironment
    from jinja2 import TemplateError
    for autoescape in (True, False):
        env = MergeEnvironment(autoescape=autoescape)
        assert env.globals == {}
        assert not env.is_safe_callable(str)
        assert not env.is_safe_attribute('text', 'upper', str.upper)
        assert env.from_string('{{ client_name|upper }}').render(client_name='Ada') == 'ADA'
        with pytest.raises(TemplateError):
            env.from_string('{{ client_name.upper() }}')


def test_invalid_saved_engagement_template_is_reported_without_creating_letter(app):
    from app.extensions import db
    from app.models import LetterTemplate, Engagement
    with app.app_context():
        t = LetterTemplate(name='Legacy method call', kind='engagement',
                           subject='Review', body_html='{{ client_name.upper() }}')
        db.session.add(t)
        db.session.commit()
        tid = t.id
    c, csrf = staff(app)
    r = c.post('/engagements/new', data={'_csrf': csrf, 'matter_id': 1, 'template_id': tid, 'action': 'draft'})
    assert r.status_code == 200 and b'Template error' in r.data
    with app.app_context():
        assert Engagement.query.count() == 0


def trust_entry(c, csrf, kind, amount, day, matter=1):
    return c.post('/trust/new', data={'_csrf': csrf, 'type': kind, 'client_id': 1,
        'matter_id': matter or '', 'amount': amount, 'date': day.isoformat(), 'description': 'Test',
        'fee_reason': 'Synthetic earned fee'})


@pytest.mark.parametrize('kind', ['disbursement', 'refund', 'bank_fee', 'firm_fee'])
@pytest.mark.parametrize('matter', [1, None])
def test_backdated_debit_preserves_later_balances(app, kind, matter):
    from app.models import TrustTransaction
    c, csrf = staff(app)
    today = date.today()
    assert trust_entry(c, csrf, 'deposit', '100', today - timedelta(days=3), matter).status_code == 302
    assert trust_entry(c, csrf, kind, '80', today - timedelta(days=1), matter).status_code == 302
    # A later deposit covers the final balance, but cannot cure an earlier shortfall.
    assert trust_entry(c, csrf, 'deposit', '100', today, matter).status_code == 302
    r = trust_entry(c, csrf, kind, '80', today - timedelta(days=2), matter)
    assert r.status_code == 200 and b'Later transactions' in r.data
    with app.app_context():
        assert TrustTransaction.query.count() == 3
    assert trust_entry(c, csrf, kind, '20', today - timedelta(days=2), matter).status_code == 302


def test_backdated_transfer_cannot_spend_funds_needed_by_later_entry(app):
    from app.extensions import db
    from app.models import Matter, TrustTransaction
    c, csrf = staff(app)
    with app.app_context():
        m = Matter(number='M-SECOND', name='Second matter', client_id=1)
        db.session.add(m)
        db.session.commit()
        mid = m.id
    today = date.today()
    trust_entry(c, csrf, 'deposit', '100', today - timedelta(days=3))
    trust_entry(c, csrf, 'disbursement', '80', today - timedelta(days=1))
    r = c.post('/trust/transfer', data={'_csrf': csrf, 'client_id': 1, 'from_matter_id': 1,
        'to_matter_id': mid, 'date': (today - timedelta(days=2)).isoformat(), 'amount': '80',
        'authorized_by': 'Synthetic client'})
    assert r.status_code == 200 and b'Later transactions' in r.data
    with app.app_context():
        assert TrustTransaction.query.count() == 2


def test_applying_trust_preserves_future_withdrawal(app):
    from app.extensions import db
    from app.models import Invoice, Payment, TrustTransaction
    c, csrf = staff(app)
    trust_entry(c, csrf, 'deposit', '100', date.today())
    trust_entry(c, csrf, 'disbursement', '80', date.today() + timedelta(days=1))
    with app.app_context():
        db.session.get(Invoice, 1).status = 'sent'
        db.session.commit()
    c.post('/trust/apply', data={'_csrf': csrf, 'invoice_id': 1, 'amount': '80'})
    with app.app_context():
        assert Payment.query.count() == 0
        assert TrustTransaction.query.count() == 2


def test_invoice_mail_failure_preserves_draft_and_allows_retry(app, monkeypatch):
    from app.extensions import db
    from app.models import Invoice, InvoiceEvent
    from app.blueprints import invoices
    c, csrf = staff(app)
    monkeypatch.setattr(invoices, 'send_email', lambda *a, **kw: False)
    r = c.post('/invoices/1/send', data={'_csrf': csrf}, follow_redirects=True)
    assert b'could not be delivered' in r.data
    with app.app_context():
        assert db.session.get(Invoice, 1).status == 'draft'
        assert InvoiceEvent.query.filter_by(event='sent').count() == 0
    monkeypatch.setattr(invoices, 'send_email', lambda *a, **kw: True)
    c.post('/invoices/1/send', data={'_csrf': csrf})
    with app.app_context():
        assert db.session.get(Invoice, 1).status == 'sent'
        assert InvoiceEvent.query.filter_by(event='sent').count() == 1


def test_invoice_failure_does_not_depend_on_callers_rollback(app, monkeypatch):
    from app.extensions import db
    from app.models import Invoice
    from app.blueprints import invoices
    monkeypatch.setattr(invoices, 'send_email', lambda *a, **kw: False)
    with app.app_context():
        inv = db.session.get(Invoice, 1)
        assert invoices._send_invoice_email(inv)
        db.session.commit()
        assert inv.status == 'draft' and inv.sent_at is None and not inv.sent_to


def test_failed_scheduled_invoice_reminder_is_retryable(app, monkeypatch):
    from app.extensions import db
    from app.models import Invoice, InvoiceEvent, AuditLog
    from app import cli
    with app.app_context():
        inv = db.session.get(Invoice, 1)
        inv.status = 'sent'
        inv.due_on = date.today() - timedelta(days=7)
        db.session.commit()
        monkeypatch.setattr(cli, 'send_email', lambda *a, **kw: False)
        assert cli.run_reminders() == (0, 0)
        assert InvoiceEvent.query.filter_by(event='reminder').count() == 0
        assert AuditLog.query.filter_by(action='reminder_sent').count() == 0
        monkeypatch.setattr(cli, 'send_email', lambda *a, **kw: True)
        assert cli.run_reminders() == (1, 0)
        assert cli.run_reminders() == (0, 0)


@pytest.mark.parametrize('role,billing,trust', [
    ('owner', True, True), ('attorney', True, False), ('paralegal', False, False),
    ('billing', True, True), ('readonly', True, False)])
def test_dashboard_respects_roles_and_saved_layouts(app, role, billing, trust):
    from app.extensions import db
    from app.models import TrustTransaction, User
    from app.blueprints.dashboard import CARDS
    with app.app_context():
        db.session.add(TrustTransaction(client_id=1, matter_id=1, date=date.today(),
            type='deposit', amount_cents=12345678))
        User.query.filter_by(role=role).one().dashboard_json = json.dumps(list(CARDS))
        db.session.commit()
    c, csrf = staff(app, role)
    page = c.get('/').get_data(as_text=True)
    assert ('data-card="ar"' in page) == billing
    assert ('data-card="wip"' in page) == billing
    assert ('data-card="trust"' in page) == trust
    assert ('$123,456.78' in page) == trust
    assert ('<th class="num">Trust</th>' in page) == trust
    assert ('<th class="num">Unbilled</th>' in page) == billing
    menu = c.get('/dashboard/customize').get_data(as_text=True)
    assert ('name="card_trust"' in menu) == trust


def test_dashboard_cannot_save_forbidden_card(app):
    from app.models import User
    c, csrf = staff(app, 'paralegal')
    c.post('/dashboard/customize', data={'_csrf': csrf, 'card_trust': '1', 'card_open_matters': '1'})
    with app.app_context():
        assert json.loads(User.query.filter_by(role='paralegal').one().dashboard_json) == ['open_matters']
