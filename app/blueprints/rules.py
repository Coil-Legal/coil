"""Court rules: rule sets, deadline day math, holidays, and applying a rule set to a matter.

Mounted without a url_prefix so the settings pages sit at /settings/rules and /settings/holidays (owner gate via
app.permissions) while the apply flow sits at /rules/matters/<id>/apply (any signed-in user).
"""
import calendar
import json
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, Response
from ..extensions import db
from ..models import Holiday, CourtRuleSet, CourtRule, Task, Matter, audit
from ..helpers import login_required, owner_required, current_user, parse_date

bp = Blueprint("rules", __name__)

# "nextmonday": count calendar days, then move to the Monday next after that day (TRCP 99 style answer date).
# "month"/"year": the corresponding date in the later month or year, which is how rules written in months read.
DAY_TYPES = [("calendar", "calendar days"), ("court", "court days (skip weekends and holidays)"),
             ("nextmonday", "calendar days, then the Monday next after"),
             ("month", "months"), ("year", "years")]
# Units counted as whole months rather than days. offset_days holds the count for these.
MONTH_UNITS = {"month": 1, "year": 12}
DIRECTIONS = ["after", "before"]
RULE_KINDS = ["deadline", "court_date", "task"]
GENERIC_NOTE = ("Generic starting point only. Check the current rule text and the local rules of the court before "
                "relying on this date.")


# ---------------------------------------------------------------------------
# Day math
# ---------------------------------------------------------------------------
def _holiday_set(holidays):
    out = set()
    for h in holidays or ():
        d = getattr(h, "date", h)
        if isinstance(d, date):
            out.add(d)
    return out


def is_court_day(d, holidays):
    return d.weekday() < 5 and d not in holidays


def _roll(d, step, holidays):
    while not is_court_day(d, holidays):
        d += timedelta(days=step)
    return d


def add_months(d, n):
    """The corresponding date n months later (or earlier), clamped to the end of the month.

    "Within six months" means the same date six months on. When that date does not exist,
    the majority rule lands on the last day of the target month rather than spilling into
    the next one: New York General Construction Law s 30 and Texas Government Code
    s 311.014(c) both say the period ends with the last day when "there are not that many
    days", and Oregon does the same for a leap-day start.

    Always computed from the trigger, never by repeated addition. Month arithmetic is not
    associative: one month twice from January 31 is March 28, but two months is March 31.
    """
    total = (d.year * 12 + d.month - 1) + n
    y, m = divmod(total, 12)
    m += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _overflow_months(d, n):
    """What the same arithmetic gives if you let the day spill into the next month instead.

    This is the date we did not use. Plain JavaScript and Go both produce it, so it is a
    real reading rather than a hypothetical, and a court could reach it too.
    """
    total = (d.year * 12 + d.month - 1) + n
    y, m = divmod(total, 12)
    m += 1
    last = calendar.monthrange(y, m)[1]
    return date(y, m, last) + timedelta(days=d.day - last) if d.day > last else None


def construction_note(trigger_date, rule):
    """Say so when month arithmetic had to make a choice, and name the date we did not use.

    Silent for trigger days 1 through 28, where nothing is ambiguous. That is the point:
    a warning on every deadline is a warning nobody reads. Two cases actually bite.

    The day does not exist in the target month (January 31 plus one month). We clamp to the
    last day; letting it spill gives a later date.

    The trigger is the last day of its month (February 28 plus one month). We keep the day
    number, so March 28. But 29 CFR 4000.43 runs last day to last day and would say March
    31. This is the case nobody sees coming, and every mainstream date library gets it
    "wrong" against that regulation.

    We take the earlier date in both cases. Filing early is survivable; filing late is not.
    """
    day_type = getattr(rule, "day_type", "calendar") or "calendar"
    if day_type not in MONTH_UNITS:
        return ""
    n = int(getattr(rule, "offset_days", 0) or 0) * MONTH_UNITS[day_type]
    if getattr(rule, "direction", "after") == "before":
        n = -n
    if not n:
        return ""
    ours = add_months(trigger_date, n)
    spill = _overflow_months(trigger_date, n)
    if spill:
        return (f"{trigger_date.isoformat()} has no matching day in that month, so this date is the "
                f"last day of the month ({ours.isoformat()}). Read the other way it would be "
                f"{spill.isoformat()}. Coil takes the earlier date. Check the rule.")
    if trigger_date.day == calendar.monthrange(trigger_date.year, trigger_date.month)[1]:
        y, m = divmod((trigger_date.year * 12 + trigger_date.month - 1) + n, 12)
        m += 1
        last = date(y, m, calendar.monthrange(y, m)[1])
        if last != ours:
            return (f"{trigger_date.isoformat()} is the last day of its month. This date keeps the same "
                    f"day number ({ours.isoformat()}). A last-day-to-last-day reading gives "
                    f"{last.isoformat()}. Coil takes the earlier date. Check the rule.")
    return ""


