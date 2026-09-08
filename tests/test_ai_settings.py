"""AI settings a firm can set for itself, and the precedence between them.

The precedence is the part worth pinning. An operator who set OPENROUTER_API_KEY or a
model in the server environment made a deliberate choice, and a Settings page that
silently overrode it would be a nasty surprise on a hosted instance. Equally, a firm that
switches zero-retention off must actually get that, not have it quietly turned back on.
"""
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
DB_PATH = os.path.join(ROOT, "data", "test_ai_settings.db")
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


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for k in ("OPENROUTER_API_KEY", "AI_OPENROUTER_MODEL", "AI_OPENROUTER_ZDR",
              "AI_OPENROUTER_NO_TRAINING", "AI_DAILY_CAP_CENTS"):
        monkeypatch.delenv(k, raising=False)


def _firm(app, **kw):
    from app.extensions import db
    from app.models import Firm
    with app.app_context():
        f = Firm.get()
        for k, v in kw.items():
            setattr(f, k, v)
        db.session.commit()


def test_a_firm_can_choose_its_own_model(app):
    import app.llm as llm
    _firm(app, ai_model="google/gemini-2.5-flash")
    with app.app_context():
        assert llm._setting("AI_OPENROUTER_MODEL") == "google/gemini-2.5-flash"


def test_the_environment_beats_the_settings_page(app, monkeypatch):
    """An operator pinning a model in .env made a decision the UI must not undo."""
    import app.llm as llm
    _firm(app, ai_model="google/gemini-2.5-flash")
    monkeypatch.setenv("AI_OPENROUTER_MODEL", "anthropic/claude-sonnet-5")
    with app.app_context():
        assert llm._setting("AI_OPENROUTER_MODEL") == "anthropic/claude-sonnet-5"


def test_turning_zero_retention_off_actually_turns_it_off(app):
    """False == 0 in Python, so an emptiness check would swallow this and switch it back on."""
    import app.llm as llm
    _firm(app, ai_zdr=False, ai_no_training=False)
    with app.app_context():
        assert llm._setting("AI_OPENROUTER_ZDR", "1") == "0"
        assert llm._setting("AI_OPENROUTER_NO_TRAINING", "1") == "0"


def test_zero_retention_is_on_for_a_firm_that_has_not_touched_it(app):
    import app.llm as llm
    _firm(app, ai_zdr=True, ai_no_training=True)
    with app.app_context():
        assert llm._setting("AI_OPENROUTER_ZDR", "1") == "1"


def test_the_routing_a_request_actually_carries_follows_the_firms_choice(app, monkeypatch):
    import app.llm as llm
    seen = {}

    class R:
        status_code = 200
        text = ""
        def json(self):
            return {"choices": [{"message": {"content": "ok"}}], "usage": {}}

    monkeypatch.setattr(llm.requests, "post",
                        lambda url, headers=None, json=None, timeout=None: (seen.update(p=json), R())[1])

    _firm(app, ai_zdr=True, ai_no_training=True, ai_api_key="firm-key")
    with app.app_context():
        llm._openrouter("google/gemini-2.5-flash", "hi", "", 64, None, None)
    assert seen["p"]["provider"] == {"zdr": True, "data_collection": "deny"}

    _firm(app, ai_zdr=False, ai_no_training=False)
    with app.app_context():
        llm._openrouter("google/gemini-2.5-flash", "hi", "", 64, None, None)
    assert "provider" not in seen["p"], "the firm switched the restriction off; it must be gone"


def test_a_firm_key_is_used_when_the_environment_has_none(app):
    import app.llm as llm
    _firm(app, ai_api_key="firm-supplied-key")
    with app.app_context():
        assert llm._setting("OPENROUTER_API_KEY") == "firm-supplied-key"
        assert llm.provider() == "openrouter"


def test_saving_settings_with_a_blank_key_does_not_wipe_the_stored_one(app):
    """The field is a password input; a blank save is the normal case, not a request to clear."""
    from app.models import Firm
    from tests.helpers import login
    _firm(app, ai_api_key="keep-me")
    c = app.test_client()
    tok = login(c)
    c.post("/settings", data={"name": "Demo Law PLLC", "ai_enabled": "1", "ai_api_key": "", "_csrf": tok})
    with app.app_context():
        assert Firm.get().ai_api_key == "keep-me"


def test_typing_none_clears_the_stored_key(app):
    from app.models import Firm
    from tests.helpers import login
    _firm(app, ai_api_key="remove-me")
    c = app.test_client()
    tok = login(c)
    c.post("/settings", data={"name": "Demo Law PLLC", "ai_enabled": "1", "ai_api_key": "none", "_csrf": tok})
    with app.app_context():
        assert Firm.get().ai_api_key == ""
