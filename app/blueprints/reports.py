"""Reports: A/R aging, WIP, revenue, trust balances, productivity, origination, realization, profitability.
Each one has a CSV download (?format=csv)."""
import csv
import io
from collections import OrderedDict, defaultdict
from datetime import date, timedelta
from flask import Blueprint, render_template, request, Response
from sqlalchemy.orm import joinedload
from ..extensions import db
from ..models import Invoice, TimeEntry, Expense, Payment, TrustTransaction, User
from ..helpers import login_required, parse_date, csv_safe

bp = Blueprint("reports", __name__, url_prefix="/reports")

OPEN_STATUSES = ("sent", "viewed", "partial")
BUCKETS = ["current", "1-30", "31-60", "61-90", "90+"]


def _csv(filename, header, rows):
    buf = io.StringIO()
    buf.write("﻿")  # BOM: Excel on Windows opens UTF-8 CSVs as ANSI without one
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([csv_safe(v) for v in r])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


def _money_csv(c):
    """Cents -> '1234.56' for spreadsheets (no symbol, no thousands separator)."""
    return f"{int(c or 0) / 100:.2f}"


def _wants_csv():
    return request.args.get("format") == "csv"


def _range():
    today = date.today()
    default_from = (today.replace(day=1) - timedelta(days=334)).replace(day=1)
    d_from = parse_date(request.args.get("from"), default_from)
    d_to = parse_date(request.args.get("to"), today)
    if d_to < d_from:
        d_from, d_to = d_to, d_from
    return d_from, d_to


def _bucket(days):
    if days <= 0:
        return "current"
    if days <= 30:
        return "1-30"
    if days <= 60:
        return "31-60"
    if days <= 90:
        return "61-90"
    return "90+"


@bp.route("")
@login_required
def index():
    return render_template("reports/index.html")


# ---------------------------------------------------------------- A/R aging
@bp.route("/ar-aging")
@login_required
def ar_aging():
    today = date.today()
    invoices = Invoice.query.filter(Invoice.status.in_(OPEN_STATUSES)).all()
    by_client_currency = OrderedDict()
    for inv in invoices:
        if inv.balance_cents <= 0:
            continue
        anchor = inv.due_on or inv.issued_on or today
        b = _bucket((today - anchor).days)
        currency = (inv.currency or "USD").upper()
        row = by_client_currency.setdefault((inv.client_id, currency),
                                            {"client": inv.client, "currency": currency, "invoices": [],
                                             **{k: 0 for k in BUCKETS}, "total": 0})
        row[b] += inv.balance_cents
        row["total"] += inv.balance_cents
        row["invoices"].append((inv, b))
    # A row is one client in one currency, so raw totals within a row are safe to sum and sort by;
    # only the cross-row/cross-currency footer needs splitting (issue #62, same class as #60/#61).
    rows = sorted(by_client_currency.values(), key=lambda r: -r["total"])
    totals = {k: {} for k in BUCKETS + ["total"]}
    for r in rows:
        for k in BUCKETS + ["total"]:
            totals[k][r["currency"]] = totals[k].get(r["currency"], 0) + r[k]
    if _wants_csv():
        out = [[r["client"].display_name, r["currency"]] + [_money_csv(r[k]) for k in BUCKETS + ["total"]]
              for r in rows]
        for currency in sorted({r["currency"] for r in rows}):
            out.append(["TOTAL", currency] + [_money_csv(totals[k].get(currency, 0)) for k in BUCKETS + ["total"]])
        return _csv("ar-aging.csv", ["Client", "Currency", "Current", "1-30", "31-60", "61-90", "90+", "Total"], out)
    return render_template("reports/ar_aging.html", rows=rows, totals=totals, buckets=BUCKETS, today=today)