def compute_deadline(trigger_date, rule, holidays=()):
    """Due date for `rule` counted from `trigger_date`.

    rule needs: offset_days, day_type (calendar | court | nextmonday | month | year), direction, roll (bool).
    Court days skip weekends and holidays. Calendar days count every day and, when the result lands on a weekend or
    holiday and roll is on, move to the next court day (forward for "after", backward for "before").
    Months and years land on the corresponding date, clamped to month end; see add_months and construction_note.
    """
    hol = _holiday_set(holidays)
    offset = int(getattr(rule, "offset_days", 0) or 0)
    day_type = getattr(rule, "day_type", "calendar") or "calendar"
    direction = getattr(rule, "direction", "after") or "after"
    roll = bool(getattr(rule, "roll", True))
    step = -1 if direction == "before" else 1
    if day_type in MONTH_UNITS:
        # Clamp first, then roll. The other order gives different answers.
        d = add_months(trigger_date, step * offset * MONTH_UNITS[day_type])
        if roll and not is_court_day(d, hol):
            d = _roll(d, step, hol)
        return d
    if day_type == "court":
        d, counted = trigger_date, 0
        while counted < offset:
            d += timedelta(days=step)
            if is_court_day(d, hol):
                counted += 1
        if roll and not is_court_day(d, hol):  # only possible when offset is 0
            d = _roll(d, step, hol)
        return d
    d = trigger_date + timedelta(days=step * offset)
    if day_type == "nextmonday":
        d += timedelta(days=(7 - d.weekday()) % 7 or 7)  # strictly after: a Monday moves to the following Monday
        step = 1
    if roll and not is_court_day(d, hol):
        d = _roll(d, step, hol)
    return d


def describe_rule(rule):
    dt = dict(DAY_TYPES).get(rule.day_type, rule.day_type)
    return f"{rule.offset_days} {dt} {rule.direction} {rule.trigger}" + ("" if rule.roll else ", no rolling")


# ---------------------------------------------------------------------------
# US federal holidays, computed in code
# ---------------------------------------------------------------------------
def _nth_weekday(year, month, weekday, n):
    d = date(year, month, 1)
    d += timedelta(days=(weekday - d.weekday()) % 7)
    return d + timedelta(weeks=n - 1)


def _last_weekday(year, month, weekday):
    d = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)
    return d - timedelta(days=(d.weekday() - weekday) % 7)


def _observed(d):
    if d.weekday() == 5:
        return d - timedelta(days=1), True
    if d.weekday() == 6:
        return d + timedelta(days=1), True
    return d, False


def federal_holidays(year):
    """[(date, name)] for the eleven US federal holidays, moved to the observed weekday when they fall on a weekend."""
    fixed = [(date(year, 1, 1), "New Year's Day"), (date(year, 6, 19), "Juneteenth"),
             (date(year, 7, 4), "Independence Day"), (date(year, 11, 11), "Veterans Day"),
             (date(year, 12, 25), "Christmas Day")]
    floating = [(_nth_weekday(year, 1, 0, 3), "Martin Luther King Jr. Day"),
                (_nth_weekday(year, 2, 0, 3), "Presidents Day"),
                (_last_weekday(year, 5, 0), "Memorial Day"),
                (_nth_weekday(year, 9, 0, 1), "Labor Day"),
                (_nth_weekday(year, 10, 0, 2), "Columbus Day"),
                (_nth_weekday(year, 11, 3, 4), "Thanksgiving Day")]
    out = []
    for d, name in fixed:
        od, moved = _observed(d)
        out.append((od, f"{name} (observed)" if moved else name))
    out.extend(floating)
    return sorted(out)


def all_holidays():
    return {h.date for h in Holiday.query.all()}


