"""Settings > Export all firm data: the owner downloads every record, document and setting as one
verified zip (gate C08, offboarding). The package itself is built by app/firm_export.py.

Owner only. /settings is mapped to the settings area in app/permissions.py, so every other role
is refused there before this module runs, and @owner_required refuses it again here.
"""
import os
from flask import Blueprint, render_template, send_file
from ..extensions import db
from ..models import AuditLog, audit
from ..helpers import owner_required, current_user
from ..firm_export import ExportBusy, ExportError, build_lock, export_dir, export_firm, verify_export

bp = Blueprint("offboarding", __name__)


def _page(error=None, status=200):
    recent = (AuditLog.query.filter_by(action="firm_export").order_by(AuditLog.id.desc()).limit(10).all())
    return render_template("settings/export.html", recent=recent, error=error), status


@bp.route("/settings/export", methods=["GET"])
@owner_required
def index():
    return _page()


@bp.route("/settings/export", methods=["POST"])
@owner_required
def download():
    user = current_user()
    try:
        # One build at a time. A second click while the first is running is told so,
        # instead of starting a second copy of the same work.
        with build_lock(export_dir()):
            path = export_firm(producer="web")
            ok, problems, _ = verify_export(path)
            if not ok:
                path.unlink(missing_ok=True)
                raise ExportError("It did not pass its own completeness check: " + "; ".join(problems[:3]))
            # Stream from an open handle and remove the directory entry, so a copy of every
            # client file does not pile up on the server after each download.
            fh = open(path, "rb")
            size = os.fstat(fh.fileno()).st_size
            path.unlink()
    except ExportBusy as e:
        return _page(str(e), 409)
    except ExportError as e:
        return _page(f"The export could not be built. {e}", 500)
    audit("firm_export", "firm", 1, f"full firm export {path.name} ({size} bytes) downloaded", user.id)
    db.session.commit()
    resp = send_file(fh, mimetype="application/zip", as_attachment=True, download_name=path.name, max_age=0)
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["Content-Length"] = str(size)
    return resp
