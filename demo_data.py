"""Fill a Coil instance with a fake practice, so every screen and every API tool has
something real-shaped to work on.

Run after seed.py:

    python demo_data.py            add the demo practice
    python demo_data.py --clear    remove it again

EVERYTHING IT CREATES IS INVENTED. The people, companies, doctors, courts, case numbers
and citations do not exist, the sample documents say so on their first line, and every
record it writes is tagged so you can find and delete it later. Do not point this at an
instance that holds real matters: it is for trying Coil out and for checking that a tool
does what it claims before you trust it with a client.
"""
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from app import create_app
from app.extensions import db
from app.models import (Contact, Matter, MatterParty, TimeEntry, Task, Invoice, InvoiceLine,
                        Note, CalendarEvent, IntakeLead, User, Firm, Document)

TAG = "[demo]"          # every record carries this so --clear can find it
SAMPLES = Path(__file__).parent / "samples"


def _clear():
    """Remove only what this script made. Anything without the tag is left alone."""
    n = 0
    for row in Note.query.filter(Note.body.like(f"%{TAG}%")).all():
        db.session.delete(row); n += 1
    for row in TimeEntry.query.filter(TimeEntry.description.like(f"%{TAG}%")).all():
        db.session.delete(row); n += 1
    for row in Task.query.filter(Task.title.like(f"%{TAG}%")).all():
        db.session.delete(row); n += 1
    for row in CalendarEvent.query.filter(CalendarEvent.title.like(f"%{TAG}%")).all():
        db.session.delete(row); n += 1
    for row in IntakeLead.query.filter(IntakeLead.description.like(f"%{TAG}%")).all():
        db.session.delete(row); n += 1
    for m in Matter.query.filter(Matter.description.like(f"%{TAG}%")).all():
        for d in Document.query.filter_by(matter_id=m.id).all():
            db.session.delete(d); n += 1
        for i in Invoice.query.filter_by(matter_id=m.id).all():
            InvoiceLine.query.filter_by(invoice_id=i.id).delete()
            db.session.delete(i); n += 1
        for t in TimeEntry.query.filter_by(matter_id=m.id).all():
            db.session.delete(t); n += 1
        MatterParty.query.filter_by(matter_id=m.id).delete()
        db.session.delete(m); n += 1
    for c in Contact.query.filter(Contact.notes.like(f"%{TAG}%")).all():
        db.session.delete(c); n += 1
    db.session.commit()
    print(f"removed {n} demo records")


