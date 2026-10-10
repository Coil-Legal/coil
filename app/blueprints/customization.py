"""Owner-managed appearance and new-matter task rules, with safe preview and history."""
import json
from flask import Blueprint, render_template, request, redirect, flash, abort
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import FirmCustomization, CustomizationRevision, audit
from ..helpers import owner_required, current_user
from ..customization import current, defaults, decode, from_form, nav_order, NAV, THEMES, MAX_RULES

bp = Blueprint("customization", __name__)


@bp.app_context_processor
def template_config():
    # Older code must not overwrite newer settings. Keep the shell usable to show errors.
    try:
        config = current()
    except (ValueError, TypeError):
        config = defaults()
    return {"firm_ui": config, "custom_nav_order": nav_order}


def page(config, revision, error=None, preview=False, status=200):
    history = CustomizationRevision.query.order_by(CustomizationRevision.id.desc()).limit(20).all()
    return render_template("settings/customization.html", firm_ui=config, revision=revision,
                           nav_items=NAV, themes=THEMES, max_rules=MAX_RULES,
                           history=history, error=error, preview=preview), status


@bp.route("/settings/customization", methods=["GET", "POST"])
@owner_required
def index():
    row = db.session.get(FirmCustomization, 1)
    revision = row.revision if row else 0
    try:
        config = decode(row.config_json) if row else defaults()
    except (ValueError, TypeError) as exc:
        return page(defaults(), revision, str(exc), status=409)
    if request.method == "GET":
        return page(config, revision)
    try:
        expected = int(request.form.get("revision", ""))
    except ValueError:
        return page(config, revision, "Reload this page before saving.", status=409)
    if expected != revision:
        return page(config, revision, "Settings changed in another session. Review them before saving.", status=409)
    action = request.form.get("action")
    if action not in ("preview", "publish", "restore"):
        abort(400)
    try:
        if action == "restore":
            source = db.session.get(CustomizationRevision, int(request.form.get("restore_revision", "")))
            if not source:
                abort(404)
            candidate = decode(source.config_json)
        else:
            candidate = from_form(request.form)
    except (ValueError, TypeError) as exc:
        return page(config, revision, str(exc), status=400)
    if action == "preview":
        return page(candidate, revision, preview=True)
    raw = json.dumps(candidate, sort_keys=True)
    try:
        if row:
            changed = db.session.execute(update(FirmCustomization).where(
                FirmCustomization.id == 1, FirmCustomization.revision == expected).values(
                    revision=expected + 1, config_json=raw))
            if changed.rowcount != 1:
                db.session.rollback()
                flash("Settings changed in another session. Reload and review before saving.", "error")
                return redirect("/settings/customization")
        else:
            db.session.add(FirmCustomization(id=1, revision=1, config_json=raw))
            db.session.add(CustomizationRevision(id=0, config_json=json.dumps(defaults()),
                                                 user_id=current_user().id, note="Original defaults"))
        note = "Restored revision " + str(source.id) if action == "restore" else "Published"
        db.session.add(CustomizationRevision(id=expected + 1, config_json=raw,
                                             user_id=current_user().id, note=note))
        audit("customization_published", "firm", 1, f"Revision {expected + 1}: {note}", current_user().id)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Settings changed in another session. Reload and review before saving.", "error")
        return redirect("/settings/customization")
    flash("Firm customization published.", "ok")
    return redirect("/settings/customization")