# ---------------------------------------------------------------------------
# Starter rule sets
# ---------------------------------------------------------------------------
STARTER_SETS = [
    {
        "name": "Federal civil (FRCP), generic", "jurisdiction": "US federal district courts",
        "description": "A generic set of common Federal Rules of Civil Procedure deadlines. It is not complete and is "
                       "not a substitute for reading the rules, the local rules and the judge's standing orders.",
        "rules": [
            ("Service of complaint", "Answer due", 21, "calendar", "after", "deadline"),
            ("Scheduling conference", "Rule 26(f) conference", 21, "calendar", "before", "deadline"),
            ("Rule 26(f) conference", "Initial disclosures due", 14, "calendar", "after", "deadline"),
            ("Service of discovery requests", "Discovery responses due", 30, "calendar", "after", "deadline"),
            ("Service of response brief", "Reply brief due", 14, "calendar", "after", "deadline"),
            ("Entry of judgment", "Notice of appeal due", 30, "calendar", "after", "deadline"),
        ],
    },
    {
        "name": "Texas civil (TRCP), generic", "jurisdiction": "Texas district and county courts",
        "description": "A generic set of common Texas Rules of Civil Procedure deadlines. It is not complete and is "
                       "not a substitute for reading the rules and the local rules of the court.",
        "rules": [
            ("Service of citation", "Answer due (10:00 a.m. on the Monday next after 20 days)", 20, "nextmonday",
             "after", "deadline"),
            ("Service of discovery requests", "Discovery responses due", 30, "calendar", "after", "deadline"),
            ("Signing of judgment", "Motion for new trial due", 30, "calendar", "after", "deadline"),
            ("Signing of judgment", "Notice of appeal due", 30, "calendar", "after", "deadline"),
        ],
    },
]


def ensure_starter_rulesets():
    if CourtRuleSet.query.count():
        return
    for spec in STARTER_SETS:
        rs = CourtRuleSet(name=spec["name"], jurisdiction=spec["jurisdiction"], description=spec["description"])
        for i, (trigger, title, off, dt, direction, kind) in enumerate(spec["rules"]):
            rs.rules.append(CourtRule(trigger=trigger, title=title, offset_days=off, day_type=dt, direction=direction,
                                      roll=True, kind=kind, notes=GENERIC_NOTE, sort=i))
        db.session.add(rs)
    db.session.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _fill_ruleset(rs, form):
    rs.name = form.get("name", "").strip()
    rs.jurisdiction = form.get("jurisdiction", "").strip()
    rs.description = form.get("description", "").strip()
    rs.is_active = bool(form.get("is_active"))
    return None if rs.name else "A name is required."


def _fill_rule(r, form):
    r.trigger = form.get("trigger", "").strip()
    r.title = form.get("title", "").strip()
    r.offset_days = abs(_int(form.get("offset_days")) or 0)
    dt = form.get("day_type", "calendar")
    r.day_type = dt if dt in dict(DAY_TYPES) else "calendar"
    d = form.get("direction", "after")
    r.direction = d if d in DIRECTIONS else "after"
    r.roll = bool(form.get("roll"))
    k = form.get("kind", "deadline")
    r.kind = k if k in RULE_KINDS else "deadline"
    r.notes = form.get("notes", "").strip()
    r.sort = _int(form.get("sort")) or 0
    if not r.trigger or not r.title:
        return "Both a trigger and a title are required."
    return None


def ruleset_to_dict(rs):
    return {"name": rs.name, "jurisdiction": rs.jurisdiction, "description": rs.description,
            "format": 2,  # 2 adds the month and year units; a build that only knows 1 must refuse those rules
            "rules": [{"trigger": r.trigger, "title": r.title, "offset_days": r.offset_days, "day_type": r.day_type,
                       "direction": r.direction, "roll": bool(r.roll), "kind": r.kind, "notes": r.notes,
                       "sort": r.sort} for r in rs.rules]}


