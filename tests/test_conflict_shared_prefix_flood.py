"""Shared boilerplate tokens must not flood the fuzzy conflict check.

rapidfuzz's token_set_ratio scores the tokens two strings share plus whatever is left
over on each side; when most tokens are shared (a repeated case-naming prefix, a batch
date) that shared chunk alone can push the ratio over FUZZY_MIN even though the leftover
tokens, the part that actually names the person, have nothing in common. Reported as
Coil QA #109 (QA2 conflict-check deep pass): a no-match control name built only to avoid
every real record still "hit" three unrelated contacts and a matter, purely because they
shared the batch's "QA2 Conflict ... 20261004" naming convention.
"""
from tests.test_phase1_independent import app, staff


def test_shared_naming_convention_does_not_flood_unrelated_contacts(app):
    from app.extensions import db
    from app.models import Contact
    from app.blueprints.conflicts import search_hits
    with app.app_context():
        db.session.add(Contact(first_name="Synthetic Flood Batch Qxz1 H.", last_name="Boyle", is_client=False))
        db.session.commit()
        hits = search_hits(["Synthetic Flood Batch Qxz1 Nomatch Control Zzyx"])
    contact_hits = [h for h in hits if h["source"] == "contact"]
    assert contact_hits == [], contact_hits


def test_shared_naming_convention_still_lets_a_real_near_miss_through(app):
    """The remainder check must not swallow a genuine typo-level match."""
    from app.extensions import db
    from app.models import Contact
    from app.blueprints.conflicts import search_hits
    with app.app_context():
        db.session.add(Contact(first_name="Synthetic Flood Batch Qxz1 Derek", last_name="Halloway",
                                is_client=False))
        db.session.commit()
        hits = search_hits(["Synthetic Flood Batch Qxz1 Derek Holloway"])
    contact_hits = [h for h in hits if h["source"] == "contact"]
    assert contact_hits and contact_hits[0]["score"] >= 80, contact_hits
