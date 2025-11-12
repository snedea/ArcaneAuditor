import asyncio
import importlib
import pytest

from web.server import UpdatePreferencesPayload, set_update_preferences_api
import web.server as server
from __version__ import __version__


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


def test_get_cached_health_respects_caching(monkeypatch):
    importlib.reload(server)

    monkeypatch.setattr(server, "get_update_prefs", lambda: {"enabled": True, "first_run_completed": True})

    call_count = {"value": 0}

    def fake_check(force=False):
        call_count["value"] += 1
        return {"update_available": False, "latest_version": "2.0.0", "current_version": __version__, "error": None}

    monkeypatch.setattr(server, "check_for_updates", fake_check)
    monkeypatch.setattr(server.time, "time", lambda: 1000.0)

    server._HEALTH_CACHE = {"latest_version": None, "error": None, "timestamp": 0.0}

    payload1 = server.get_cached_health(force=True)
    assert call_count["value"] == 1
    assert payload1["update_info"]["latest_version"] == "2.0.0"
    assert payload1["update_info"]["update_available"] is True

    monkeypatch.setattr(server.time, "time", lambda: 1001.0)
    payload2 = server.get_cached_health()

    assert call_count["value"] == 1
    assert payload2["update_info"]["latest_version"] == "2.0.0"

    monkeypatch.setattr(server, "__version__", "2.0.0")
    payload3 = server.get_cached_health()
    assert payload3["update_info"]["update_available"] is False


def test_get_cached_health_disabled(monkeypatch):
    importlib.reload(server)

    monkeypatch.setattr(server, "get_update_prefs", lambda: {"enabled": False, "first_run_completed": True})
    monkeypatch.setattr(server, "check_for_updates", lambda force=False: {"latest_version": "3.0.0", "current_version": __version__, "error": None})
    server._HEALTH_CACHE = {"latest_version": None, "error": None, "timestamp": 0.0}

    payload = server.get_cached_health(force=True)

    assert payload["status"] == "healthy"
    assert payload["version"] == __version__
    assert "update_info" not in payload

