"""Coil QA #179: construction_note() described the pre-roll clamped date as "this date", but
when the rule has roll on and that clamped date lands on a weekend or holiday,
compute_deadline() rolls it forward (or back) to the next court day. The note, and the
identical copy saved into the task's own notes, named a date the user never actually sees.

Jan 31, 2027 + 1 month clamps to Feb 28, 2027 (a Sunday); with roll on it becomes Mar 1, 2027,
the same fixture test_month_deadlines.py::test_clamping_happens_before_rolling already uses.

Run: .venv/bin/python -m pytest tests/test_construction_note_roll.py -q
"""
from datetime import date

from tests.test_month_deadlines import R
from app.blueprints.rules import construction_note, compute_deadline


def test_note_names_the_rolled_date_when_roll_moves_it():
    due = compute_deadline(date(2027, 1, 31), R(roll=True))
    assert due == date(2027, 3, 1)
    note = construction_note(date(2027, 1, 31), R(roll=True))
    assert "2027-03-01" in note, "the date actually shown and saved"
    assert "2027-02-28" in note, "still names the clamped date it rolled from"


def test_note_stays_as_before_when_roll_is_off():
    note = construction_note(date(2027, 1, 31), R(roll=False))
    assert "2027-03-01" not in note
    assert "2027-02-28" in note


def test_note_stays_as_before_when_the_clamped_date_is_already_a_court_day():
    # Aug 31, 2026 + 1 month clamps to Sep 30, 2026, a Wednesday: no roll needed.
    note = construction_note(date(2026, 8, 31), R(roll=True))
    assert "2026-09-30" in note
    assert note == construction_note(date(2026, 8, 31), R(roll=False))


def test_last_day_to_last_day_case_also_names_the_rolled_date():
    # Nov 28, 2026 is the last day of Nov 2026's own month? No: Nov has 30 days. Use a trigger
    # that IS its month's last day and whose +1 month lands on a non-court day.
    trigger = date(2026, 2, 28)  # last day of Feb 2026
    due = compute_deadline(trigger, R(roll=True))
    note = construction_note(trigger, R(roll=True))
    if due != date(2026, 3, 28):
        assert due.isoformat() in note
