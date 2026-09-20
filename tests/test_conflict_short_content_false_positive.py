"""A document whose extracted text is just a stray short word must not "exact" match every
query that happens to share that word.

Filed as Coil QA #42: a document's extracted_text was a two-character placeholder ("QA"), and
every synthetic QA search name (all conventionally prefixed "QA ...") came back as an "exact"
document-contents hit, because rapidfuzz's token_set_ratio returns 100 whenever one side's
tokens are a full subset of the other's, which a lone short word always is. Free text (notes,
messages, document contents, lead descriptions) is meant to match on substring only, per
_score's own docstring; the bug was that the substring-only rule was keyed off text length
(>200 chars) instead of the field's kind, so a short piece of content slipped into the fuzzy
path meant for names.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_conflict_short_content.db")
DB_URI = f"sqlite:///{DB_PATH}"


@pytest.fixture(scope="module")
def app():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = dict(os.environ, DATABASE_URL=DB_URI)
    out = subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], env=env, cwd=ROOT,
                         capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    from app import create_app
    return create_app({"SQLALCHEMY_DATABASE_URI": DB_URI, "TESTING": True})


def _make_document(app, name, extracted_text):
    from app.extensions import db
    from app.models import Document, Matter
    with app.app_context():
        matter = Matter.query.first()
        d = Document(matter_id=matter.id, name=name, extracted_text=extracted_text, mime="text/plain",
                     path="unused", size=len(extracted_text))
        db.session.add(d)
        db.session.commit()


def test_a_short_placeholder_does_not_fuzzy_match_every_qa_prefixed_query(app):
    from app.blueprints.conflicts import search_hits
    _make_document(app, "real.docx", "QA")
    with app.app_context():
        hits = search_hits(["QA SY Impossible DocFalsePositive Zxq9"])
    content_hits = [h for h in hits if h["role"] == "file contents"]
    assert content_hits == [], content_hits


def test_a_real_substring_in_short_content_still_hits(app):
    from app.blueprints.conflicts import search_hits
    _make_document(app, "notice.txt", "QA Smith divorce filing, uncontested.")
    with app.app_context():
        hits = search_hits(["QA Smith divorce"])
    content_hits = [h for h in hits if h["role"] == "file contents" and h["label"].startswith("notice.txt")]
    assert content_hits and content_hits[0]["score"] == 100
