from copy import deepcopy

from utils.config_normalizer import normalize_config_rules


PRODUCTION_SAMPLE = {
    "RuleA": {
        "enabled": True,
        "severity_override": None,
        "custom_settings": {"threshold": 10, "toggle": False},
    },
    "RuleB": {
        "enabled": True,
        "severity_override": "warning",
        "custom_settings": {},
    },
}


def test_normalize_injects_missing_rules():
    existing = {
        "RuleA": {
            "enabled": False,
            "custom_settings": {"threshold": 20},
        }
    }

    normalized = normalize_config_rules(
        existing, default_enabled=True, production_rules=deepcopy(PRODUCTION_SAMPLE)
    )

    assert normalized["RuleA"]["enabled"] is False
    assert normalized["RuleA"]["custom_settings"]["threshold"] == 20
    assert normalized["RuleA"]["custom_settings"]["toggle"] is False

    assert "RuleB" in normalized
    assert normalized["RuleB"]["enabled"] is True
    assert normalized["RuleB"]["severity_override"] == "warning"
    assert normalized["RuleB"]["custom_settings"] == {}

    # Ensure original data remains untouched
    assert existing["RuleA"]["custom_settings"] == {"threshold": 20}


def test_normalize_respects_default_disabled():
    normalized = normalize_config_rules(
        {},
        default_enabled=False,
        production_rules=deepcopy(PRODUCTION_SAMPLE),
    )

    assert normalized["RuleA"]["enabled"] is False
    assert normalized["RuleB"]["enabled"] is False


def test_normalize_preserves_custom_rules():
    existing = {
        "CustomRule": {
            "enabled": True,
            "severity_override": "info",
            "custom_settings": {"foo": "bar"},
        }
    }

    normalized = normalize_config_rules(
        existing,
        default_enabled=True,
        production_rules=deepcopy(PRODUCTION_SAMPLE),
    )

    assert "CustomRule" in normalized
    assert normalized["CustomRule"]["custom_settings"]["foo"] == "bar"

