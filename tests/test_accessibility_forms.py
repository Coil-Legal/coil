"""Issue #97: form fields with no accessible label, including the public intake
form and the client portal. Checks the client-facing templates fixed directly
(real for/id pairs, aria-label on bare filter controls) rather than the generic
app.js label-linking stopgap, which needs a browser to exercise.

Own SQLite file (data/test_accessibility_forms.db), own UPLOAD_DIR.
Run: .venv/bin/python -m pytest tests/test_accessibility_forms.py -q
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_accessibility_forms.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "test_accessibility_forms_uploads")


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    env = dict(os.environ, DATABASE_URL=DB_URI)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    a = create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True, "SMTP_HOST": "",
                    "UPLOAD_DIR": UPLOAD_DIR})
    yield a


def _labelled_ids(html):
    """Every id a <label for="..."> points at."""
    return set(re.findall(r'<label[^>]*\bfor="([^"]+)"', html))


def _control_ids(html):
    return set(re.findall(r'<(?:input|select|textarea)[^>]*\bid="([^"]+)"', html))


def test_public_intake_form_fields_are_all_labelled(app):
    c = app.test_client()
    html = c.get("/intake/form").get_data(as_text=True)
    for field_id in ("in_name", "in_email", "in_phone", "mt", "in_description", "in_adverse_party"):
        assert f'id="{field_id}"' in html, field_id
    labelled = _labelled_ids(html)
    for field_id in ("in_name", "in_email", "in_phone", "mt", "in_description", "in_adverse_party"):
        assert field_id in labelled, field_id
    # Every visible control that carries a label-targetable id is actually targeted,
    # i.e. no id was added to a field without pairing it to a label.
    assert _control_ids(html) <= labelled | {"mt_other"}


def test_portal_upload_form_fields_are_labelled(app):
    from app.extensions import db
    from app.models import Contact, PortalToken
    with app.app_context():
        contact = Contact.query.filter_by(email="maria@example.com").first()
        tok = PortalToken(contact_id=contact.id, expires_at=datetime.utcnow() + timedelta(minutes=30))
        db.session.add(tok)
        db.session.commit()
        token = tok.token
    c = app.test_client()
    r = c.get(f"/portal/auth/{token}")
    assert r.status_code == 302
    html = c.get("/portal").get_data(as_text=True)
    assert 'id="upload_matter_id"' in html and 'for="upload_matter_id"' in html
    assert 'id="upload_file"' in html and 'for="upload_file"' in html


def test_contacts_filter_controls_have_accessible_names(app):
    from tests.helpers import login
    c = app.test_client()
    login(c)
    html = c.get("/contacts").get_data(as_text=True)
    assert 'name="q"' in html and 'aria-label="Search contacts"' in html
    assert 'name="only"' in html and 'aria-label="Filter by client status"' in html


def test_calendar_view_picker_has_an_accessible_name(app):
    from tests.helpers import login
    c = app.test_client()
    login(c)
    html = c.get("/calendar").get_data(as_text=True)
    assert 'aria-label="Calendar view"' in html


def test_matter_apply_template_select_and_upload_file_input_have_accessible_names(app):
    from tests.helpers import login
    from app.extensions import db
    from app.models import Matter, MatterTemplate
    c = app.test_client()
    login(c)
    with app.app_context():
        matter_id = Matter.query.first().id
        if not MatterTemplate.query.filter_by(is_active=True).first():
            db.session.add(MatterTemplate(name="Standard engagement", is_active=True))
            db.session.commit()
    overview_html = c.get(f"/matters/{matter_id}?tab=overview").get_data(as_text=True)
    assert 'name="template_id" aria-label="Apply a template"' in overview_html
    documents_html = c.get(f"/matters/{matter_id}?tab=documents").get_data(as_text=True)
    assert 'name="file" aria-label="Upload a file (25 MB max)"' in documents_html


def test_milestone_due_date_inputs_have_accessible_names(app):
    from tests.helpers import login
    from app.models import Matter
    c = app.test_client()
    login(c)
    with app.app_context():
        matter_id = Matter.query.first().id
    html = c.get(f"/matters/{matter_id}/edit").get_data(as_text=True)
    assert html.count('name="ms_due" aria-label="Milestone due date"') >= 1


def test_payments_month_filter_has_an_accessible_name(app):
    """Issue #120 (QA Bot 2): the /payments month input had no label, id, title
    or aria-label, so axe-core flagged it as `label` (critical)."""
    from tests.helpers import login
    c = app.test_client()
    login(c)
    html = c.get("/payments").get_data(as_text=True)
    assert re.search(r'name="month" value="[^"]*" aria-label="Month"', html)


def test_accounting_ledger_filter_controls_have_accessible_names(app):
    """Same unlabeled-filter pattern as #120, found in the operating ledger's
    month input and account select while fixing the payments page."""
    from tests.helpers import login
    c = app.test_client()
    login(c)
    html = c.get("/accounting/").get_data(as_text=True)
    assert 'name="month"' in html and 'aria-label="Month"' in html
    assert 'name="account_id" aria-label="Filter by account"' in html


def test_matter_custom_field_inputs_have_accessible_names(app):
    """Bot 1's final rescan (case 1458): the new-matter custom field value box sits in a
    table cell with no label the sibling script can reach."""
    from tests.helpers import login
    c = app.test_client()
    login(c)
    html = c.get("/matters/new").get_data(as_text=True)
    assert 'name="cf_key" aria-label="Custom field name"' in html
    assert 'name="cf_value" aria-label="Custom field value"' in html
