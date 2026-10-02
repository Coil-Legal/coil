"""A long original file name must not produce an on-disk path over the filesystem limit (#87)."""
from tests.test_phase1_independent import app  # noqa: F401


def test_store_bytes_truncates_a_long_name_instead_of_500ing(app):
    from app.extensions import db
    from app.blueprints.documents import store_bytes, abs_path

    name = "QA Documents Share 20261002-" + "A" * 194 + ".txt"
    assert len(name) == 226

    with app.app_context():
        doc, error = store_bytes(1, name, b"synthetic contents", mime="text/plain")
        assert error is None
        db.session.flush()
        assert doc.name == name
        full = abs_path(doc)
        assert len(full.split("/")[-1].encode()) <= 255
        with open(full, "rb") as f:
            assert f.read() == b"synthetic contents"