def ruleset_from_dict(data):
    if not isinstance(data, dict) or not str(data.get("name", "")).strip():
        raise ValueError("The JSON needs at least a \"name\" and a \"rules\" list.")
    rs = CourtRuleSet(name=str(data["name"]).strip()[:200], jurisdiction=str(data.get("jurisdiction", ""))[:120],
                      description=str(data.get("description", "")), is_active=True)
    rules = data.get("rules") or []
    if not isinstance(rules, list):
        raise ValueError("\"rules\" must be a list.")
    for i, item in enumerate(rules):
        if not isinstance(item, dict) or not item.get("trigger") or not item.get("title"):
            raise ValueError(f"Rule {i + 1} needs a trigger and a title.")
        dt = item.get("day_type", "calendar")
        if dt not in dict(DAY_TYPES):
            # Refuse the whole file rather than coerce or skip. A rule set written by a newer
            # Coil can carry a unit this build does not know, and reading "6 months" as
            # "6 calendar days" moves a deadline five months earlier without saying anything.
            # A rule set with one deadline quietly missing is worse than no rule set.
            raise ValueError(
                f"Rule {i + 1} ({item.get('title') or 'untitled'}) uses the unit \"{dt}\", which this "
                f"version of Coil does not know. Nothing was imported. Update Coil, or edit the file.")
        direction = item.get("direction", "after")
        kind = item.get("kind", "deadline")
        rs.rules.append(CourtRule(
            trigger=str(item["trigger"])[:120], title=str(item["title"])[:300],
            offset_days=abs(_int(item.get("offset_days")) or 0),
            day_type=dt,
            direction=direction if direction in DIRECTIONS else "after",
            roll=bool(item.get("roll", True)), kind=kind if kind in RULE_KINDS else "deadline",
            notes=str(item.get("notes", "")), sort=_int(item.get("sort")) if _int(item.get("sort")) is not None else i))
    return rs


# ---------------------------------------------------------------------------
# Rule sets
# ---------------------------------------------------------------------------
@bp.route("/settings/rules")
@login_required
def index():
    ensure_starter_rulesets()
    sets = CourtRuleSet.query.order_by(CourtRuleSet.is_active.desc(), CourtRuleSet.name).all()
    usage = {}
    for rid, n in db.session.query(CourtRule.ruleset_id, db.func.count(Task.id)).join(
            Task, Task.rule_id == CourtRule.id).group_by(CourtRule.ruleset_id).all():
        usage[rid] = n
    return render_template("rules/index.html", sets=sets, usage=usage, holiday_count=Holiday.query.count(),
                           is_owner=current_user().role == "owner")


@bp.route("/settings/rules/new", methods=["GET", "POST"])
@owner_required
def new():
    rs = CourtRuleSet(is_active=True)
    if request.method == "POST":
        err = _fill_ruleset(rs, request.form)
        if err:
            flash(err, "error")
            return render_template("rules/ruleset_form.html", rs=rs, is_new=True)
        db.session.add(rs)
        db.session.flush()
        audit("create", "court_rule_set", rs.id, rs.name, current_user().id)
        db.session.commit()
        flash(f"Rule set {rs.name} created. Add its rules below.", "ok")
        return redirect(url_for("rules.detail", id=rs.id))
    return render_template("rules/ruleset_form.html", rs=rs, is_new=True)


@bp.route("/settings/rules/import", methods=["GET", "POST"])
@owner_required
def import_json():
    if request.method == "POST":
        raw = request.form.get("json", "").strip()
        f = request.files.get("file")
        if f and f.filename:
            raw = f.read().decode("utf-8", "ignore")
        try:
            rs = ruleset_from_dict(json.loads(raw or "{}"))
        except (ValueError, json.JSONDecodeError) as e:
            flash(f"Could not import: {e}", "error")
            return render_template("rules/import.html", raw=raw)
        db.session.add(rs)
        db.session.flush()
        audit("import", "court_rule_set", rs.id, rs.name, current_user().id)
        db.session.commit()
        flash(f"Imported {rs.name} with {len(rs.rules)} rules. Check every rule before using the set.", "ok")
        return redirect(url_for("rules.detail", id=rs.id))
    return render_template("rules/import.html", raw="")


@bp.route("/settings/rules/<int:id>")
@login_required
def detail(id):
    rs = db.session.get(CourtRuleSet, id) or abort(404)
    r = CourtRule(day_type="calendar", direction="after", roll=True, kind="deadline", sort=len(rs.rules))
    return render_template("rules/detail.html", rs=rs, r=r, day_types=DAY_TYPES, directions=DIRECTIONS,
                           kinds=RULE_KINDS, is_owner=current_user().role == "owner",
                           usage=Task.query.join(CourtRule).filter(CourtRule.ruleset_id == rs.id).count())


@bp.route("/settings/rules/<int:id>/edit", methods=["GET", "POST"])
@owner_required
def edit(id):
    rs = db.session.get(CourtRuleSet, id) or abort(404)
    if request.method == "POST":
        err = _fill_ruleset(rs, request.form)
        if err:
            flash(err, "error")
            return render_template("rules/ruleset_form.html", rs=rs, is_new=False)
        db.session.commit()
        flash("Rule set saved.", "ok")
        return redirect(url_for("rules.detail", id=rs.id))
    return render_template("rules/ruleset_form.html", rs=rs, is_new=False)


