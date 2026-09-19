"""Two-way SMS threads per contact via Twilio, plus secure portal messages in the same timeline.
Inbound webhook at /webhooks/twilio, so no url_prefix."""
import re
from datetime import timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, current_app, Response
from markupsafe import escape
from ..extensions import db
from ..models import Contact, Matter, Message, Firm, audit, now
from ..helpers import login_required, current_user
from ..services.sms import send_sms
from ..services.mail import send_email
from ..i18n import t, lang_for

bp = Blueprint("messages", __name__)


def _digits(s):
    return re.sub(r"\D", "", s or "")


_PHONE_CHARS_RE = re.compile(r"^[\d\s()+.-]+$")


def _looks_like_a_phone_number(s):
    """Twilio's create-message call does not always reject a malformed "To" synchronously - a value
    with letters can come back "queued" with the real failure only surfacing later on a delivery
    status callback Coil does not listen for. Catch letters before they ever reach Twilio, rather
    than let them sit as a permanently misleading "queued". Digit count is left to Twilio's own
    response (already passed through verbatim, e.g. error 21211 for a too-short number), since a
    short placeholder like 555-0100 is a normal, deliberately-fake QA fixture."""
    s = (s or "").strip()
    return bool(s) and bool(_PHONE_CHARS_RE.match(s)) and bool(_digits(s))


def match_contact_by_phone(number):
    """Compare the last 10 digits so +1 prefixes and formatting do not matter."""
    d = _digits(number)[-10:]
    if not d:
        return None
    for c in Contact.query.filter(Contact.phone != "").all():
        if _digits(c.phone)[-10:] == d:
            return c
    return None


def unread_portal_count(contact_id=None):
    """Client portal messages staff have not opened yet (dashboard and thread badges)."""
    q = Message.query.filter(Message.channel == "portal", Message.direction == "in", Message.read_at.is_(None))
    if contact_id:
        q = q.filter(Message.contact_id == contact_id)
    return q.count()


@bp.route("/messages")
@login_required
def index():
    cutoff = now() - timedelta(hours=24)
    rows = Message.query.order_by(Message.created_at.desc()).all()
    threads = []
    seen = set()
    unmatched = []
    for m in rows:
        if m.contact_id is None:
            if m.direction == "in":
                unmatched.append(m)
            continue
        if m.contact_id in seen:
            continue
        seen.add(m.contact_id)
        recent_in = Message.query.filter(Message.contact_id == m.contact_id, Message.direction == "in",
                                         Message.channel != "portal", Message.created_at >= cutoff).count()
        threads.append(dict(contact=m.contact, latest=m, recent_in=recent_in,
                            unread_portal=unread_portal_count(m.contact_id)))
    contacts = Contact.query.filter((Contact.phone != "") | (Contact.email != "")).order_by(
        Contact.last_name, Contact.first_name, Contact.company_name).all()
    return render_template("messages/index.html", threads=threads, unmatched=unmatched, contacts=contacts,
                           unread_total=unread_portal_count())


@bp.route("/messages/<int:contact_id>")
@login_required
def thread(contact_id):
    c = db.session.get(Contact, contact_id) or abort(404)
    msgs = Message.query.filter_by(contact_id=c.id).order_by(Message.created_at, Message.id).all()
    changed = False
    for m in msgs:
        if m.channel == "portal" and m.direction == "in" and m.read_at is None:
            m.read_at = now()
            changed = True
    if changed:
        db.session.commit()
    matters = Matter.query.filter_by(client_id=c.id).order_by(Matter.status, Matter.created_at.desc()).all()
    # Pre-fill the reply subject from the client's last email so the attorney does not retype it.
    last_email = next((m for m in reversed(msgs) if m.channel == "email" and m.direction == "in"), None)
    prior = (last_email.subject or "").strip() if last_email else ""
    reply_subject = prior if prior.lower().startswith("re:") else (f"Re: {prior}" if prior else "")
    return render_template("messages/thread.html", c=c, msgs=msgs, matters=matters,
                           reply_subject=reply_subject,
                           matter_id=request.args.get("matter_id", type=int))


