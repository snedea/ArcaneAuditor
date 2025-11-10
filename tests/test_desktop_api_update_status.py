import pytest

from __version__ import __version__
from arcane_auditor_desktop import Api, _show_confirmation


def test_get_health_status_disabled_updates(monkeypatch):
    api = Api("127.0.0.1", 8080)

    monkeypatch.setattr(
        "utils.preferences_manager.get_update_prefs",
        lambda: {"enabled": False, "first_run_completed": True},
    )

    result = api.get_health_status()

    assert result["status"] == "healthy"
    assert result["version"] == __version__
    assert "update_info" not in result
    assert "update_error" not in result


def test_get_health_status_with_update(monkeypatch):
    api = Api("127.0.0.1", 8080)

    monkeypatch.setattr(
        "utils.preferences_manager.get_update_prefs",
        lambda: {"enabled": True, "first_run_completed": True},
    )

    update_payload = {
        "update_available": True,
        "latest_version": "9.9.9",
        "current_version": "1.2.3",
        "error": None,
    }

    monkeypatch.setattr(
        "utils.update_checker.check_for_updates",
        lambda force=False: update_payload,
    )

    result = api.get_health_status()

    assert result["status"] == "healthy"
    assert result["version"] == __version__
    assert result["update_info"] == update_payload


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