@bp.route("/settings/rules/<int:id>/delete", methods=["POST"])
@owner_required
def delete(id):
    rs = db.session.get(CourtRuleSet, id) or abort(404)
    used = Task.query.join(CourtRule).filter(CourtRule.ruleset_id == rs.id).count()
    if used:
        rs.is_active = False
        db.session.commit()
        flash(f"{rs.name} is used by {used} task(s), so it was deactivated instead of deleted.", "ok")
        return redirect(url_for("rules.index"))
    audit("delete", "court_rule_set", rs.id, rs.name, current_user().id)
    db.session.delete(rs)
    db.session.commit()
    flash(f"Deleted rule set {rs.name}.", "ok")
    return redirect(url_for("rules.index"))


@bp.route("/settings/rules/<int:id>/export.json")
@login_required
def export_json(id):
    rs = db.session.get(CourtRuleSet, id) or abort(404)
    body = json.dumps(ruleset_to_dict(rs), indent=2)
    fname = "".join(ch if ch.isalnum() else "-" for ch in rs.name).strip("-").lower() or "ruleset"
    return Response(body, mimetype="application/json",
                    headers={"Content-Disposition": f"attachment; filename={fname}.json"})


@bp.route("/settings/rules/<int:id>/rules", methods=["POST"])
@owner_required
def rule_add(id):
    rs = db.session.get(CourtRuleSet, id) or abort(404)
    r = CourtRule(ruleset_id=rs.id)
    err = _fill_rule(r, request.form)
    if err:
        flash(err, "error")
        return redirect(url_for("rules.detail", id=rs.id))
    db.session.add(r)
    db.session.commit()
    flash(f"Added rule: {r.title}.", "ok")
    return redirect(url_for("rules.detail", id=rs.id))


@bp.route("/settings/rules/<int:id>/rules/<int:rid>/edit", methods=["GET", "POST"])
@owner_required
def rule_edit(id, rid):
    rs = db.session.get(CourtRuleSet, id) or abort(404)
    r = db.session.get(CourtRule, rid)
    if not r or r.ruleset_id != rs.id:
        abort(404)
    if request.method == "POST":
        err = _fill_rule(r, request.form)
        if err:
            flash(err, "error")
        else:
            db.session.commit()
            flash("Rule saved.", "ok")
            return redirect(url_for("rules.detail", id=rs.id))
    return render_template("rules/rule_form.html", rs=rs, r=r, day_types=DAY_TYPES, directions=DIRECTIONS,
                           kinds=RULE_KINDS)


@bp.route("/settings/rules/<int:id>/rules/<int:rid>/delete", methods=["POST"])
@owner_required
def rule_delete(id, rid):
    r = db.session.get(CourtRule, rid)
    if not r or r.ruleset_id != id:
        abort(404)
    if Task.query.filter_by(rule_id=r.id).count():
        flash("That rule already produced tasks on a matter, so it cannot be deleted. Edit it instead.", "error")
        return redirect(url_for("rules.detail", id=id))
    db.session.delete(r)
    db.session.commit()
    flash("Rule removed.", "ok")
    return redirect(url_for("rules.detail", id=id))


# ---------------------------------------------------------------------------
# Holidays
# ---------------------------------------------------------------------------
@bp.route("/settings/holidays")
@login_required
def holidays():
    year = _int(request.args.get("year")) or date.today().year
    rows = Holiday.query.filter(Holiday.date >= date(year, 1, 1), Holiday.date <= date(year, 12, 31)).order_by(
        Holiday.date).all()
    years = sorted({h.date.year for h in Holiday.query.all()} | {year, date.today().year, date.today().year + 1})
    return render_template("rules/holidays.html", rows=rows, year=year, years=years,
                           is_owner=current_user().role == "owner")


@bp.route("/settings/holidays", methods=["POST"])
@owner_required
def holiday_add():
    d = parse_date(request.form.get("date"))
    name = request.form.get("name", "").strip()
    if not d:
        flash("A date is required.", "error")
        return redirect(url_for("rules.holidays"))
    if Holiday.query.filter_by(date=d).first():
        flash(f"{d.isoformat()} is already a holiday.", "error")
        return redirect(url_for("rules.holidays", year=d.year))
    db.session.add(Holiday(date=d, name=name[:120]))
    db.session.commit()
    flash(f"Added {name or d.isoformat()}.", "ok")
    return redirect(url_for("rules.holidays", year=d.year))