# ---------------------------------------------------------------- WIP
@bp.route("/wip")
@login_required
def wip():
    # t.matter and e.matter per row, and matter.client in the CSV branch, were four thousand
    # queries on a firm with thirty thousand unbilled entries. Load them with the rows.
    time_rows = (TimeEntry.query.options(joinedload(TimeEntry.matter).joinedload(Matter.client))
                 .filter(TimeEntry.billable == True, TimeEntry.invoice_id == None).all())  # noqa: E712,E711
    exp_rows = (Expense.query.options(joinedload(Expense.matter).joinedload(Matter.client))
                .filter(Expense.billable == True, Expense.invoice_id == None).all())  # noqa: E712,E711
    by_matter = {}
    for t in time_rows:
        r = by_matter.setdefault(t.matter_id, {"matter": t.matter, "minutes": 0, "time_cents": 0,
                                                "expense_cents": 0, "entries": 0, "expenses": 0, "oldest": None})
        r["minutes"] += t.minutes
        r["time_cents"] += t.amount_cents
        r["entries"] += 1
        if t.date and (r["oldest"] is None or t.date < r["oldest"]):
            r["oldest"] = t.date
    for e in exp_rows:
        r = by_matter.setdefault(e.matter_id, {"matter": e.matter, "minutes": 0, "time_cents": 0,
                                                "expense_cents": 0, "entries": 0, "expenses": 0, "oldest": None})
        r["expense_cents"] += e.amount_cents
        r["expenses"] += 1
        if e.date and (r["oldest"] is None or e.date < r["oldest"]):
            r["oldest"] = e.date
    rows = sorted(by_matter.values(), key=lambda r: -(r["time_cents"] + r["expense_cents"]))
    for r in rows:
        r["total"] = r["time_cents"] + r["expense_cents"]
        r["currency"] = r["matter"].currency_code
    # Each row is one matter, so it has exactly one currency and its own total is safe to sum;
    # only the cross-matter footer needs splitting by currency (issue #64, same class as #60-#63).
    # minutes_by_currency is separate from the page's single grand-total minutes (issue #67): a
    # currency's CSV TOTAL row must show that currency's hours, not every matter's hours combined.
    totals = {"minutes": sum(r["minutes"] for r in rows), "minutes_by_currency": {},
              "time_cents": {}, "expense_cents": {}, "total": {}}
    for r in rows:
        totals["minutes_by_currency"][r["currency"]] = totals["minutes_by_currency"].get(r["currency"], 0) + r["minutes"]
        for k in ("time_cents", "expense_cents", "total"):
            totals[k][r["currency"]] = totals[k].get(r["currency"], 0) + r[k]
    if _wants_csv():
        out = [[r["matter"].number, r["matter"].name, r["matter"].client.display_name, r["matter"].billing_type,
                r["currency"], f"{r['minutes'] / 60:.2f}", _money_csv(r["time_cents"]),
                _money_csv(r["expense_cents"]), _money_csv(r["total"]),
                r["oldest"].isoformat() if r["oldest"] else ""] for r in rows]
        for currency in sorted({r["currency"] for r in rows}):
            out.append(["TOTAL", "", "", "", currency, f"{totals['minutes_by_currency'].get(currency, 0) / 60:.2f}",
                        _money_csv(totals["time_cents"].get(currency, 0)),
                        _money_csv(totals["expense_cents"].get(currency, 0)),
                        _money_csv(totals["total"].get(currency, 0)), ""])
        return _csv("wip.csv", ["Matter", "Name", "Client", "Billing", "Currency", "Unbilled hours",
                                "Unbilled time", "Unbilled expenses", "Total WIP", "Oldest item"], out)
    return render_template("reports/wip.html", rows=rows, totals=totals)


# ---------------------------------------------------------------- revenue
def _payment_currency(p):
    """Stripe only ever settles USD (see payments.pay_confirm), so a non-USD payment is always a
    manual method with no surcharge/processor fee; every payment counted here has an invoice."""
    return (p.invoice.currency or "USD").upper() if p.invoice else "USD"


@bp.route("/revenue")
@login_required
def revenue():
    d_from, d_to = _range()
    payments = (Payment.query.filter(Payment.account == "operating", Payment.received_on >= d_from,
                                     Payment.received_on <= d_to)
                .order_by(Payment.received_on).all())
    by_month = OrderedDict()
    by_matter = {}
    by_method = {}
    total_by_currency = {}
    for p in payments:
        currency = _payment_currency(p)
        key = p.received_on.strftime("%Y-%m") if p.received_on else "unknown"
        m = by_month.setdefault(key, {"month": key, "by_currency": {}, "surcharge": 0, "fees": 0, "count": 0})
        m["by_currency"][currency] = m["by_currency"].get(currency, 0) + (p.amount_cents or 0)
        m["surcharge"] += p.surcharge_cents or 0
        m["fees"] += p.stripe_fee_cents or 0
        m["count"] += 1
        matter = p.matter or (p.invoice.matter if p.invoice else None)
        mk = matter.id if matter else 0
        r = by_matter.setdefault(mk, {"matter": matter, "by_currency": {}, "count": 0})
        r["by_currency"][currency] = r["by_currency"].get(currency, 0) + (p.amount_cents or 0)
        r["count"] += 1
        method_row = by_method.setdefault(p.method or "other", {})
        method_row[currency] = method_row.get(currency, 0) + (p.amount_cents or 0)
        total_by_currency[currency] = total_by_currency.get(currency, 0) + (p.amount_cents or 0)
    matter_rows = sorted(by_matter.values(), key=lambda r: -sum(r["by_currency"].values()))
    if _wants_csv():
        out = [["month", m["month"], "", currency, m["count"], _money_csv(cents),
                # surcharge/fees are always USD (see _payment_currency), so they only land on that row.
                _money_csv(m["surcharge"]) if currency == "USD" else "0.00",
                _money_csv(m["fees"]) if currency == "USD" else "0.00"]
               for m in by_month.values() for currency, cents in sorted(m["by_currency"].items())]
        out += [["matter", r["matter"].number if r["matter"] else "(none)",
                 r["matter"].name if r["matter"] else "", currency, r["count"], _money_csv(cents), "", ""]
                for r in matter_rows for currency, cents in sorted(r["by_currency"].items())]
        out += [["total", f"{d_from.isoformat()} to {d_to.isoformat()}", "", currency, len(payments),
                 _money_csv(cents), "", ""] for currency, cents in sorted(total_by_currency.items())]
        return _csv("revenue.csv",
                    ["Group", "Key", "Name", "Currency", "Payments", "Amount", "Surcharge", "Processor fees"], out)
    return render_template("reports/revenue.html", months=list(by_month.values()), matter_rows=matter_rows,
                           by_method=by_method, total=total_by_currency, count=len(payments),
                           d_from=d_from, d_to=d_to)


