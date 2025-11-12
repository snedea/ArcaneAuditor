import pytest

from __version__ import __version__
from arcane_auditor_desktop import Api, _show_confirmation


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_get_health_status_disabled_updates(monkeypatch):
    api = Api("127.0.0.1", 8080)

    payload = {"status": "healthy", "version": __version__}
    monkeypatch.setattr("requests.get", lambda url, timeout=3: DummyResponse(payload))

    result = api.get_health_status()

    assert result == payload


def test_get_health_status_with_update(monkeypatch):
    api = Api("127.0.0.1", 8080)

    update_payload = {
        "update_available": True,
        "latest_version": "9.9.9",
        "current_version": "1.2.3",
        "error": None,
    }

    payload = {
        "status": "healthy",
        "version": __version__,
        "update_info": update_payload,
    }

    monkeypatch.setattr("requests.get", lambda url, timeout=3: DummyResponse(payload))

    result = api.get_health_status()

    assert result == payload


def test_get_health_status_first_run_not_completed(monkeypatch):
    api = Api("127.0.0.1", 8080)

    payload = {"status": "healthy", "version": __version__}

    monkeypatch.setattr("requests.get", lambda url, timeout=3: DummyResponse(payload))

    result = api.get_health_status()

    assert result == payload


def test_show_confirmation_handles_closed_window():
    class ClosedWindow:
        def __init__(self):
            self.closed = True
            self.confirm_calls = []

        def evaluate_js(self, script):
            raise RuntimeError("window closed")

        def create_confirmation_dialog(self, title, message):
            self.confirm_calls.append((title, message))
            return False

    window = ClosedWindow()

    result = _show_confirmation(
        window,
        "Enable Update Detection?",
        "Would you like Arcane Auditor to occasionally check for new versions?",
    )

    assert result is False
    assert len(window.confirm_calls) == 0


def test_show_confirmation_falls_back_on_eval_failure():
    class BrokenWindow:
        def __init__(self):
            self.closed = False
            self.eval_calls = 0
            self.confirm_calls = []

        def evaluate_js(self, script):
            self.eval_calls += 1
            raise RuntimeError("lost bridge")

        def set_on_top(self, value):
            return None

    window = BrokenWindow()

    result = _show_confirmation(
        window,
        "Enable Update Detection?",
        "Would you like Arcane Auditor to occasionally check for new versions?",
    )

    assert result is False
    assert window.eval_calls >= 1


def test_api_set_update_preferences(monkeypatch):
    captured = {}

    monkeypatch.setattr(
        "utils.preferences_manager.get_update_prefs",
        lambda: {"enabled": False, "first_run_completed": True},
    )

    def fake_set(prefs):
        captured.update(prefs)
        return True

    monkeypatch.setattr("utils.preferences_manager.set_update_prefs", fake_set)

    api = Api("127.0.0.1", 8080)
    result = api.set_update_preferences(True)

    assert result["success"] is True
    assert captured["enabled"] is True

