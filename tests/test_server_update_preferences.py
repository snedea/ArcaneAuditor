import asyncio
import pytest

from web.server import UpdatePreferencesPayload, set_update_preferences_api


def test_update_preferences_post(monkeypatch):
    stored = {"enabled": False, "first_run_completed": False}

    monkeypatch.setattr("web.server.get_update_prefs", lambda: stored.copy())

    def fake_set_update_prefs(new_prefs):
        stored.update(new_prefs)
        return True

    monkeypatch.setattr("web.server.set_update_prefs", fake_set_update_prefs)

    response = asyncio.run(set_update_preferences_api(UpdatePreferencesPayload(enabled=True)))

    assert response["success"] is True
    assert stored["enabled"] is True

