import importlib
import json

import web.server as server


def test_get_dynamic_config_info_normalizes_rules(monkeypatch, tmp_path):
    server_module = importlib.reload(server)

    personal_dir = tmp_path / "personal"
    teams_dir = tmp_path / "teams"
    presets_dir = tmp_path / "presets"
    for directory in (personal_dir, teams_dir, presets_dir):
        directory.mkdir()

    config_path = personal_dir / "my-config.json"
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump({"rules": {"RuleA": {"enabled": True}}}, handle)

    production_rules = {
        "RuleA": {
            "enabled": True,
            "severity_override": None,
            "custom_settings": {"threshold": 10},
        },
        "RuleB": {
            "enabled": True,
            "severity_override": None,
            "custom_settings": {"threshold": 5},
        },
    }

    monkeypatch.setattr(
        server_module,
        "get_config_dirs",
        lambda: {
            "personal": str(personal_dir),
            "teams": str(teams_dir),
            "presets": str(presets_dir),
        },
    )
    monkeypatch.setattr(server_module, "get_new_rule_default_enabled", lambda: False)
    monkeypatch.setattr(server_module, "get_production_rules", lambda: production_rules)

    config_info = server_module.get_dynamic_config_info()

    key = "my-config_personal"
    assert key in config_info
    entry = config_info[key]

    assert entry["total_rules"] == 2
    assert entry["rules_count"] == 1  # Only RuleA stays enabled
    assert entry["rules"]["RuleB"]["enabled"] is False
    assert entry["rules"]["RuleB"]["custom_settings"]["threshold"] == 5

