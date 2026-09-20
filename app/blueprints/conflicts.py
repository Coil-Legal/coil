"""Conflict checks: fuzzy name search across everything the firm has touched."""
import json
import re
import unicodedata
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from rapidfuzz import fuzz
from ..extensions import db
from ..models import ConflictCheck, Contact, Matter, MatterParty, Note, IntakeLead, Message, Document, audit
from ..helpers import login_required, current_user

bp = Blueprint("conflicts", __name__, url_prefix="/conflicts")

OUTCOMES = ["clear", "conflict", "waived", "unresolved"]
FUZZY_MIN = 80


def normalise(s):
    """Fold accented Latin letters (Nguyễn, François, Müller) to their plain form before
    matching, so a client's name typed with or without diacritics hits the same record.
    Non-Latin scripts (Greek, Cyrillic, CJK) have no ASCII decomposition and are unaffected."""
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = "".join(ch if ch.isalnum() else " " for ch in s.casefold())
    return " ".join(s.split())


CONTENT_ROLES = {"note", "message", "file contents", "lead description"}


def _score(query, text, content=False):
    """Exact substring wins; otherwise token_set_ratio at or above the threshold.
    Free text (notes, messages, file contents, lead descriptions) only matches on substring:
    fuzzy scoring a whole document against a name matches on a single shared common word, and
    a short or failed extraction (a two-character "QA" placeholder, say) then looks like an
    "exact" hit against every query that happens to share that word, regardless of length."""
    nq, nt = normalise(query), normalise(text)
    if not nq or not nt:
        return None
    if len(nq) >= 3 and nq in nt:
        return 100
    if content:
        return None
    s = fuzz.token_set_ratio(nq, nt)
    return int(s) if s >= FUZZY_MIN else None


def _index(exclude_contact_id=None, exclude_lead_id=None):
    """Everything we search, as (text, source, label, url, role)."""
    rows = []
    for c in Contact.query.all():
        if c.id == exclude_contact_id:
            continue
        role = "client" if c.is_client else "contact"
        url = f"/contacts/{c.id}"
        names = {c.display_name, f"{c.first_name} {c.last_name}".strip(), c.company_name or ""}
        names.update(a.strip() for a in (c.aliases or "").splitlines())
        for n in names:
            if n:
                rows.append((n, "contact", c.display_name, url, role))
        if c.email:
            rows.append((c.email, "contact", f"{c.display_name} <{c.email}>", url, role))
    for p in MatterParty.query.all():
        m = p.matter
        rows.append((p.name, "party", f"{p.name} on {m.label if m else '?'}", f"/matters/{p.matter_id}",
                     p.role.replace("_", " ")))
    for m in Matter.query.all():
        rows.append((m.name, "matter", m.label, f"/matters/{m.id}", "matter name"))
    for n in Note.query.all():
        url = f"/matters/{n.matter_id}" if n.matter_id else (f"/contacts/{n.contact_id}" if n.contact_id else "")
        snippet = " ".join(n.body.split())[:90]
        rows.append((n.body, "note", snippet, url, "note"))
    for msg in Message.query.all():
        if not msg.body:
            continue
        who = msg.contact.display_name if msg.contact else (msg.to_addr or msg.from_addr or "unknown")
        url = f"/messages/{msg.contact_id}" if msg.contact_id else "/messages"
        snippet = " ".join(msg.body.split())[:90]
        rows.append((msg.body, "message", f"{msg.channel} with {who}: {snippet}", url, "message"))
    for d in Document.query.all():
        url = f"/documents?matter_id={d.matter_id}"
        label = f"{d.name} on {d.matter.label if d.matter else '?'}"
        rows.append((d.name, "document", label, url, "file name"))
        if d.extracted_text:
            rows.append((d.extracted_text, "document", f"{label} (contents)", url, "file contents"))
    for l in IntakeLead.query.all():
        if l.id == exclude_lead_id:
            continue
        rows.append((l.name, "lead", l.name, f"/intake/{l.id}", "lead"))
        if l.email:
            rows.append((l.email, "lead", f"{l.name} <{l.email}>", f"/intake/{l.id}", "lead email"))
        if l.description:
            rows.append((l.description, "lead", f"{l.name}: " + " ".join(l.description.split())[:80], f"/intake/{l.id}",
                         "lead description"))
        if l.adverse_party:
            rows.append((l.adverse_party, "lead", f"{l.adverse_party} (adverse to lead {l.name})",
                         f"/intake/{l.id}", "adverse party"))
    return rows


