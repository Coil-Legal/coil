"""Versioned, per-install configuration. No customer-specific code or executable rules."""
import json
from datetime import timedelta
from sqlalchemy import event, select, inspect
from sqlalchemy.orm import Session, object_session
from .models import Firm, FirmCustomization, Matter, Task, AuditLog, now

NAV = [('dashboard', 'Dashboard', 'Home'), ('intake', 'Intake', 'Clients'), ('intake_pipeline', 'Pipeline', 'Clients'), ('contacts', 'Contacts', 'Clients'), ('matters', 'Matters', 'Clients'), ('conflicts', 'Conflict check', 'Clients'), ('engagements', 'Engagement letters', 'Clients'), ('messages', 'Messages', 'Clients'), ('signatures', 'Signatures', 'Clients'), ('voice', 'Voice line', 'Clients'), ('time', 'Time & expenses', 'Work'), ('time_suggestions', 'Time suggestions', 'Work'), ('tasks', 'Tasks & deadlines', 'Work'), ('calendar', 'Calendar', 'Work'), ('documents', 'Documents', 'Work'), ('doctemplates', 'Document templates', 'Work'), ('ai_search', 'Ask Coil', 'Work'), ('research', 'Research', 'Work'), ('pi', 'Personal injury', 'Work'), ('criminal', 'Criminal defense', 'Work'), ('invoices', 'Invoices', 'Money'), ('statements', 'Client statements', 'Money'), ('payments', 'Payments', 'Money'), ('money_plans', 'Plans & splits', 'Money'), ('trust', 'Trust accounting', 'Money'), ('accounting', 'Accounting', 'Money'), ('reports', 'Reports', 'Money'), ('settings', 'Settings', 'Firm'), ('settings_templates', 'Matter templates', 'Firm'), ('settings_audit', 'Audit log', 'Firm'), ('settings_rules', 'Court rules', 'Firm'), ('import', 'Import from another system', 'Firm'), ('exports', 'Exports', 'Firm'), ('setup-guide', 'Setup guide', 'Firm'), ('features', 'Feature map', 'Firm')]
THEMES = {"blue": "Blue", "forest": "Forest", "plum": "Plum"}
MAX_RULES = 8


def defaults():
    return dict(schema_version=1, theme="blue", density="comfortable", width="standard",
                brand_name="", nav_labels={}, nav_order={}, rules=[])


def decode(raw):
    """Reject unknown versions; never silently rewrite future configurations."""
    value = json.loads(raw or "{}")
    if not isinstance(value, dict) or value.get("schema_version", 1) != 1:
        raise ValueError("This configuration needs a newer version of Coil.")
    result = defaults()
    result.update(value)
    if result["theme"] not in THEMES or result["density"] not in ("comfortable", "compact") or result["width"] not in ("standard", "wide"):
        raise ValueError("Unsupported appearance setting.")
    if not isinstance(result["nav_labels"], dict) or not isinstance(result["nav_order"], dict) or not isinstance(result["rules"], list):
        raise ValueError("Invalid customization settings.")
    return result


def current():
    from .extensions import db
    row = db.session.get(FirmCustomization, 1)
    return decode(row.config_json) if row else defaults()


def nav_order(keys, config):
    return sorted(keys, key=lambda k: (config["nav_order"].get(k, 1000), keys.index(k)))


def from_form(form):
    value = defaults()
    for field, options in (("theme", THEMES), ("density", ("comfortable", "compact")), ("width", ("standard", "wide"))):
        v = form.get(field, defaults()[field])
        if v not in options:
            raise ValueError("Choose an available " + field + ".")
        value[field] = v
    value["brand_name"] = text(form.get("brand_name"), 80, "Brand name")
    for key, label, section in NAV:
        v = text(form.get("label_" + key), 40, "Navigation label")
        if v:
            value["nav_labels"][key] = v
        raw = form.get("order_" + key, "").strip()
        if raw:
            value["nav_order"][key] = integer(raw, 1, 99, "Navigation position")
    for i in range(MAX_RULES):
        prefix = f"rule_{i}_"
        title = text(form.get(prefix + "title"), 200, "Task title")
        enabled = form.get(prefix + "enabled") == "1"
        if not title:
            if enabled:
                raise ValueError("Enabled rules need a task title.")
            continue
        billing = form.get(prefix + "billing", "")
        if billing not in ("", "flat", "hourly", "contingency", "hybrid"):
            raise ValueError("Choose an available billing type.")
        value["rules"].append(dict(enabled=enabled, title=title, billing=billing,
            practice_area=text(form.get(prefix + "practice_area"), 100, "Practice area"),
            offset=integer(form.get(prefix + "offset", "0"), 0, 365, "Task due offset")))
    return value


def text(value, limit, label):
    value = (value or "").strip()
    if len(value) > limit or any(ord(c) < 32 for c in value):
        raise ValueError(f"{label} must be at most {limit} characters without control characters.")
    return value


def integer(value, low, high, label):
    try:
        result = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a whole number from {low} to {high}.")
    if not low <= result <= high:
        raise ValueError(f"{label} must be a whole number from {low} to {high}.")
    return result


@event.listens_for(Matter, "after_insert")
def remember_new_matter(mapper, connection, matter):
    # Imports can autoflush before filling billing/practice fields. Evaluate only
    # once their transaction is ready to commit, after those fields are final.
    session = object_session(matter)
    if session is not None:
        session.info.setdefault("customization_new_matters", set()).add(matter)


@event.listens_for(Session, "before_commit")
def apply_new_matter_workflows(session):
    if session.in_nested_transaction():
        return
    session.flush()
    matters = session.info.pop("customization_new_matters", set())
    for matter in matters:
        if not inspect(matter).deleted:
            create_workflow_tasks(session.connection(), matter)


@event.listens_for(Session, "after_soft_rollback")
def discard_pending_workflows(session, previous_transaction):
    if previous_transaction.parent is None:
        session.info.pop("customization_new_matters", None)
    elif "customization_new_matters" in session.info:
        session.info["customization_new_matters"] = {
            m for m in session.info["customization_new_matters"] if inspect(m).persistent
        }


def create_workflow_tasks(connection, matter):
    """Ordinary tasks in the matter transaction; no external side effects."""
    raw = connection.execute(select(FirmCustomization.config_json).where(FirmCustomization.id == 1)).scalar()
    if not raw:
        return
    config = decode(raw)
    switches = connection.execute(select(Firm.tool_overrides).where(Firm.id == 1)).scalar()
    if json.loads(switches or "{}").get("tasks") is False:
        return
    for rule in config["rules"]:
        if not rule["enabled"] or (rule["billing"] and rule["billing"] != matter.billing_type):
            continue
        if rule["practice_area"] and rule["practice_area"].casefold() != (matter.practice_area or "").strip().casefold():
            continue
        connection.execute(Task.__table__.insert().values(matter_id=matter.id, title=rule["title"],
            kind="task", priority="normal", assignee_id=matter.responsible_user_id,
            due_on=matter.opened_on + timedelta(days=rule["offset"]) if matter.opened_on else None,
            notes="Created by the firm's new-matter workflow.", done=False))
        connection.execute(AuditLog.__table__.insert().values(action="workflow_task", entity="matter",
            entity_id=matter.id, detail="New-matter workflow: " + rule["title"], created_at=now()))
