"""Keep unsupported AI comparisons visible without presenting them as contradictions."""
import json
from io import BytesIO
import pytest
from pypdf import PdfReader
from tests.test_zip_import_review import app, client


def save_dep(app,text,first,second):
    from app.extensions import db
    from app.models import DepositionSummary,Matter
    from app.blueprints.documents import store_bytes
    with app.app_context():
        doc,error=store_bytes(1,'review-transcript.txt',text.encode(),user_id=1)
        assert error is None
        dep=DepositionSummary(matter=db.session.get(Matter,1),document=doc,deponent='Synthetic witness',
            summary_text='Synthetic summary.',contradictions_json=json.dumps([{'testimony':first,
            'conflicts_with':second,'source':'p1:1','kind':'internal'}]))
        db.session.add(dep);db.session.commit()
        return dep.id,dep.contradictions_json

@pytest.mark.parametrize('answer',["I am not sure.","I don't recall.","I do not know.","I cannot remember."])
def test_uncertainty_is_review_comparison_in_page_note_pdf(app,client,answer):
    from app.extensions import db
    from app.models import DepositionSummary
    from app.blueprints.discovery import deposition_note_text,build_deposition_pdf
    first='The warehouse door was scarlet.'
    text=f'Page 1\n1:1 Q. What color was the door?\n1:2 A. {first}\n1:3 Q. What was the badge number?\n1:4 A. {answer}'
    did,original=save_dep(app,text,first,answer)
    html=client.get(f'/discovery/depositions/{did}').get_data(as_text=True)
    assert 'Comparisons needing review' in html
    assert '<strong>Conflicts with:</strong>' not in html
    assert 'uncertain answer' in html
    with app.app_context():
        dep=db.session.get(DepositionSummary,did)
        note=deposition_note_text(dep)
        pdf='\n'.join(p.extract_text() for p in PdfReader(BytesIO(build_deposition_pdf(dep))).pages)
        for output in (note,pdf):
            assert 'comparisons needing review' in output.lower()
            assert 'possible contradictions' not in output.lower()
            assert first in output and answer in output
            assert 'uncertain answer' in output
        assert dep.contradictions_json==original

@pytest.mark.parametrize('first,second,text',[
    ('Not actually in transcript.','The door was blue.','Page 1\n1:1 A. The door was blue.'),
    ('The door was scarlet.','The door was blue.','Page 1\n1:1 A. The door was scarlet.\n1:2 A. The door was blue.\n1:3 A. The door was blue.'),
])
def test_unresolved_either_statement_needs_review(app,client,first,second,text):
    did,_=save_dep(app,text,first,second)
    html=client.get(f'/discovery/depositions/{did}').get_data(as_text=True)
    assert 'Comparisons needing review' in html
    assert '<strong>Conflicts with:</strong>' not in html


def test_two_unique_assertions_remain_possible_not_confirmed(app,client):
    did,_=save_dep(app,'Page 1\n1:1 A. The door was scarlet.\n1:2 A. The door was blue.',
                   'The door was scarlet.','The door was blue.')
    html=client.get(f'/discovery/depositions/{did}').get_data(as_text=True)
    assert '<strong>Conflicts with:</strong>' in html
    assert 'Comparisons needing review' not in html
    assert 'Depo. Tr. 1:1' in html and 'Depo. Tr. 1:2' in html
    assert 'AI draft' in html


def test_identical_statements_are_not_presented_as_conflicting(app,client):
    did,_=save_dep(app,'Page 1\n1:1 A. The door was scarlet.',
                   'The door was scarlet.','The door was scarlet.')
    html=client.get(f'/discovery/depositions/{did}').get_data(as_text=True)
    assert 'Both statements are the same.' in html
    assert '<strong>Conflicts with:</strong>' not in html