# ---------------------------------------------------------------- trust balances
@bp.route("/trust-balances")
@login_required
def trust_balances():
    txns = TrustTransaction.query.all()
    by_client = {}
    by_matter = {}
    for t in txns:
        c = by_client.setdefault(t.client_id, {"client": t.client, "cents": 0, "count": 0, "uncleared": 0})
        c["cents"] += t.amount_cents
        c["count"] += 1
        if not t.cleared:
            c["uncleared"] += 1
        mk = t.matter_id or 0
        m = by_matter.setdefault((t.client_id, mk), {"client": t.client, "matter": t.matter, "cents": 0})
        m["cents"] += t.amount_cents
    client_rows = sorted(by_client.values(), key=lambda r: r["client"].sort_name or "")
    matter_rows = sorted(by_matter.values(), key=lambda r: (r["client"].sort_name or "",
                                                              r["matter"].number if r["matter"] else ""))
    total = sum(r["cents"] for r in client_rows)
    negatives = [r for r in client_rows if r["cents"] < 0] + [r for r in matter_rows if r["cents"] < 0]
    if _wants_csv():
        out = [["client", r["client"].display_name, "", _money_csv(r["cents"])] for r in client_rows]
        out += [["matter", r["client"].display_name, r["matter"].label if r["matter"] else "(general)",
                 _money_csv(r["cents"])] for r in matter_rows]
        out.append(["total", "", "", _money_csv(total)])
        return _csv("trust-balances.csv", ["Level", "Client", "Matter", "Balance"], out)
    return render_template("reports/trust_balances.html", client_rows=client_rows, matter_rows=matter_rows,
                           total=total, negatives=negatives)


# ---------------------------------------------------------------- productivity
@bp.route("/productivity")
@login_required
def productivity():
    # Billable minutes have no currency, but their dollar value does: one timekeeper can log
    # billable time against matters in more than one currency in the same month, so "amount" is
    # kept as a per-currency dict throughout, same as compensation/origination/realization's user
    # rows (issue #71, same class as #66/#68/#70).
    d_from, d_to = _range()
    entries = (TimeEntry.query.options(joinedload(TimeEntry.matter))
               .filter(TimeEntry.date >= d_from, TimeEntry.date <= d_to).all())
    months = sorted({e.date.strftime("%Y-%m") for e in entries})
    users = {u.id: u for u in User.query.all()}
    grid = {}
    for e in entries:
        key = (e.user_id, e.date.strftime("%Y-%m"))
        cell = grid.setdefault(key, {"billable": 0, "nonbillable": 0, "billed": 0, "amount": {}})
        if e.billable:
            cell["billable"] += e.minutes
            currency = e.matter.currency_code if e.matter else "USD"
            cell["amount"][currency] = cell["amount"].get(currency, 0) + e.amount_cents
            if e.invoice_id:
                cell["billed"] += e.minutes
        else:
            cell["nonbillable"] += e.minutes
    user_rows = []
    for uid in sorted({k[0] for k in grid}, key=lambda i: users[i].name if i in users else ""):
        u = users.get(uid)
        cells = [grid.get((uid, m), {"billable": 0, "nonbillable": 0, "billed": 0, "amount": {}}) for m in months]
        tot_amount = {}
        for c in cells:
            for code, cents in c["amount"].items():
                tot_amount[code] = tot_amount.get(code, 0) + cents
        tot = {"billable": sum(c["billable"] for c in cells), "nonbillable": sum(c["nonbillable"] for c in cells),
               "billed": sum(c["billed"] for c in cells), "amount": tot_amount}
        user_rows.append({"user": u, "cells": cells, "total": tot})
    grand_amount = {}
    for r in user_rows:
        for code, cents in r["total"]["amount"].items():
            grand_amount[code] = grand_amount.get(code, 0) + cents
    grand = {"billable": sum(r["total"]["billable"] for r in user_rows),
             "nonbillable": sum(r["total"]["nonbillable"] for r in user_rows),
             "amount": grand_amount}
    if _wants_csv():
        out = []
        for r in user_rows:
            name = r["user"].name if r["user"] else "(nobody)"
            for m, c in zip(months, r["cells"]):
                if not c["amount"]:
                    out.append([name, m, f"{c['billable'] / 60:.2f}", f"{c['nonbillable'] / 60:.2f}",
                                f"{(c['billable'] + c['nonbillable']) / 60:.2f}", f"{c['billed'] / 60:.2f}",
                                "", "0.00"])
                for currency, cents in sorted(c["amount"].items()):
                    out.append([name, m, f"{c['billable'] / 60:.2f}", f"{c['nonbillable'] / 60:.2f}",
                                f"{(c['billable'] + c['nonbillable']) / 60:.2f}", f"{c['billed'] / 60:.2f}",
                                currency, _money_csv(cents)])
            for currency, cents in sorted(r["total"]["amount"].items()) or [("", 0)]:
                out.append([name, "TOTAL", f"{r['total']['billable'] / 60:.2f}",
                            f"{r['total']['nonbillable'] / 60:.2f}",
                            f"{(r['total']['billable'] + r['total']['nonbillable']) / 60:.2f}",
                            f"{r['total']['billed'] / 60:.2f}", currency, _money_csv(cents)])
        return _csv("productivity.csv", ["User", "Month", "Billable hours", "Non-billable hours", "Total hours",
                                         "Billed hours", "Currency", "Billable value"], out)
    return render_template("reports/productivity.html", months=months, user_rows=user_rows, grand=grand,
                           d_from=d_from, d_to=d_to)


