"""Citation checking, and the one failure mode that matters.

A reporter page resolves to whichever case occupies it. A pincite lands inside another
case's page range, so an invented citation with plausible numbers happily resolves to a
real case with a completely different name. Reporting that as "resolved" is worse than
having no cite checker at all: it tells an attorney a fabricated citation has been
checked, and that is how people get sanctioned.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.blueprints._courtlistener import _claimed_names, _name_for, _names_agree, _norm_name  # noqa: E402


def test_a_case_name_is_read_from_in_front_of_its_citation():
    text = "See Halloway v. Pemberton Carriers, 812 F.3d 1144 (9th Cir. 2016)."
    assert _name_for(text, "812 F.3d 1144", _claimed_names(text)) == "Halloway v. Pemberton Carriers"


def test_the_introductory_signal_is_not_part_of_the_name():
    for signal in ("See ", "See also ", "Accord ", "Cf. ", "But see "):
        text = f"{signal}Smith v. Jones, 100 F.3d 200 (5th Cir. 1996)."
        assert _name_for(text, "100 F.3d 200", _claimed_names(text)) == "Smith v. Jones"


def test_a_fabricated_name_does_not_agree_with_the_real_one():
    """The actual failure seen in review: 812 F.3d 1144 is a pincite into Tubbs."""
    assert _names_agree("Halloway v. Pemberton Carriers",
                        "Tubbs v. Surface Transportation Board") is False


def test_the_same_case_still_agrees_through_normal_variation():
    """Reporters abbreviate and add corporate suffixes. One shared surname is enough."""
    for claimed, actual in [
        ("Celotex Corp. v. Catrett", "Celotex Corp. v. Catrett, Administratrix of the Estate"),
        ("Matsushita Elec. Indus. Co. v. Zenith Radio Corp.",
         "Matsushita Electric Industrial Co. v. Zenith Radio Corp."),
        ("Anderson v. Liberty Lobby", "Anderson v. Liberty Lobby, Inc."),
    ]:
        assert _names_agree(claimed, actual) is True, claimed


def test_nothing_to_compare_never_cries_wolf():
    """A citation with no case name in front is common and is not evidence of anything."""
    assert _names_agree("", "Tubbs v. Surface Transportation Board") is True
    assert _names_agree("Smith v. Jones", "") is True


def test_corporate_noise_alone_is_not_a_match():
    """Two unrelated companies both ending in Inc must not agree on the word Inc."""
    assert _names_agree("Acme Inc. v. Widget LLC", "Zephyr Inc. v. Gadget LLC") is False


def test_normalisation_drops_the_words_that_carry_no_identity():
    got = _norm_name("The Celotex Corporation, Inc. v. Catrett, et al.")
    for noise in ("the", "corporation", "inc", "et", "al", "v"):
        assert noise not in got
    assert "celotex" in got and "catrett" in got
