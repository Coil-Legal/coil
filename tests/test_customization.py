"""Acceptance regressions for two firms sharing code and isolated persisted settings."""
import json
import sqlite3
from datetime import date

import pytest
from app import create_app
from app.extensions import db
from app.models import (Firm, User, Contact, Matter, Task, FirmCustomization,
                        CustomizationRevision, AuditLog)
from tests.helpers import login


def make_app(path):
    app = create_app(dict(TESTING=True, SECRET_KEY='customization-tests',
        SQLALCHEMY_DATABASE_URI='sqlite:///' + str(path / 'practice.db'),
        UPLOAD_DIR=str(path / 'uploads'), PDF_DIR=str(path / 'pdf'), SMTP_HOST='',
        STRIPE_SECRET_KEY='', TWILIO_AUTH_TOKEN=''))
    with app.app_context():
        if not db.session.get(User, 1):
            owner = User(id=1, email='owner@example.com', name='Owner', role='owner')
            owner.set_password('password123')
            staff = User(id=2, email='staff@example.test', name='Staff', role='attorney')
            staff.set_password('password123')
            db.session.add_all([owner, staff, Firm(id=1, name='Test firm'),
                Contact(id=1, first_name='Test', last_name='Client', is_client=True)])
            db.session.commit()
    return app


@pytest.fixture
def firm(tmp_path):
    a = tmp_path / 'a'; a.mkdir()
    app = make_app(a)
    client = app.test_client(); token = login(client)
    return app, client, token, a


def publish(client, token, revision=0, **values):
    return client.post('/settings/customization', data=dict(_csrf=token, revision=revision,
        action='publish', **values))


def add_matter(app, **values):
    with app.app_context():
        m = Matter(number=values.pop('number', 'M-100'), name='New matter', client_id=1,
                   opened_on=date(2028, 2, 28), responsible_user_id=1, **values)
        db.session.add(m); db.session.commit()
        return m.id


def test_two_firms_preview_publish_and_isolation(firm, tmp_path):
    app, c, token, path = firm
    b = tmp_path / 'b'; b.mkdir(); other = make_app(b)
    c2 = other.test_client(); login(c2)
    r = c.post('/settings/customization', data={'_csrf':token, 'revision':0, 'action':'preview',
        'theme':'forest', 'brand_name':'Defense workspace', 'label_matters':'Cases', 'order_matters':1})
    assert r.status_code == 200
    assert b'firm-theme-forest' in r.data and b'Preview only' in r.data
    assert b'firm-theme-blue' in c.get('/').data
    assert publish(c, token, theme='forest', density='compact', width='wide',
                   brand_name='Defense workspace', label_matters='Cases', order_matters='1').status_code == 302
    page = c.get('/').data
    assert b'firm-theme-forest firm-density-compact firm-width-wide' in page
    assert b'>Cases</a>' in page
    assert page.index(b'href="/matters"') < page.index(b'href="/contacts"')
    assert b'Defense workspace' in page
    assert b'firm-theme-blue' in c2.get('/').data and b'>Cases</a>' not in c2.get('/').data
    with app.app_context():
        assert FirmCustomization.query.one().revision == 1
        assert CustomizationRevision.query.count() == 2
        assert AuditLog.query.filter_by(action='customization_published').count() == 1


def test_owner_only_and_csrf(firm):
    app, c, token, path = firm
    staff = app.test_client(); tok = login(staff, 'staff@example.test')
    assert staff.get('/settings/customization').status_code == 403
    assert publish(staff, tok, theme='forest').status_code == 403
    assert c.post('/settings/customization', data={'action':'publish','revision':0}).status_code == 400


@pytest.mark.parametrize('bad', [{'theme':'<style>'}, {'order_matters':'-1'},
    {'brand_name':'x'*81}, {'rule_0_enabled':'1'},
    {'rule_0_title':'Review', 'rule_0_offset':'999'}, {'rule_0_title':'Review', 'rule_0_billing':'invalid'}])
def test_invalid_configuration_is_atomic(firm, bad):
    app, c, token, path = firm
    assert publish(c, token, **bad).status_code == 400
    with app.app_context():
        assert FirmCustomization.query.count() == 0 and CustomizationRevision.query.count() == 0


def test_labels_escape_markup_and_do_not_bypass_tools(firm):
    app, c, token, path = firm
    assert publish(c, token, label_matters='<script>x</script>', label_criminal='Secret cases').status_code == 302
    with app.app_context():
        Firm.get().tool_overrides = json.dumps({'criminal':False}); db.session.commit()
    page = c.get('/').data
    assert b'&lt;script&gt;x&lt;/script&gt;' in page
    assert b'<script>x</script>' not in page and b'>Secret cases</a>' not in page
    assert c.get('/criminal').status_code == 404


def test_history_restore_and_stale_form(firm):
    app, c, token, path = firm
    publish(c, token, theme='forest')
    assert publish(c, token, revision=0, theme='plum').status_code == 409
    assert publish(c, token, revision=1, theme='plum').status_code == 302
    r=c.post('/settings/customization', data={'_csrf':token,'revision':2,'action':'restore','restore_revision':1})
    assert r.status_code == 302
    with app.app_context():
        assert FirmCustomization.query.one().revision == 3
        assert json.loads(FirmCustomization.query.one().config_json)['theme'] == 'forest'
        assert CustomizationRevision.query.count() == 4