# ================================================================ Phase 2: origination, realization, profitability
# Shared bits for the three attorney-level reports below.
from ..models import Matter, InvoiceLine  # noqa: E402


def _pct(num, den):
    """Percent as a float, or None when the denominator is zero (templates show a dash)."""
    if not den:
        return None
    return round(100.0 * num / den, 1)


def _pct_csv(v):
    return "" if v is None else f"{v:.1f}"


def _hours_csv(minutes):
    return f"{(minutes or 0) / 60:.2f}"


def _attorney_for(matter):
    """Originator, falling back to the responsible attorney. Returns (user_or_None, flagged).
    flagged is True when the matter has no originator recorded."""
    if matter is None:
        return None, True
    if matter.originating_user_id and matter.originator:
        return matter.originator, False
    return matter.responsible, True


def _share_str(row_by_currency, total_by_currency):
    """Percent of the total this row represents, kept separate per currency: adding a EUR share to a USD
    share would misstate both, the same mistake as summing their cents into one dollar figure (issue #66)."""
    codes = sorted(c for c in row_by_currency if total_by_currency.get(c))
    if not codes:
        return "-"
    single = len(total_by_currency) == 1
    parts = [f"{100.0 * row_by_currency[c] / total_by_currency[c]:.1f}%" + ("" if single else f" {c}")
             for c in codes]
    return " + ".join(parts)


# ---------------------------------------------------------------- origination
def origination_data(d_from, d_to):
    """Collected operating revenue in the range, grouped by originating attorney.
    Returns (rows, totals). Each row: {"user", "by_currency", "count", "matter_count", "flagged_count",
    "matters": [...], "share"}. Matters with no originator use the responsible attorney and carry flagged=True.
    A payment's currency comes from its invoice, and nothing stops one matter from carrying invoices in more
    than one currency, so both the matter and attorney rows (and the grand total) keep a per-currency dict
    instead of one scalar (issue #66: summing across currencies into one dollar figure misstated both)."""
    payments = (Payment.query.filter(Payment.account == "operating", Payment.received_on >= d_from,
                                     Payment.received_on <= d_to).all())
    by_user = {}
    for p in payments:
        matter = p.matter or (p.invoice.matter if p.invoice else None)
        user, flagged = _attorney_for(matter)
        uid = user.id if user else 0
        currency = _payment_currency(p)
        row = by_user.setdefault(uid, {"user": user, "by_currency": {}, "count": 0, "matters": {}})
        row["by_currency"][currency] = row["by_currency"].get(currency, 0) + (p.amount_cents or 0)
        row["count"] += 1
        mk = matter.id if matter else 0
        mrow = row["matters"].setdefault(mk, {"matter": matter, "by_currency": {}, "count": 0, "flagged": flagged})
        mrow["by_currency"][currency] = mrow["by_currency"].get(currency, 0) + (p.amount_cents or 0)
        mrow["count"] += 1
    rows = []
    for row in by_user.values():
        matters = sorted(row["matters"].values(), key=lambda r: -sum(r["by_currency"].values()))
        row["matters"] = matters
        row["matter_count"] = len([m for m in matters if m["matter"]])
        row["flagged_count"] = len([m for m in matters if m["flagged"]])
        rows.append(row)
    rows.sort(key=lambda r: (-sum(r["by_currency"].values()), r["user"].name if r["user"] else "zzz"))
    total_by_currency = {}
    for r in rows:
        for code, cents in r["by_currency"].items():
            total_by_currency[code] = total_by_currency.get(code, 0) + cents
    totals = {"by_currency": total_by_currency, "count": sum(r["count"] for r in rows),
              "matter_count": sum(r["matter_count"] for r in rows),
              "flagged_count": sum(r["flagged_count"] for r in rows)}
    for r in rows:
        r["share"] = _share_str(r["by_currency"], total_by_currency)
    return rows, totals