@bp.route("/settings/holidays/load", methods=["POST"])
@owner_required
def holidays_load():
    year = _int(request.form.get("year")) or date.today().year
    existing = all_holidays()
    added = 0
    for d, name in federal_holidays(year):
        if d not in existing:
            db.session.add(Holiday(date=d, name=name))
            added += 1
    db.session.commit()
    flash(f"Loaded US federal holidays for {year}: {added} added, {11 - added} already present.", "ok")
    return redirect(url_for("rules.holidays", year=year))


@bp.route("/settings/holidays/<int:id>/delete", methods=["POST"])
@owner_required
def holiday_delete(id):
    h = db.session.get(Holiday, id) or abort(404)
    year = h.date.year
    db.session.delete(h)
    db.session.commit()
    flash("Holiday removed.", "ok")
    return redirect(url_for("rules.holidays", year=year))


# ---------------------------------------------------------------------------
# Apply a rule set to a matter
# ---------------------------------------------------------------------------
def apply_rules(matter, ruleset, trigger, trigger_date, user=None):
    """Create one Task per rule in `ruleset` with the given trigger. Returns (created, skipped) lists."""
    hol = all_holidays()
    created, skipped = [], []
    for r in ruleset.rules:
        if r.trigger != trigger:
            continue
        if Task.query.filter_by(matter_id=matter.id, rule_id=r.id, trigger_date=trigger_date).first():
            skipped.append(r)
            continue
        # A construction warning belongs on the task, not only on the preview the user already left.
        note = "\n\n".join(x for x in ((r.notes or "").strip(), construction_note(trigger_date, r)) if x)
        t = Task(matter_id=matter.id, title=r.title, kind=r.kind if r.kind in ("task", "deadline", "court_date")
                 else "deadline", due_on=compute_deadline(trigger_date, r, hol), priority="normal",
                 assignee_id=matter.responsible_user_id, notes=note, rule_id=r.id,
                 trigger_date=trigger_date, rule_trigger=r.trigger)
        db.session.add(t)
        created.append(t)
    return created, skipped


@bp.route("/rules/matters/<int:id>/apply", methods=["GET", "POST"])
@login_required
def apply(id):
    m = db.session.get(Matter, id) or abort(404)
    ensure_starter_rulesets()
    sets = CourtRuleSet.query.filter_by(is_active=True).order_by(CourtRuleSet.name).all()
    src = request.form if request.method == "POST" else request.args
    rs = db.session.get(CourtRuleSet, _int(src.get("ruleset_id")) or 0)
    if rs and not rs.is_active:
        rs = None
    trigger = (src.get("trigger") or "").strip()
    trigger_date = parse_date(src.get("trigger_date"))
    triggers = []
    if rs:
        for r in rs.rules:
            if r.trigger not in triggers:
                triggers.append(r.trigger)
    if request.method == "POST":
        if not rs or trigger not in triggers or not trigger_date:
            flash("Pick a rule set, a trigger and the date it happened.", "error")
        else:
            created, skipped = apply_rules(m, rs, trigger, trigger_date, current_user())
            if created:
                db.session.flush()
                audit("apply_rules", "matter", m.id,
                      f"{rs.name}: {trigger} on {trigger_date.isoformat()}, {len(created)} task(s)",
                      current_user().id)
                db.session.commit()
            msg = f"Added {len(created)} deadline(s) from {rs.name}."
            if skipped:
                msg += f" Skipped {len(skipped)} already on the matter for that trigger date."
            flash(msg, "ok" if created else "error")
            return redirect(url_for("matters.detail", id=m.id, tab="tasks"))
    preview = []
    if rs and trigger in triggers and trigger_date:
        hol = all_holidays()
        for r in rs.rules:
            if r.trigger == trigger:
                exists = Task.query.filter_by(matter_id=m.id, rule_id=r.id, trigger_date=trigger_date).first()
                preview.append((r, compute_deadline(trigger_date, r, hol), exists,
                                construction_note(trigger_date, r)))
    existing = Task.query.filter(Task.matter_id == m.id, Task.rule_id.isnot(None)).order_by(Task.due_on).all()
    return render_template("rules/apply.html", m=m, sets=sets, rs=rs, triggers=triggers, trigger=trigger,
                           trigger_date=trigger_date, preview=preview, existing=existing,
                           holiday_count=Holiday.query.count(), describe=describe_rule)
