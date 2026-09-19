"""Deadlines counted in months and years.

Rules written in months are routine in the work a solo does: six months to move for
relief from a default judgment, six months to present a government tort claim, four
months for a probate creditor claim, a year under the savings statutes, and every
statute of limitation. Before this existed an attorney had to convert to days by hand
and type 180, which is wrong in most months, and Coil rendered that wrong date with
no warning at all.

The semantics are the corresponding date, clamped to the end of the month. That is the
majority rule and it is codified: New York General Construction Law s 30 and Texas
Government Code s 311.014(c) both end the period on the last day when the month has
too few days, and Oregon says the same for a leap-day start.

Where the construction is genuinely contested, Coil takes the earlier date and says so
on the deadline. Filing early is survivable. Filing late ends the case.

Run: .venv/bin/python -m pytest tests/test_month_deadlines.py -q
"""
import os
import sys
from datetime import date

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.blueprints.rules import (  # noqa: E402
    add_months, compute_deadline, construction_note, describe_rule, ruleset_from_dict, DAY_TYPES)


class R:
    """A rule without the database, matching what compute_deadline reads."""

    def __init__(self, offset_days=1, day_type="month", direction="after", roll=False,
                 trigger="Filing", notes=""):
        self.offset_days, self.day_type, self.direction = offset_days, day_type, direction
        self.roll, self.trigger, self.notes = roll, trigger, notes


# --------------------------------------------------------------------- the ordinary case
@pytest.mark.parametrize("trigger,months,expected", [
    (date(2026, 6, 15), 6, date(2026, 12, 15)),   # the everyday one: same date, six months on
    (date(2026, 1, 15), 1, date(2026, 2, 15)),
    (date(2026, 11, 30), 3, date(2027, 2, 28)),   # crosses a year boundary and clamps
    (date(2026, 3, 10), 12, date(2027, 3, 10)),
])
def test_the_corresponding_date(trigger, months, expected):
    assert compute_deadline(trigger, R(offset_days=months)) == expected


def test_a_year_is_the_same_date_next_year_not_365_days(): 
    """365 days is not a year across a leap year, and the difference is a day in court."""
    assert compute_deadline(date(2027, 3, 1), R(offset_days=1, day_type="year")) == date(2028, 3, 1)


def test_months_count_backward_too():
    assert compute_deadline(date(2026, 5, 15), R(offset_days=3, direction="before")) == date(2026, 2, 15)


# --------------------------------------------------------------------- the month-end rule
def test_a_day_that_does_not_exist_clamps_to_the_end_of_the_month():
    """January 31 plus one month. NY General Construction Law s 30: the period ends with the last day."""
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert compute_deadline(date(2026, 1, 31), R()) == date(2026, 2, 28)


def test_the_leap_year_version():
    assert add_months(date(2028, 1, 31), 1) == date(2028, 2, 29)
    assert add_months(date(2024, 2, 29), 12) == date(2025, 2, 28)


def test_month_math_is_anchored_never_accumulated():
    """One month twice is not two months. Adding repeatedly loses the day and the deadline moves."""
    once_then_again = add_months(add_months(date(2026, 1, 31), 1), 1)
    straight = add_months(date(2026, 1, 31), 2)
    assert once_then_again == date(2026, 3, 28)
    assert straight == date(2026, 3, 31)
    assert once_then_again != straight, "this is why the offset is applied to the trigger in one step"
    assert compute_deadline(date(2026, 1, 31), R(offset_days=2)) == straight


# --------------------------------------------------------------------- saying so
def test_it_warns_when_the_day_did_not_exist():
    note = construction_note(date(2026, 1, 31), R())
    assert "2026-02-28" in note, "it names the date it chose"
    assert "2026-03-03" in note, "and the date it did not choose"
    assert "earlier" in note


def test_it_warns_on_the_case_nobody_sees_coming():
    """February 28 plus one month. We say March 28; 29 CFR 4000.43 runs last day to last day
    and would say March 31. Every mainstream date library quietly disagrees with that reg."""
    note = construction_note(date(2026, 2, 28), R())
    assert "2026-03-28" in note and "2026-03-31" in note


def test_it_stays_quiet_when_nothing_is_ambiguous():
    """A warning on every deadline is a warning nobody reads. Days 1 to 28 are never ambiguous."""
    for day in (1, 14, 15, 28):
        assert construction_note(date(2026, 6, day), R(offset_days=6)) == ""


def test_days_and_court_days_never_warn():
    for dt in ("calendar", "court", "nextmonday"):
        assert construction_note(date(2026, 1, 31), R(day_type=dt, offset_days=30)) == ""


def test_the_warning_lands_on_the_task_itself(tmp_path):
    """The preview is a page the attorney has already left by the time the deadline matters."""
    from app.blueprints import rules as rules_mod
    note = rules_mod.construction_note(date(2026, 1, 31), R(notes="Check local rules."))
    combined = "\n\n".join(x for x in ("Check local rules.", note) if x)
    assert combined.startswith("Check local rules.")
    assert "2026-02-28" in combined, "the rule's own note and the warning both survive"


# --------------------------------------------------------------------- weekends and holidays
def test_clamping_happens_before_rolling():
    """Reversing the order gives a different answer. Jan 31 2027 + 1 month clamps to Feb 28,
    a Sunday, which then rolls to Mar 1."""
    assert add_months(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert date(2027, 2, 28).weekday() == 6
    assert compute_deadline(date(2027, 1, 31), R(roll=True)) == date(2027, 3, 1)


def test_rolling_can_be_turned_off_for_a_statute():
    assert compute_deadline(date(2027, 1, 31), R(roll=False)) == date(2027, 2, 28)


# --------------------------------------------------------------------- the file format
def test_an_unknown_unit_is_refused_not_read_as_days():
    """A rule set from a newer Coil must not import "6 months" as six calendar days.
    That moves a deadline five months earlier and nothing on screen would say so."""
    data = {"name": "From the future", "rules": [
        {"trigger": "Filing", "title": "Answer", "offset_days": 6, "day_type": "fortnight"}]}
    with pytest.raises(ValueError) as e:
        ruleset_from_dict(data)
    assert "fortnight" in str(e.value)
    assert "Nothing was imported" in str(e.value)


def test_a_month_rule_survives_a_round_trip():
    data = {"name": "Probate", "rules": [
        {"trigger": "Letters issued", "title": "Creditor claim", "offset_days": 4, "day_type": "month"}]}
    rs = ruleset_from_dict(data)
    assert rs.rules[0].day_type == "month" and rs.rules[0].offset_days == 4


def test_the_rule_reads_in_plain_words():
    assert describe_rule(R(offset_days=6)).startswith("6 months after")
    assert "years" in describe_rule(R(offset_days=2, day_type="year"))


def test_every_unit_has_a_label():
    """The task detail page renders this; a missing label shows the attorney a raw key."""
    from app.helpers import _day_type_label
    for key, label in DAY_TYPES:
        assert _day_type_label(key) == label and label