@bp.route("/origination")
@login_required
def origination():
    d_from, d_to = _range()
    rows, totals = origination_data(d_from, d_to)
    if _wants_csv():
        out = []
        for r in rows:
            name = r["user"].name if r["user"] else "(no attorney)"
            for m in r["matters"]:
                for currency, cents in sorted(m["by_currency"].items()):
                    out.append([name, m["matter"].number if m["matter"] else "",
                                m["matter"].name if m["matter"] else "(no matter)",
                                m["matter"].client.display_name if m["matter"] else "", m["count"], currency,
                                _money_csv(cents), "no originator, responsible attorney used" if m["flagged"] else ""])
            for currency, cents in sorted(r["by_currency"].items()):
                out.append([name, "TOTAL", f"{r['matter_count']} matters", "", r["count"], currency,
                            _money_csv(cents), f"{r['flagged_count']} flagged" if r["flagged_count"] else ""])
        for currency, cents in sorted(totals["by_currency"].items()):
            out.append(["ALL", f"{d_from.isoformat()} to {d_to.isoformat()}", f"{totals['matter_count']} matters", "",
                        totals["count"], currency, _money_csv(cents), ""])
        return _csv("origination.csv", ["Attorney", "Matter", "Name", "Client", "Payments", "Currency", "Collected",
                                        "Flag"], out)
    return render_template("reports/origination.html", rows=rows, totals=totals, d_from=d_from, d_to=d_to)


# ---------------------------------------------------------------- realization
def _time_lines_by_entry():
    """Read actual lines from every payer, matching copied lines by group and sort.

    Only the first invoice keeps the source foreign key. Reconstructing another
    payer's cents from percentages loses rounding cents and ignores their receipts.
    """
    lines = (db.session.query(InvoiceLine).join(Invoice, Invoice.id == InvoiceLine.invoice_id)
             .options(joinedload(InvoiceLine.invoice))
             .filter(InvoiceLine.kind == "time", Invoice.status != "void").all())
    source_by_position = {}
    for line in lines:
        if line.time_entry_id and line.invoice.split_group:
            source_by_position[(line.invoice.split_group, line.sort)] = line.time_entry_id
    out = defaultdict(list)
    for line in lines:
        source = line.time_entry_id
        if not source and line.invoice.split_group:
            source = source_by_position.get((line.invoice.split_group, line.sort))
        if source:
            out[source].append(line)
    return out


