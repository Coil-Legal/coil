"""Per-firm tool switches.

Every firm runs the same Coil. What makes one firm's Coil its own is which tools are on,
chosen on Settings > Tools and stored on the firm. These tests hold the promises that page
makes: a switched-off tool leaves the menu, the dashboard and the matter tabs and its pages
close; nothing is deleted; links already sent to clients keep working; the tools a firm
cannot run without cannot be switched off; and a firm that never opens the page sees
exactly what it saw before.

Run: .venv/bin/python -m pytest tests/test_firm_tools.py -q
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_firm_tools.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOAD_DIR = os.path.join(ROOT, "data", "uploads", "test_firm_tools")
PDF_DIR = os.path.join(ROOT, "data", "pdf", "test_firm_tools")

from tests.helpers import login  # noqa: E402

ALL_ON = None  # sentinel for "every tool at its default"


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    shutil.rmtree(UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(PDF_DIR, ignore_errors=True)
    env = dict(os.environ, DATABASE_URL=DB_URI, STRIPE_SECRET_KEY="", STRIPE_WEBHOOK_SECRET="", SMTP_HOST="")
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "UPLOAD_DIR": UPLOAD_DIR, "PDF_DIR": PDF_DIR,
                       "TESTING": True, "STRIPE_SECRET_KEY": "", "STRIPE_WEBHOOK_SECRET": "", "SMTP_HOST": ""})


@pytest.fixture(scope="module")
def owner(app):
    c = app.test_client()
    c._csrf = login(c)
    return c


@pytest.fixture(autouse=True)
def reset_tools(app):
    """Each test starts from a firm that has never touched Settings > Tools."""
    from app.extensions import db
    from app.models import Firm
    with app.app_context():
        Firm.get().tool_overrides = "{}"
        db.session.commit()
    yield


def switch(c, on=None, off=()):
    """Post the Tools form as a browser would: every box ticked except the ones in ``off``."""
    from app.tools import TOOLS
    keys = set(TOOLS) if on is None else set(on)
    keys -= set(off)
    data = {f"tool_{k}": "1" for k in keys}
    data["_csrf"] = c._csrf
    return c.post("/settings/tools", data=data, follow_redirects=True)


def stored(app):
    from app.models import Firm
    with app.app_context():
        return json.loads(Firm.get().tool_overrides or "{}")


def menu(c):
    return c.get("/").data.decode()


# ------------------------------------------------------------------ nothing changes by default
def test_a_firm_that_never_opens_the_page_sees_everything(app, owner):
    page = menu(owner)
    for label in ("Personal injury", "Invoices", "Trust accounting", "Voice line", "Time suggestions"):
        assert label in page
    assert stored(app) == {}


def test_every_tool_page_opens_by_default(owner):
    for path in ("/pi", "/invoices", "/trust", "/time", "/tasks", "/calendar", "/intake"):
        assert owner.get(path).status_code != 404, path


# ------------------------------------------------------------------ switching one off
def test_a_switched_off_tool_leaves_the_menu_and_its_pages_close(app, owner):
    r = switch(owner, off=["pi"])
    assert "Switched off: Personal injury" in r.data.decode()
    assert "Personal injury" not in menu(owner)
    r = owner.get("/pi")
    assert r.status_code == 404
    assert "switched off for this firm" in r.data.decode()


def test_the_owner_is_told_where_to_switch_it_back_on(owner):
    switch(owner, off=["pi"])
    body = owner.get("/pi").data.decode()
    assert "/settings/tools" in body and "still there" in body


def test_only_the_difference_from_the_default_is_stored(app, owner):
    """A tool added in a later release must arrive at its own default, not inherit a snapshot."""
    switch(owner, off=["pi"])
    assert stored(app) == {"pi": False}
    switch(owner)
    assert stored(app) == {}


def test_nothing_is_deleted_and_switching_back_restores_the_page(app, owner):
    from app.models import Invoice
    with app.app_context():
        before = Invoice.query.count()
    switch(owner, off=["invoices"])
    assert owner.get("/invoices").status_code == 404
    with app.app_context():
        assert Invoice.query.count() == before, "switching a tool off must never delete its records"
    switch(owner)
    assert owner.get("/invoices").status_code == 200


def test_the_change_is_in_the_audit_log(app, owner):
    switch(owner, off=["criminal", "research"])
    from app.models import AuditLog
    with app.app_context():
        row = AuditLog.query.filter_by(action="tools_changed").order_by(AuditLog.id.desc()).first()
        assert row is not None
        assert "Criminal defense" in row.detail and "Research" in row.detail


# ------------------------------------------------------------------ the finer points
def test_a_sub_tool_can_be_off_while_its_parent_stays_on(owner):
    """Longest prefix wins: /time/suggestions belongs to its own switch, not to /time."""
    switch(owner, off=["time_suggestions"])
    assert owner.get("/time").status_code == 200
    assert owner.get("/time/suggestions").status_code == 404
    page = menu(owner)
    assert "Time &amp; expenses" in page and "Time suggestions" not in page


def test_switching_off_a_tool_also_switches_off_what_depends_on_it(app, owner):
    """Payments and plans without invoices would be pages pointing at nothing."""
    r = switch(owner, off=["invoices"])
    body = r.data.decode()
    assert "Still off because a tool they rely on is off: " in body
    assert "Switched off: Invoices." in body, "the dependents are named once, as held, not twice"
    assert owner.get("/payments").status_code == 404
    assert owner.get("/money/plans").status_code == 404
    # The firm's own ticks are kept, so switching invoices back on brings them straight back.
    assert stored(app) == {"invoices": False}
    switch(owner)
    assert owner.get("/payments").status_code == 200


def test_an_old_held_tool_is_not_repeated_on_an_unrelated_later_save(owner):
    """Invoices off holds Payments and Plans off, reported once. A later save that only touches an
    unrelated tool (Time suggestions) must not repeat that held notice: nothing about Payments or
    Plans changed in this save, so it is not news."""
    switch(owner, off=["invoices"])
    r = switch(owner, off=["invoices", "time_suggestions"])
    body = r.data.decode()
    assert "Switched off: Time suggestions." in body
    assert "Still off because" not in body


def test_the_money_heading_goes_when_every_money_tool_is_off(owner):
    switch(owner, off=["invoices", "statements", "trust", "accounting", "reports", "payments", "plans"])
    assert '<div class="sec">Money</div>' not in menu(owner)


def test_core_tools_cannot_be_switched_off(owner):
    """Contacts, matters, settings and exports are what a firm needs to run and to leave."""
    r = owner.post("/settings/tools", data={"_csrf": owner._csrf, "tool_contacts": ""}, follow_redirects=True)
    assert r.status_code == 200
    for path in ("/contacts", "/matters", "/settings", "/exports"):
        assert owner.get(path).status_code == 200, path


# ------------------------------------------------------------------ what never closes
def test_links_already_sent_to_clients_keep_working(app, owner):
    """A client with a public invoice link was promised it. The switch is about staff screens."""
    from datetime import date
    from app.extensions import db
    from app.models import Invoice, InvoiceLine, Matter
    with app.app_context():
        m = Matter.query.first()
        inv = Invoice(number="QA-TOOLS-1", matter_id=m.id, client_id=m.client_id, status="sent",
                      issued_on=date.today())
        db.session.add(inv)
        db.session.flush()
        db.session.add(InvoiceLine(invoice_id=inv.id, description="QA tools", amount_cents=1000, kind="fee"))
        inv.recalc()
        db.session.commit()
        token = inv.public_token
    assert app.test_client().get(f"/p/{token}").status_code == 200, "the link works before the switch"
    switch(owner, off=["invoices"])
    assert app.test_client().get(f"/p/{token}").status_code == 200, "and still works after it"


def test_incoming_webhooks_are_never_closed(app, owner):
    """Twilio still posts while Messages is off. Its own checks answer, not the switch."""
    switch(owner, off=["messages"])
    r = app.test_client().post("/webhooks/twilio", data={"From": "+15125550100", "Body": "hi"})
    assert b"switched off for this firm" not in r.data


def test_switching_off_intake_closes_the_public_intake_form(app, owner):
    switch(owner, off=["intake"])
    assert app.test_client().get("/intake/form").status_code == 404


# ------------------------------------------------------------------ everywhere else it shows
def test_dashboard_cards_for_switched_off_tools_disappear(owner):
    switch(owner, off=["invoices", "time"])
    page = menu(owner)
    assert "Outstanding A/R" not in page
    assert "Log time" not in page and "Start timer" not in page


def test_the_conflict_check_button_leaves_the_contact_page_when_off(app, owner):
    """Settings > Tools hides /conflicts and its sidebar link; the same switch must take the
    shortcut button on a contact's own page with it, or a click lands on a 404."""
    from app.models import Contact
    with app.app_context():
        cid = Contact.query.first().id
    assert "Conflict check</a>" in owner.get(f"/contacts/{cid}").data.decode()
    switch(owner, off=["conflicts"])
    page = owner.get(f"/contacts/{cid}").data.decode()
    assert "Conflict check</a>" not in page
    switch(owner)
    assert "Conflict check</a>" in owner.get(f"/contacts/{cid}").data.decode()


