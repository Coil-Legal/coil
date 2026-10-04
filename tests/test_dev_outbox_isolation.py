"""The dev outbox is one module-level list shared by every Flask app created in this
process. Each pytest test module builds its own app/DB/upload dir for isolation, but mail
sent by an earlier test module stayed in the outbox for the next one, and dev_outbox()
caps at the last 50 entries: once the whole run's cumulative total passed 50, a test doing
`before = len(dev_outbox()); ...; assert len(dev_outbox()) == before + 1` could see no
change at all. create_app() now clears the outbox for TESTING apps.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def test_create_app_testing_clears_the_dev_outbox():
    from app.services.mail import _dev_outbox, dev_outbox
    from app import create_app
    _dev_outbox.append({"to": "leftover@example.test", "subject": "from an earlier test module", "html": "<p>x</p>"})
    assert dev_outbox()
    create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True})
    assert dev_outbox() == []