def search_hits(names, exclude_contact_id=None, exclude_lead_id=None):
    """Shared read-only search for the checker and intake conversion."""
    queries = [n.strip() for n in names if n and n.strip()]
    if not queries or any(not normalise(q) for q in queries):
        raise ValueError("Enter a name containing letters or numbers before running the conflict check.")
    index = _index(exclude_contact_id, exclude_lead_id)
    hits = {}
    for q in queries:
        for text, source, label, url, role in index:
            score = _score(q, text, content=role in CONTENT_ROLES)
            if score is None:
                continue
            key = (q, source, url, label)
            if key not in hits or hits[key]["score"] < score:
                hits[key] = {"query": q, "source": source, "label": label, "score": score,
                             "url": url, "role": role, "match": text, "kind": source}
    return sorted(hits.values(), key=lambda r: (-r["score"], r["query"], r["source"]))


def run_check(names, matter_id=None, contact_id=None, user_id=None):
    """Run a check and store it. Returns the committed ConflictCheck."""
    queries = [n.strip() for n in names.splitlines() if n.strip()]
    results = [{k: v for k, v in hit.items() if k not in ("match", "kind")}
               for hit in search_hits(queries)]
    chk = ConflictCheck(run_by_id=user_id, query="\n".join(queries), results_json=json.dumps(results),
                        matter_id=matter_id, contact_id=contact_id,
                        outcome="unresolved" if results else "clear")
    db.session.add(chk)
    db.session.flush()
    audit("run", "conflict_check", chk.id, f"{len(queries)} names, {len(results)} hits", user_id)
    db.session.commit()
    return chk


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


@bp.route("")
@login_required
def index():
    history = db.session.query(ConflictCheck).order_by(ConflictCheck.created_at.desc()).limit(50).all()
    matter_id = _int(request.args.get("matter_id"))
    contact_id = _int(request.args.get("contact_id"))
    prefill = request.args.get("q", "")
    matter = db.session.get(Matter, matter_id) if matter_id else None
    contact = db.session.get(Contact, contact_id) if contact_id else None
    if matter and not prefill:
        lines = [matter.client.display_name] + [p.name for p in matter.parties]
        prefill = "\n".join(lines)
    if contact and not prefill:
        prefill = contact.display_name
    matters = Matter.query.filter(Matter.status != "closed").order_by(Matter.number).all()
    return render_template("conflicts/index.html", history=history, prefill=prefill, matter=matter, contact=contact,
                           matters=matters)


@bp.route("/run", methods=["POST"])
@login_required
def run():
    names = request.form.get("names", "")
    if not names.strip():
        flash("Enter at least one name to search.", "error")
        return redirect(url_for("conflicts.index"))
    try:
        chk = run_check(names, matter_id=_int(request.form.get("matter_id")),
                        contact_id=_int(request.form.get("contact_id")), user_id=current_user().id)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("conflicts.index"))
    return redirect(url_for("conflicts.detail", id=chk.id))


@bp.route("/<int:id>")
@login_required
def detail(id):
    chk = db.session.get(ConflictCheck, id) or abort(404)
    contact = db.session.get(Contact, chk.contact_id) if chk.contact_id else None
    return render_template("conflicts/detail.html", chk=chk, results=chk.results, contact=contact, outcomes=OUTCOMES)


@bp.route("/<int:id>/resolve", methods=["POST"])
@login_required
def resolve(id):
    chk = db.session.get(ConflictCheck, id) or abort(404)
    outcome = request.form.get("outcome", "")
    if outcome not in OUTCOMES:
        flash("Pick an outcome.", "error")
        return redirect(url_for("conflicts.detail", id=id))
    notes = request.form.get("notes", "").strip()
    if outcome == "waived" and not notes:
        flash("Enter a reason before waiving a conflict.", "error")
        return redirect(url_for("conflicts.detail", id=id))
    chk.outcome = outcome
    chk.notes = notes
    audit("resolve", "conflict_check", chk.id, outcome, current_user().id)
    if chk.matter_id:
        audit("conflict_check", "matter", chk.matter_id, f"check #{chk.id} marked {outcome}", current_user().id)
    db.session.commit()
    flash(f"Conflict check marked {outcome}.", "ok")
    return redirect(url_for("conflicts.detail", id=id))