def test_the_request_signature_link_leaves_the_documents_list_when_off(app, owner):
    """Same promise for the Signatures switch: the per-row shortcut on /documents must not
    point at a tool whose own page now 404s."""
    from app.extensions import db
    from app.models import Document, Matter
    with app.app_context():
        m = Matter.query.first()
        db.session.add(Document(matter_id=m.id, name="QA-TOOLS.pdf", path="qa-tools.pdf", mime="application/pdf"))
        db.session.commit()
    assert "Request signature</a>" in owner.get("/documents").data.decode()
    switch(owner, off=["signatures"])
    page = owner.get("/documents").data.decode()
    assert "Request signature</a>" not in page
    switch(owner)
    assert "Request signature</a>" in owner.get("/documents").data.decode()


def test_matter_tabs_follow_the_switches(app, owner):
    from app.models import Matter
    with app.app_context():
        mid = Matter.query.first().id
    switch(owner, off=["invoices", "trust"])
    page = owner.get(f"/matters/{mid}").data.decode()
    assert f"/matters/{mid}?tab=invoices" not in page
    assert f"/matters/{mid}?tab=trust" not in page
    assert f"/matters/{mid}?tab=tasks" in page
    # Asking for a closed tab by URL lands on the overview rather than an error.
    assert owner.get(f"/matters/{mid}?tab=invoices").status_code == 200


