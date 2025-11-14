import importlib
import json

import utils.preferences_manager as preferences_manager


def _reload_with_tmp(monkeypatch, tmp_path):
    module = importlib.reload(preferences_manager)
    tmp_dir = tmp_path / "prefs"
    tmp_dir.mkdir()
    module.PREFERENCES_DIR = tmp_dir
    module.PREFERENCES_FILE = tmp_dir / "preferences.json"
    module.PREFERENCES_TMP = tmp_dir / "preferences.json.tmp"
    return module


def test_migrate_preferences_adds_rule_evolution(monkeypatch, tmp_path):
    prefs_module = _reload_with_tmp(monkeypatch, tmp_path)

    legacy_prefs = {
        "schema_version": 1,
        "ui": {"theme": "dark"},
        "updates": {
            "enabled": True,
            "first_run_completed": True,
            "last_checked": 0,
            "latest_version_cache": "",
        },
    }

    with prefs_module.PREFERENCES_FILE.open("w", encoding="utf-8") as handle:
        json.dump(legacy_prefs, handle)

    loaded = prefs_module.load_preferences()

    assert "rule_evolution" in loaded
    assert loaded["rule_evolution"]["new_rule_default_enabled"] is True


def test_set_new_rule_default_enabled_persists(monkeypatch, tmp_path):
    prefs_module = _reload_with_tmp(monkeypatch, tmp_path)

    assert prefs_module.get_new_rule_default_enabled() is True

    assert prefs_module.set_new_rule_default_enabled(False) is True
    assert prefs_module.get_new_rule_default_enabled() is False

    persisted = prefs_module.load_preferences()
    assert persisted["rule_evolution"]["new_rule_default_enabled"] is False