@bp.route("/messages/send", methods=["POST"])
@login_required
def send():
    c = db.session.get(Contact, request.form.get("contact_id", type=int) or 0) or abort(404)
    body = request.form.get("body", "").strip()
    matter_id = request.form.get("matter_id", type=int) or None
    if not body:
        flash("Type a message first.", "error")
        return redirect(url_for("messages.thread", contact_id=c.id))
    if not c.phone:
        flash(f"{c.display_name} has no phone number on file.", "error")
        return redirect(url_for("messages.thread", contact_id=c.id))
    if not _looks_like_a_phone_number(c.phone):
        flash(f"{c.phone!r} on file for {c.display_name} is not a valid phone number. "
              f"Fix it on the contact before sending.", "error")
        return redirect(url_for("messages.thread", contact_id=c.id))
    provider_id, status, detail = send_sms(c.phone, body)
    m = Message(contact_id=c.id, matter_id=matter_id, direction="out", channel="sms", to_addr=c.phone,
                from_addr=current_app.config.get("TWILIO_FROM_NUMBER", "") or "", body=body,
                provider_id=provider_id or "", status=status or "queued")
    db.session.add(m)
    db.session.flush()
    audit("send", "message", m.id, f"sms to {c.phone} ({status})", current_user().id)
    db.session.commit()
    if status == "unconfigured":
        flash("Twilio is not configured, so the message was stored but not delivered. See Settings > Integrations.", "")
    elif str(status).startswith("error"):
        flash(f"Twilio would not send this message: {detail} It was stored for the record.", "error")
    return redirect(url_for("messages.thread", contact_id=c.id))


@bp.route("/messages/email-send", methods=["POST"])
@login_required
def email_send():
    """Answer a filed client email by email, and keep the answer in the matter file.

    Mail filing pulls the client's email into the matter, and until now the only way
    to answer it was the attorney's own mail client, which put the answer somewhere
    Coil could not see. A file that holds one side of a conversation is worse than
    no file. The reply carries In-Reply-To and References so it lands in the client's
    existing thread rather than arriving as a fresh email they have to reconcile.
    """
    c = db.session.get(Contact, request.form.get("contact_id", type=int) or 0) or abort(404)
    body = request.form.get("body", "").strip()
    subject = request.form.get("subject", "").strip()
    matter_id = request.form.get("matter_id", type=int) or None
    back = redirect(url_for("messages.thread", contact_id=c.id))
    if not body:
        flash("Type a message first.", "error")
        return back
    if not c.email:
        flash(f"{c.display_name} has no email address on file.", "error")
        return back

    # Thread onto the most recent inbound email from this contact, if there is one.
    last_in = Message.query.filter_by(contact_id=c.id, channel="email", direction="in") \
                           .filter(Message.message_id != "") \
                           .order_by(Message.created_at.desc()).first()
    if not subject:
        prior = (last_in.subject or "").strip() if last_in else ""
        subject = prior if prior.lower().startswith("re:") else (f"Re: {prior}" if prior else "Message from your attorney")
    headers = {}
    if last_in and last_in.message_id:
        headers = {"In-Reply-To": last_in.message_id, "References": last_in.message_id}

    html = "<p>" + "</p><p>".join(escape(p) for p in body.split("\n\n") if p.strip()) + "</p>"
    firm = Firm.get()
    sent = False
    try:
        sent = send_email(c.email, subject[:300], html, text=body,
                          reply_to=(firm.email or None) if firm else None, headers=headers)
    except Exception:
        # A mail relay problem must not lose the attorney's words. Record and say so.
        current_app.logger.exception("[MAIL] reply to %s failed", c.email)

    m = Message(contact_id=c.id, matter_id=matter_id, direction="out", channel="email",
                to_addr=c.email[:200], from_addr=(current_app.config.get("MAIL_FROM") or "")[:200],
                subject=subject[:300], body=body, status="sent" if sent else "not_sent",
                user_id=current_user().id)
    db.session.add(m)
    db.session.flush()
    audit("send", "message", m.id, f"email to {c.email} ({m.status})", current_user().id)
    db.session.commit()
    if sent:
        flash(f"Emailed {c.display_name}. The reply is on the thread.", "ok")
    else:
        flash("Email is not configured, so the reply was saved to the thread but not sent. "
              "See Settings > Integrations.", "error")
    return back


