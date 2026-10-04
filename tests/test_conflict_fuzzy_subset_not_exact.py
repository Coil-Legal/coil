"""A fuzzy token-subset match must never show as "exact".

rapidfuzz's token_set_ratio returns 100 whenever one side's tokens are a full subset of the
other's, which a name missing a middle initial or a Jr/Sr suffix always is. The literal
substring check in _score already owns score 100; the fuzzy path must stay below it so a
near-match renders as a percentage badge, not the "exact" badge. Filed as Coil QA #106.
"""
from tests.test_phase1_independent import app, staff


def test_dropped_middle_initial_and_suffix_scores_fuzzy_not_exact(app):
    from app.extensions import db
    from app.models import Contact
    from app.blueprints.conflicts import search_hits
    with app.app_context():
        db.session.add(Contact(first_name="Synthetic Walker J.",
                                last_name="Vance-Hyphen Jr Qxz9", is_client=False))
        db.session.commit()
        hits = search_hits(["Synthetic Walker Vance-Hyphen Qxz9"])
    contact_hits = [h for h in hits if h["source"] == "contact"]
    assert contact_hits, contact_hits
    assert all(h["score"] < 100 for h in contact_hits), contact_hits


def test_true_exact_substring_still_scores_100(app):
    from app.extensions import db
    from app.models import Contact
    from app.blueprints.conflicts import search_hits
    with app.app_context():
        db.session.add(Contact(first_name="Synthetic Priya", last_name="Okonkwo Zxq7", is_client=False))
        db.session.commit()
        hits = search_hits(["Synthetic Priya Okonkwo Zxq7"])
    contact_hits = [h for h in hits if h["source"] == "contact"]
    assert contact_hits and contact_hits[0]["score"] == 100, contact_hits