def test_conditional_workflows_are_transactional_and_do_not_repeat(firm):
    app, c, token, path = firm
    publish(c, token, rule_0_enabled='1', rule_0_title='Review intake',
        rule_0_billing='flat', rule_0_practice_area='Criminal defense', rule_0_offset='2')
    mid=add_matter(app, billing_type='flat', practice_area='criminal defense')
    add_matter(app, number='M-101', billing_type='hourly', practice_area='Criminal defense')
    with app.app_context():
        t=Task.query.one(); assert t.matter_id == mid and t.title == 'Review intake'
        assert t.due_on == date(2028,3,1) and t.assignee_id == 1
        m=db.session.get(Matter,mid);m.name='Changed';db.session.commit()
        assert Task.query.count()==1 and AuditLog.query.filter_by(action='workflow_task').count()==1
        m=Matter(number='M-102',name='Rollback',client_id=1,billing_type='flat',practice_area='Criminal defense',opened_on=date(2028,2,28))
        db.session.add(m);db.session.flush();db.session.rollback()
        assert Task.query.count()==1
        Firm.get().tool_overrides=json.dumps({'tasks':False});db.session.commit()
    add_matter(app,number='M-103',billing_type='flat',practice_area='Criminal defense')
    with app.app_context():assert Task.query.count()==1


def test_old_database_upgrade_then_reopen_and_restore(firm, tmp_path):
    app,c,token,path=firm
    # Simulate the prior schema, preserving existing firm and client data.
    with app.app_context():
        db.session.remove()
        CustomizationRevision.__table__.drop(db.engine)
        FirmCustomization.__table__.drop(db.engine)
        db.engine.dispose()
    upgraded=make_app(path)
    cu=upgraded.test_client();tu=login(cu)
    assert publish(cu,tu,theme='plum',rule_0_enabled='1',rule_0_title='Review new matter',rule_0_offset='1').status_code==302
    add_matter(upgraded,billing_type='hourly')
    with upgraded.app_context():db.session.remove();db.engine.dispose()
    reopened=make_app(path)
    cr=reopened.test_client();login(cr)
    assert b'firm-theme-plum' in cr.get('/').data
    dest=tmp_path/'restored';dest.mkdir()
    with sqlite3.connect(path/'practice.db') as source, sqlite3.connect(dest/'practice.db') as target:
        source.backup(target)
    restored=make_app(dest)
    client=restored.test_client();login(client)
    assert b'firm-theme-plum' in client.get('/').data
    with restored.app_context():
        assert Task.query.count()==1
        assert FirmCustomization.query.one().revision==1
        assert db.session.get(Contact,1).last_name=='Client'
    add_matter(restored,number='M-101',billing_type='hourly')
    with restored.app_context():assert Task.query.count()==2


def test_future_schema_cannot_be_overwritten(firm):
    app,c,token,path=firm
    with app.app_context():
        db.session.add(FirmCustomization(id=1, revision=9, config_json='{"schema_version":2}'));db.session.commit()
    assert publish(c,token,revision=9,theme='forest').status_code==409
    with app.app_context():assert FirmCustomization.query.one().revision==9


def test_workflow_uses_final_fields_after_early_import_flush(firm):
    app,c,token,path=firm
    publish(c,token,rule_0_enabled='1',rule_0_title='Hourly review',rule_0_billing='hourly',rule_0_offset='2')
    with app.app_context():
        m=Matter(number='M-early',name='Imported',client_id=1)
        db.session.add(m);db.session.flush()
        m.billing_type='hourly';m.opened_on=date(2028,2,28);m.responsible_user_id=2
        db.session.commit()
        t=Task.query.one()
        assert t.title=='Hourly review' and t.due_on==date(2028,3,1) and t.assignee_id==2
        db.session.commit()
        assert Task.query.count()==1


def test_browser_matter_creation_runs_rule_and_invalid_form_does_not(firm):
    app,c,token,path=firm
    publish(c,token,rule_0_enabled='1',rule_0_title='Review browser matter',rule_0_billing='flat',rule_0_offset='1')
    data=dict(_csrf=token,client_id=1,name='Browser matter',billing_type='flat',
              opened_on='2028-02-29',responsible_user_id=1)
    assert c.post('/matters/new',data=dict(data,client_id='')).status_code==200
    with app.app_context():assert Task.query.count()==0
    assert c.post('/matters/new',data=data).status_code==302
    with app.app_context():
        task=Task.query.one();assert task.title=='Review browser matter' and task.due_on==date(2028,3,1)


def test_import_savepoint_failure_keeps_other_rows_workflows(firm):
    app,c,token,path=firm
    publish(c,token,rule_0_enabled='1',rule_0_title='Imported review',rule_0_billing='hourly')
    with app.app_context():
        with db.session.begin_nested():
            first=Matter(number='M-a',name='Keep',client_id=1,billing_type='hourly',opened_on=date(2028,2,28))
            db.session.add(first);db.session.flush()
        try:
            with db.session.begin_nested():
                second=Matter(number='M-b',name='Reject',client_id=1,billing_type='hourly',opened_on=date(2028,2,28))
                db.session.add(second);db.session.flush()
                raise ValueError('Rejected row')
        except ValueError:
            pass
        db.session.commit()
        assert Matter.query.count()==1
        assert Task.query.one().matter_id==first.id