def _collected_by_time_entry(lines_by_entry):
    """Allocate each invoice's time share once, conserving whole receipt cents.

    Round the invoice's combined time share, then distribute remaining cents by
    fractional remainder with entry ID as a stable tie-breaker. Include entries
    outside the requested dates so changing report windows cannot move pennies.
    Expense and tax shares remain outside collected time.
    """
    from fractions import Fraction

    invoices = {}

    def add(inv, entry_id, cents):
        if inv and inv.total_cents:
            row = invoices.setdefault(inv.id, {"invoice": inv, "weights": defaultdict(int)})
            row["weights"][entry_id] += cents or 0

    for entry_id, lines in lines_by_entry.items():
        for line in lines:
            add(line.invoice, entry_id, line.amount_cents)
    # Older imports can link an entry to an invoice without creating time lines.
    legacy = (TimeEntry.query.join(Invoice, TimeEntry.invoice_id == Invoice.id)
              .options(joinedload(TimeEntry.invoice)).filter(Invoice.status != "void").all())
    for entry in legacy:
        if entry.id not in lines_by_entry:
            add(entry.invoice, entry.id, entry.amount_cents)

    collected = defaultdict(int)
    for row in invoices.values():
        inv = row["invoice"]
        paid = sum(p.amount_cents or 0 for p in inv.payments)
        shares = {eid: Fraction(paid * cents, inv.total_cents) for eid, cents in row["weights"].items()}
        cents = {eid: share.numerator // share.denominator for eid, share in shares.items()}
        remainder = round(sum(shares.values(), Fraction())) - sum(cents.values())
        order = sorted(shares, key=lambda eid: (-(shares[eid] - cents[eid]), eid))
        for eid in order[:remainder]:
            cents[eid] += 1
        for eid, amount in cents.items():
            collected[eid] += amount
    return collected


def realization_data(d_from, d_to):
    """Worked / billed / collected per attorney and per matter for time entries dated in the range.
    worked   = every time entry at its rate
    billed   = the time lines those entries produced on non-void invoices (entry value when the line is missing)
    collected = payments on those invoices, prorated by each time line's share of the invoice total
    write-downs = worked minus billed for invoiced entries; unbilled WIP is not a write-down.

    A matter has exactly one currency, so matter_rows keep worked/billed/collected/writedown scalar, tagged
    with that matter's currency_code (same as profitability_data's matter rows, issue #69). But an attorney
    can log time across matters in more than one currency, so user_rows and totals keep worked/billed/
    collected/writedown as per-currency dicts instead of one combined sum, and billing_pct/collection_pct
    become per-currency dicts too (issue #70, same class as #68's compensation_data)."""
    entries = TimeEntry.query.filter(TimeEntry.date >= d_from, TimeEntry.date <= d_to).all()
    lines_by_entry = _time_lines_by_entry()
    collected_by_entry = _collected_by_time_entry(lines_by_entry)
    invoiced_matters = {mid for (mid,) in db.session.query(Invoice.matter_id).filter(Invoice.status != "void")
                        .distinct().all()}
    by_user, by_matter = {}, {}
    for e in entries:
        worked = e.amount_cents
        billed = 0
        collected = collected_by_entry.get(e.id, 0)
        lines = lines_by_entry.get(e.id, [])
        if lines:
            for ln in lines:
                billed += ln.amount_cents or 0
        elif e.invoice_id and e.invoice and e.invoice.status != "void":
            billed = worked
        writedown = (worked - billed) if lines or (e.invoice_id and e.invoice and e.invoice.status != "void") else 0
        currency = e.matter.currency_code if e.matter else "USD"

        mk = e.matter.id if e.matter else 0
        mr = by_matter.setdefault(mk, {"matter": e.matter, "currency": currency, "minutes": 0, "worked": 0,
                                       "billed": 0, "collected": 0, "writedown": 0, "entries": 0})
        mr["minutes"] += e.minutes or 0
        mr["worked"] += worked
        mr["billed"] += billed
        mr["collected"] += collected
        mr["writedown"] += writedown
        mr["entries"] += 1

        uk = e.user.id if e.user else 0
        ur = by_user.setdefault(uk, {"user": e.user, "minutes": 0, "minutes_by_currency": {}, "worked": {},
                                     "billed": {}, "collected": {}, "writedown": {}, "entries": 0})
        ur["minutes"] += e.minutes or 0
        ur["minutes_by_currency"][currency] = ur["minutes_by_currency"].get(currency, 0) + (e.minutes or 0)
        ur["worked"][currency] = ur["worked"].get(currency, 0) + worked
        ur["billed"][currency] = ur["billed"].get(currency, 0) + billed
        ur["collected"][currency] = ur["collected"].get(currency, 0) + collected
        ur["writedown"][currency] = ur["writedown"].get(currency, 0) + writedown
        ur["entries"] += 1

    for r in by_matter.values():
        r["billing_pct"] = _pct(r["billed"], r["worked"])
        r["collection_pct"] = _pct(r["collected"], r["billed"])
        r["invoiced"] = (r["matter"].id in invoiced_matters) if r["matter"] else False
    matter_rows = sorted(by_matter.values(), key=lambda r: -r["worked"])

    for r in by_user.values():
        r["billing_pct"] = {c: _pct(r["billed"].get(c, 0), w) for c, w in r["worked"].items()}
        r["collection_pct"] = {c: _pct(r["collected"].get(c, 0), b) for c, b in r["billed"].items()}
    user_rows = sorted(by_user.values(), key=lambda r: -sum(r["worked"].values()))

    totals = {"minutes": sum(r["minutes"] for r in user_rows), "entries": sum(r["entries"] for r in user_rows),
              "minutes_by_currency": {}, "worked": {}, "billed": {}, "collected": {}, "writedown": {}}
    for r in user_rows:
        for code, minutes in r["minutes_by_currency"].items():
            totals["minutes_by_currency"][code] = totals["minutes_by_currency"].get(code, 0) + minutes
        for k in ("worked", "billed", "collected", "writedown"):
            for code, cents in r[k].items():
                totals[k][code] = totals[k].get(code, 0) + cents
    totals["billing_pct"] = {c: _pct(totals["billed"].get(c, 0), w) for c, w in totals["worked"].items()}
    totals["collection_pct"] = {c: _pct(totals["collected"].get(c, 0), b) for c, b in totals["billed"].items()}
    return user_rows, matter_rows, totals


@bp.route("/realization")
@login_required
def realization():
    d_from, d_to = _range()
    user_rows, matter_rows, totals = realization_data(d_from, d_to)
    if _wants_csv():
        out = []
        for r in user_rows:
            name = r["user"].name if r["user"] else "(unknown)"
            for currency in sorted(r["worked"]):
                out.append(["attorney", name, "", currency, _hours_csv(r["minutes_by_currency"].get(currency, 0)),
                            _money_csv(r["worked"][currency]), _money_csv(r["billed"][currency]),
                            _money_csv(r["collected"][currency]), _pct_csv(r["billing_pct"].get(currency)),
                            _pct_csv(r["collection_pct"].get(currency)), _money_csv(r["writedown"][currency]), ""])
        for r in matter_rows:
            m = r["matter"]
            out.append(["matter", m.number if m else "", m.name if m else "(no matter)", r["currency"],
                        _hours_csv(r["minutes"]), _money_csv(r["worked"]), _money_csv(r["billed"]),
                        _money_csv(r["collected"]), _pct_csv(r["billing_pct"]), _pct_csv(r["collection_pct"]),
                        _money_csv(r["writedown"]), "" if r["invoiced"] else "not yet invoiced"])
        for currency in sorted(totals["worked"]):
            out.append(["total", f"{d_from.isoformat()} to {d_to.isoformat()}", "", currency,
                        _hours_csv(totals["minutes_by_currency"].get(currency, 0)),
                        _money_csv(totals["worked"][currency]), _money_csv(totals["billed"][currency]),
                        _money_csv(totals["collected"][currency]), _pct_csv(totals["billing_pct"].get(currency)),
                        _pct_csv(totals["collection_pct"].get(currency)), _money_csv(totals["writedown"][currency]),
                        ""])
        return _csv("realization.csv", ["Group", "Key", "Name", "Currency", "Hours", "Worked", "Billed", "Collected",
                                        "Billing realization %", "Collection realization %", "Write-downs", "Flag"],
                    out)
    return render_template("reports/realization.html", user_rows=user_rows, matter_rows=matter_rows, totals=totals,
                           d_from=d_from, d_to=d_to)


# ---------------------------------------------------------------- profitability
MATTER_STATUSES = ("pending", "open", "closed")


def profitability_data(d_from, d_to, status=""):
    """Per matter: collected operating revenue in the range, cost = time at each user's cost rate plus
    non-billable expenses, margin and margin %. A matter is flagged when any user who logged time on it has no
    cost rate, because its cost is understated rather than zero.

    A matter_row's revenue/cost/margin/margin_pct stay scalar (one matter has exactly one currency, same as
    compensation_data's matter rows), tagged with that matter's currency_code. But summing across matters in
    the totals footer into one dollar figure misstates it the same way #60-#64/#66-#68 did, so totals keeps
    revenue/time_cost/expense_cost/cost/margin/margin_pct as per-currency dicts instead (issue #69)."""
    payments = Payment.query.filter(Payment.account == "operating", Payment.received_on >= d_from,
                                    Payment.received_on <= d_to).all()
    entries = TimeEntry.query.filter(TimeEntry.date >= d_from, TimeEntry.date <= d_to).all()
    expenses = Expense.query.filter(Expense.billable == False, Expense.date >= d_from,  # noqa: E712
                                    Expense.date <= d_to).all()
    users = {u.id: u for u in User.query.all()}

    def blank():
        return {"matter": None, "revenue": 0, "payments": 0, "minutes": 0, "time_cost": 0, "expense_cost": 0,
                "cost": 0, "missing_rate_users": [], "users": set()}

    by_matter = {}
    for p in payments:
        matter = p.matter or (p.invoice.matter if p.invoice else None)
        r = by_matter.setdefault(matter.id if matter else 0, blank())
        r["matter"] = matter
        r["revenue"] += p.amount_cents or 0
        r["payments"] += 1
    for e in entries:
        r = by_matter.setdefault(e.matter_id, blank())
        r["matter"] = e.matter
        r["minutes"] += e.minutes or 0
        u = users.get(e.user_id)
        rate = (u.cost_rate_cents or 0) if u else 0
        r["time_cost"] += int(round((e.minutes or 0) * rate / 60.0))
        r["users"].add(e.user_id)
        if not rate:
            name = u.name if u else f"user #{e.user_id}"
            if name not in r["missing_rate_users"]:
                r["missing_rate_users"].append(name)
    for x in expenses:
        r = by_matter.setdefault(x.matter_id, blank())
        r["matter"] = x.matter
        r["expense_cost"] += x.amount_cents or 0
    rows = []
    for r in by_matter.values():
        if status and (not r["matter"] or r["matter"].status != status):
            continue
        r["currency"] = r["matter"].currency_code if r["matter"] else "USD"
        r["cost"] = r["time_cost"] + r["expense_cost"]
        r["margin"] = r["revenue"] - r["cost"]
        r["margin_pct"] = _pct(r["margin"], r["revenue"])
        r["cost_rate_missing"] = bool(r["missing_rate_users"])
        r["users"] = sorted(r["users"])
        rows.append(r)
    rows.sort(key=lambda r: -r["margin"])
    totals = {"revenue": {}, "time_cost": {}, "expense_cost": {}, "cost": {}, "margin": {},
              "minutes_by_currency": {}, "payments": sum(r["payments"] for r in rows),
              "minutes": sum(r["minutes"] for r in rows)}
    for r in rows:
        for k in ("revenue", "time_cost", "expense_cost", "cost", "margin"):
            totals[k][r["currency"]] = totals[k].get(r["currency"], 0) + r[k]
        totals["minutes_by_currency"][r["currency"]] = totals["minutes_by_currency"].get(r["currency"], 0) + r["minutes"]
    totals["margin_pct"] = {c: _pct(totals["margin"].get(c, 0), totals["revenue"].get(c, 0))
                            for c in totals["revenue"]}
    totals["flagged"] = len([r for r in rows if r["cost_rate_missing"]])
    return rows, totals


@bp.route("/profitability")
@login_required
def profitability():
    d_from, d_to = _range()
    status = request.args.get("status", "")
    if status not in MATTER_STATUSES:
        status = ""
    rows, totals = profitability_data(d_from, d_to, status)
    if _wants_csv():
        out = []
        for r in rows:
            m = r["matter"]
            out.append([m.number if m else "", m.name if m else "(no matter)", m.client.display_name if m else "",
                        m.status if m else "", r["currency"], _money_csv(r["revenue"]), _hours_csv(r["minutes"]),
                        _money_csv(r["time_cost"]), _money_csv(r["expense_cost"]), _money_csv(r["cost"]),
                        _money_csv(r["margin"]), _pct_csv(r["margin_pct"]),
                        "cost rate not set: " + ", ".join(r["missing_rate_users"]) if r["cost_rate_missing"] else ""])
        for currency in sorted(totals["revenue"]):
            out.append(["TOTAL", f"{d_from.isoformat()} to {d_to.isoformat()}", "", status or "all", currency,
                        _money_csv(totals["revenue"][currency]),
                        _hours_csv(totals["minutes_by_currency"].get(currency, 0)),
                        _money_csv(totals["time_cost"][currency]), _money_csv(totals["expense_cost"][currency]),
                        _money_csv(totals["cost"][currency]), _money_csv(totals["margin"][currency]),
                        _pct_csv(totals["margin_pct"].get(currency)),
                        f"{totals['flagged']} flagged" if totals["flagged"] else ""])
        return _csv("profitability.csv", ["Matter", "Name", "Client", "Status", "Currency", "Revenue", "Hours",
                                          "Time cost", "Non-billable expenses", "Total cost", "Margin", "Margin %",
                                          "Flag"], out)
    return render_template("reports/profitability.html", rows=rows, totals=totals, d_from=d_from, d_to=d_to,
                           status=status, statuses=MATTER_STATUSES)


# ---------------------------------------------------------------- compensation (Agent P, data in money.py)
@bp.route("/compensation")
@login_required
def compensation():
    from .money import compensation_data
    d_from, d_to = _range()
    matter_rows, user_rows, totals = compensation_data(d_from, d_to)
    if _wants_csv():
        out = []
        for r in matter_rows:
            m = r["matter"]
            currency = r["currency"]
            for user, pct, cents in r["working"]:
                out.append([m.number or "", m.name, m.client.display_name if m.client else "", "working",
                            user.name if user else "", f"{pct:g}", currency, _money_csv(cents), _money_csv(r["fee"]),
                            _money_csv(r["gross"]), "no working split, responsible attorney used" if r["flagged"] else ""])
            for user, pct, cents in r["originating"]:
                out.append([m.number or "", m.name, m.client.display_name if m.client else "", "originating",
                            user.name if user else "", f"{pct:g}", currency, _money_csv(cents), _money_csv(r["fee"]),
                            _money_csv(r["gross"]), "default originator credit" if r["defaulted"] else ""])
            for user, pct, cents in r["referral"]:
                out.append([m.number or "", m.name, m.client.display_name if m.client else "", "referral",
                            user.name if user else "", f"{pct:g}", currency, _money_csv(cents), _money_csv(r["fee"]),
                            _money_csv(r["gross"]), ""])
        for r in user_rows:
            name = r["user"].name if r["user"] else "(nobody)"
            for currency, cents in sorted(r["working"].items()):
                out.append(["TOTAL", name, f"{r['matter_count']} matters", "working", "", "", currency,
                            _money_csv(cents), "", "", ""])
            for currency, cents in sorted(r["originating"].items()):
                out.append(["TOTAL", name, "", "originating", "", "", currency, _money_csv(cents), "", "", ""])
            for currency, cents in sorted(r["referral"].items()):
                out.append(["TOTAL", name, "", "referral", "", "", currency, _money_csv(cents), "", "", ""])
        for currency in sorted(set(totals["working"]) | set(totals["fee"]) | set(totals["gross"])):
            out.append(["ALL", f"{d_from.isoformat()} to {d_to.isoformat()}", "", "working", "", "", currency,
                        _money_csv(totals["working"].get(currency, 0)), _money_csv(totals["fee"].get(currency, 0)),
                        _money_csv(totals["gross"].get(currency, 0)),
                        f"{totals['flagged']} flagged" if totals["flagged"] else ""])
        return _csv("compensation.csv", ["Matter", "Name", "Client", "Role", "Person", "Percent", "Currency",
                                         "Allocated", "Fee collected", "Payment total", "Flag"], out)
    return render_template("reports/compensation.html", matter_rows=matter_rows, user_rows=user_rows, totals=totals,
                           d_from=d_from, d_to=d_to)