@bp.route("/messages/portal-send", methods=["POST"])
@login_required
def portal_send():
    """Reply inside the client portal. The client gets an email saying a message is waiting, never the body."""
    c = db.session.get(Contact, request.form.get("contact_id", type=int) or 0) or abort(404)
    body = request.form.get("body", "").strip()
    matter_id = request.form.get("matter_id", type=int) or None
    matter = db.session.get(Matter, matter_id) if matter_id else None
    if matter and matter.client_id != c.id:
        matter = None
    if not body:
        flash("Type a message first.", "error")
        return redirect(url_for("messages.thread", contact_id=c.id))
    u = current_user()
    firm = Firm.get()
    m = Message(contact_id=c.id, matter_id=matter.id if matter else None, direction="out", channel="portal",
                to_addr=c.email or "", from_addr=firm.email or "", body=body[:20000], status="portal", user_id=u.id)
    db.session.add(m)
    db.session.flush()
    audit("send", "message", m.id, f"portal message to {c.display_name}", u.id)
    db.session.commit()
    if c.email:
        _email_new_message_notice(c, matter, firm)
        flash("Posted to the portal. The client was emailed that a message is waiting.", "ok")
    else:
        flash(f"Posted to the portal. {c.display_name} has no email on file, so no notice was sent.", "")
    return redirect(url_for("messages.thread", contact_id=c.id))


def _email_new_message_notice(c, matter, firm):
    lang = lang_for(c)
    url = f"{current_app.config['BASE_URL']}/portal/login"
    about = f"{matter.number} {matter.name}" if matter else t("email.new_message.about_account", lang)
    subj = t("email.new_message.subject", lang, firm=firm.name)
    html = (f"<div style='font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:1.5;color:#1c2430'>"
            f"<p>{escape(t('email.hello', lang, name=c.first_name or c.display_name))}</p>"
            f"<p>{escape(t('email.new_message.body', lang, firm=firm.name, about=about))}</p>"
            f"<p style='margin:20px 0'><a href='{url}' style='background:#1f5f8b;color:#fff;padding:10px 18px;"
            f"border-radius:6px;text-decoration:none;display:inline-block'>{escape(t('email.new_message.button', lang))}</a></p>"
            f"<p style='font-size:12px;color:#666'>{escape(t('email.fallback_link', lang, url=url))}</p>"
            f"<p style='font-size:13px;color:#666'>{escape(firm.name or '')}<br>{escape(firm.phone or '')}</p></div>")
    send_email(c.email, subj, html, text=t("email.new_message.text", lang, firm=firm.name, url=url),
               reply_to=firm.email or None)


@bp.route("/webhooks/twilio", methods=["POST"])
def twilio_inbound():
    frm = request.form.get("From", "")
    body = request.form.get("Body", "")
    sid = request.form.get("MessageSid", "")
    to = request.form.get("To", "")
    c = match_contact_by_phone(frm)
    if sid and Message.query.filter_by(provider_id=sid).first():
        return _twiml()
    m = Message(contact_id=c.id if c else None, direction="in", channel="sms", from_addr=frm, to_addr=to,
                body=body, provider_id=sid, status="received")
    db.session.add(m)
    db.session.flush()
    audit("receive", "message", m.id, f"sms from {frm}" + (f" ({c.display_name})" if c else " (no match)"))
    db.session.commit()
    return _twiml()


def _twiml():
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response></Response>', mimetype="text/xml")
