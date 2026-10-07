"""#159: the Clio activities export's combined 'Description/Note' header wasn't auto-mapped to
Description, so imported time entries kept a blank description. #158 is the direct consequence:
the activities dedupe hash key includes description, so rows that only differ by narrative text
collapsed into "updates" of each other once that column went unmapped."""
import io
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_clio_description_note.db")
DB_URI = f"sqlite:///{DB_PATH}"
UPLOADS = os.path.join(ROOT, "data", "uploads-test-clio-description-note")


@pytest.fixture(scope="module")
def app():
    import subprocess
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    env = {**os.environ, "DATABASE_URL": DB_URI}
    subprocess.run([sys.executable, os.path.join(ROOT, "seed.py")], check=True, cwd=ROOT, env=env)
    os.environ["DATABASE_URL"] = env["DATABASE_URL"]
    from app import create_app
    return create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": env["DATABASE_URL"], "UPLOAD_DIR": UPLOADS})


@pytest.fixture(scope="module")
def client(app):
    from tests.helpers import login
    c = app.test_client()
    c.tok = login(c)
    return c


def test_auto_map_detects_combined_description_note_header():
    from app.blueprints._importmap import auto_map
    headers = ["Type", "Date", "User", "Matter", "Client", "Activity Description", "Description/Note", "Quantity",
               "Rate", "Total", "Billable", "Non-billable", "Billed", "Bill state"]
    mapping = auto_map("clio", "activities", headers)
    assert mapping["description"] == "Description/Note"
    assert mapping["category"] == "Activity Description"


def _upload(c, body, filename):
    data = {"_csrf": c.tok, "source": "clio", "file": (io.BytesIO(body.encode()), filename)}
    r = c.post("/import/activities/upload", data=data, content_type="multipart/form-data")
    assert r.status_code == 302, r.data[:300]
    return r.headers["Location"].rsplit("/", 1)[-1]


def _commit(c, token):
    r = c.post(f"/import/preview/{token}", data={"_csrf": c.tok, "do": "commit"})
    assert r.status_code == 302, r.data[:500]
    return int(r.headers["Location"].rsplit("/", 1)[-1])


def _job(app, job_id):
    from app.models import ImportJob
    with app.app_context():
        j = ImportJob.query.get(job_id)
        return {"created": j.created, "updated": j.updated, "errors": j.errors}


# Same matter, same date, same hours and total on both rows: before the fix, Description/Note went
# unmapped, both rows hashed identically, and the second was imported as an "update" of the first.
CLIO_ACTIVITIES = (
    "Type,Date,User,Matter,Client,Activity Description,Description/Note,Quantity,Rate,Total,Billable,"
    "Non-billable,Billed,Bill state\r\n"
    "TimeEntry,03/02/2026,Demo Owner,M-1001,Rosa Alvarez,,Call with client re: trust funding,0.50,300.00,150.00,"
    "Yes,,No,\r\n"
    "TimeEntry,03/02/2026,Demo Owner,M-1001,Rosa Alvarez,,Draft amendment to trust,0.50,300.00,150.00,Yes,,No,\r\n"
)


def test_description_note_mapped_and_rows_not_collapsed(app, client):
    from app.models import TimeEntry
    token = _upload(client, CLIO_ACTIVITIES, "activities.csv")
    html = client.get(f"/import/preview/{token}").data.decode()
    assert 'name="map_description"' in html and "Description/Note" in html
    job = _commit(client, token)
    j = _job(app, job)
    assert j["created"] == 2 and j["updated"] == 0 and not j["errors"], j
    with app.app_context():
        descriptions = {t.description for t in TimeEntry.query.all()}
        assert "Call with client re: trust funding" in descriptions
        assert "Draft amendment to trust" in descriptions
