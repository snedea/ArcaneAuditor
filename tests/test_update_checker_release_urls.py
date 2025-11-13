import importlib

import utils.update_checker as update_checker


def _mock_update_storage(monkeypatch):
    monkeypatch.setattr(update_checker, "get_update_last_checked", lambda: None)
    monkeypatch.setattr(update_checker, "set_update_last_checked", lambda ts: None)
    monkeypatch.setattr(update_checker, "get_cached_latest_version", lambda: None)
    monkeypatch.setattr(update_checker, "set_cached_latest_version", lambda value: None)


def test_release_url_when_update_available(monkeypatch):
    importlib.reload(update_checker)

    _mock_update_storage(monkeypatch)
    monkeypatch.setattr(update_checker, "get_latest_version", lambda: "9.9.9")
    monkeypatch.setattr(update_checker, "__version__", "1.2.3", raising=False)

    result = update_checker.check_for_updates(force=True)

    assert result["update_available"] is True
    assert result["release_url"].endswith("/tag/v9.9.9")


def test_release_url_uses_cached_version_on_error(monkeypatch):
    importlib.reload(update_checker)

    monkeypatch.setattr(update_checker, "get_update_last_checked", lambda: None)
    monkeypatch.setattr(update_checker, "set_update_last_checked", lambda ts: None)
    monkeypatch.setattr(update_checker, "get_cached_latest_version", lambda: "8.8.8")
    monkeypatch.setattr(update_checker, "set_cached_latest_version", lambda value: None)

    monkeypatch.setattr(update_checker, "get_latest_version", lambda: None)
    monkeypatch.setattr(update_checker, "__version__", "7.7.7", raising=False)

    result = update_checker.check_for_updates(force=True)

    assert result["update_available"] is True
    assert result["release_url"].endswith("/tag/v8.8.8")