def _mk_invoice(firm, matter, client, user, lines, status, days_ago):
    number = f"{firm.invoice_prefix or ''}{firm.next_invoice_number}"
    firm.next_invoice_number = (firm.next_invoice_number or 1000) + 1
    issued = date.today() - timedelta(days=days_ago)
    subtotal = sum(qty * rate for _, qty, rate in lines)
    inv = Invoice(number=number, matter_id=matter.id, client_id=client.id, kind=matter.billing_type,
                  status=status, issued_on=issued, due_on=issued + timedelta(days=30),
                  subtotal_cents=subtotal, total_cents=subtotal,
                  paid_cents=subtotal if status == "paid" else (subtotal // 2 if status == "partial" else 0))
    db.session.add(inv)
    db.session.flush()
    for desc, qty, rate in lines:
        db.session.add(InvoiceLine(invoice_id=inv.id, description=desc, quantity=qty,
                                   unit_cents=rate, amount_cents=qty * rate,
                                   kind="time" if matter.billing_type == "hourly" else "flat",
                                   date=issued))
    return inv


def build():
    u = User.query.first()
    firm = Firm.get()
    if Matter.query.filter(Matter.description.like(f"%{TAG}%")).count():
        print("demo practice is already loaded. Run with --clear first to rebuild it.")
        return

    # --- people ------------------------------------------------------------------
    rosalind = Contact(first_name="Rosalind", last_name="Marchetti", email="rosalind@example.test",
                       phone="+15125550164", is_client=True, address="88 Cypress Row, Austin, TX 78704",
                       notes=f"{TAG} Referred by Maria Alvarez.")
    nordvale = Contact(kind="company", company_name="Nordvale Freight Co.", email="claims@nordvale.test",
                       is_client=False, notes=f"{TAG} Adverse party, Marchetti PI matter.")
    teodora = Contact(first_name="Teodora", last_name="Vance", email="teodora@example.test",
                      is_client=True, phone="+15125550188", notes=f"{TAG} Managing member, Bluebonnet.")
    lucien = Contact(first_name="Lucien", last_name="Okonkwo", email="lucien@example.test",
                     is_client=True, phone="+15125550172", notes=f"{TAG} Criminal defense client.")
    db.session.add_all([rosalind, nordvale, teodora, lucien])
    db.session.commit()

    # --- matters -----------------------------------------------------------------
    n = firm.next_matter_number or 1003
    pi = Matter(number=f"M-{n}", client_id=rosalind.id, name="Marchetti v. Nordvale Freight (PI)",
                practice_area="Personal Injury", billing_type="contingency", contingency_pct=33.3,
                responsible_user_id=u.id, opened_on=date.today() - timedelta(days=180),
                sol_date=date.today() + timedelta(days=520),
                sol_basis="Two-year limitations, TX CPRC 16.003",
                description=f"{TAG} Rear-end collision, Farm Road 12, 11 Feb 2026. Fake matter for testing.")
    crim = Matter(number=f"M-{n+1}", client_id=lucien.id, name="State v. Okonkwo (DWI)",
                  practice_area="Criminal Defense", billing_type="flat", flat_fee_cents=450000,
                  responsible_user_id=u.id, opened_on=date.today() - timedelta(days=60),
                  court="Tarrant Valley County Court 3", case_number="DEMO-CR-2026-1188",
                  description=f"{TAG} First offence DWI. Fake matter for testing.")
    corp = Matter(number=f"M-{n+2}", client_id=teodora.id, name="Bluebonnet carrier contract review",
                  practice_area="Business", billing_type="hourly", hourly_rate_cents=35000,
                  responsible_user_id=u.id, opened_on=date.today() - timedelta(days=30),
                  description=f"{TAG} Review of freight services agreement. Fake matter for testing.")
    db.session.add_all([pi, crim, corp])
    firm.next_matter_number = n + 3
    db.session.commit()
    db.session.add(MatterParty(matter_id=pi.id, contact_id=nordvale.id,
                               name="Nordvale Freight Co.", role="adverse"))

    # --- the work ----------------------------------------------------------------
    for days, mins, what, matter in [
        (12, 90, "Review medical records and build treatment chronology", pi),
        (9, 45, "Call with client re: MMI and demand strategy", pi),
        (6, 150, "Draft settlement demand to Continental Mutual", pi),
        (20, 60, "Review freight services agreement, indemnity and insurance clauses", corp),
        (14, 30, "Email to client summarising contract risks", corp),
        (25, 120, "Review offence report and dashcam, prepare for setting", crim),
    ]:
        db.session.add(TimeEntry(matter_id=matter.id, user_id=u.id,
                                 date=date.today() - timedelta(days=days), minutes=mins,
                                 rate_cents=35000 if matter.billing_type == "hourly" else 0,
                                 description=f"{what} {TAG}",
                                 billable=matter.billing_type == "hourly"))

    for days, title, matter in [
        (3, "Follow up with Continental Mutual on the demand", pi),
        (10, "Request pre-trip inspection records", pi),
        (-2, "File motion to suppress", crim),
        (21, "Return marked-up contract to client", corp),
    ]:
        db.session.add(Task(matter_id=matter.id, title=f"{title} {TAG}",
                            due_on=date.today() + timedelta(days=days), assignee_id=u.id, kind="task"))

    for days, title, matter, where in [
        (4, "Call with adjuster, Continental Mutual", pi, "Phone"),
        (11, "Pretrial setting, County Court 3", crim, "Tarrant Valley Courthouse"),
        (18, "Contract walkthrough with Teodora", corp, "Office"),
    ]:
        db.session.add(CalendarEvent(matter_id=matter.id, title=f"{title} {TAG}",
                                     starts_at=datetime.utcnow() + timedelta(days=days, hours=3),
                                     ends_at=datetime.utcnow() + timedelta(days=days, hours=4),
                                     location=where, user_id=u.id))

    for matter, body in [
        (pi, "Adjuster called offering 6,000 before we were retained. Client did not sign anything."),
        (pi, "Records complete from all five providers. C6-C7 changes look chronic; say so in the demand."),
        (crim, "Client has no priors. Breath test administered 47 minutes after the stop."),
        (corp, "Section 5 indemnity is one-sided. Flagged to client with suggested revision."),
    ]:
        db.session.add(Note(matter_id=matter.id, user_id=u.id, body=f"{body} {TAG}"))

    db.session.add(IntakeLead(name="Wendell Achterberg", email="wendell@example.test",
                              phone="+15125550133", matter_type="Landlord dispute",
                              description=f"{TAG} Withheld deposit after moving out. Fake lead for testing.",
                              source="web"))

    # --- money -------------------------------------------------------------------
    _mk_invoice(firm, corp, teodora, u,
                [("Contract review, 1.0 hr", 1, 35000), ("Client correspondence, 0.5 hr", 1, 17500)],
                "sent", 20)
    _mk_invoice(firm, corp, teodora, u, [("Contract review, 2.0 hr", 2, 35000)], "paid", 55)
    _mk_invoice(firm, crim, lucien, u, [("Flat fee, DWI defence", 1, 450000)], "partial", 30)
    db.session.commit()

    # --- documents ---------------------------------------------------------------
    from app.blueprints.documents import store_bytes
    files = [
        (pi, "medical-records-demo.txt", "Medical records", "Records"),
        (pi, "deposition-excerpt-demo.txt", "Depositions", "Discovery"),
        (pi, "settlement-demand-demo.txt", "Demand", "Correspondence"),
        (pi, "intake-notes-demo.txt", "Intake", "Intake"),
        (pi, "brief-with-citations-demo.txt", "Briefing", "Pleadings"),
        (corp, "contract-demo.txt", "Contract", "Contracts"),
    ]
    added = 0
    for matter, fname, tag, folder in files:
        src = SAMPLES / fname
        if not src.exists():
            print(f"  missing sample {fname}, skipped")
            continue
        doc, err = store_bytes(matter.id, fname, src.read_bytes(), mime="text/plain",
                               user_id=u.id, folder=folder, tags=f"demo,{tag}")
        if err:
            print(f"  {fname}: {err}")
        else:
            added += 1
    db.session.commit()

    print(f"demo practice loaded: 3 matters, 4 contacts, 6 time entries, 3 invoices, "
          f"4 notes, 4 tasks, 3 events, 1 lead, {added} documents")
    print("Everything is tagged [demo]. Remove it with: python demo_data.py --clear")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        if "--clear" in sys.argv:
            _clear()
        else:
            build()