# ------------------------------------------------------------------ who may change it
def test_only_the_owner_can_open_the_tools_page(app):
    from app.extensions import db
    from app.models import User
    with app.app_context():
        if not User.query.filter_by(email="para-tools@example.test").first():
            u = User(email="para-tools@example.test", name="QA Paralegal Tools", role="paralegal", initials="QP")
            u.set_password("password123")
            db.session.add(u)
            db.session.commit()
    c = app.test_client()
    login(c, email="para-tools@example.test")
    assert c.get("/settings/tools").status_code == 403


def test_staff_are_told_to_ask_the_owner(app, owner):
    switch(owner, off=["pi"])
    c = app.test_client()
    login(c, email="para-tools@example.test")
    body = c.get("/pi").data.decode()
    assert "Ask the firm owner" in body
    assert "/settings/tools" not in body


# ------------------------------------------------------------------ the request-a-feature path
def test_a_new_tool_can_ship_switched_off_for_everyone(app, owner, monkeypatch):
    """How one firm's request reaches every firm without being forced on any of them."""
    from app import tools
    optional = tools.Tool("qa_optional", "QA optional tool", "Work", "Built for one firm.", ["/qa-optional"],
                          default_on=False)
    monkeypatch.setitem(tools.TOOLS, "qa_optional", optional)
    monkeypatch.setattr(tools, "_PREFIXES",
                        sorted(tools._PREFIXES + [("/qa-optional", "qa_optional")], key=lambda x: -len(x[0])))
    with app.test_request_context():
        from app.models import Firm
        assert tools.enabled_map(Firm.get())["qa_optional"] is False, "off for every firm until asked for"
    switch(owner, on=list(tools.TOOLS))
    assert stored(app) == {"qa_optional": True}, "the firm that asked switches it on for itself"


def test_bad_stored_data_falls_back_to_every_tool_on(app, owner):
    from app.extensions import db
    from app.models import Firm
    with app.app_context():
        Firm.get().tool_overrides = "not json"
        db.session.commit()
    assert "Personal injury" in menu(owner)


def test_an_unknown_key_never_hides_anything(app):
    from app.tools import tool_enabled
    with app.test_request_context():
        assert tool_enabled("no_such_tool") is True
