"""
Configuration normalization helpers.

Ensures that user-provided configuration rule sets stay aligned with the
production-ready baseline and that new rules are injected with the
appropriate default enabled state.
"""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from utils.arcane_paths import resource_path


@lru_cache(maxsize=1)
def _load_production_rules() -> Dict[str, Dict[str, Any]]:
    """Load the production-ready rule definitions once."""
    production_path = Path(
        resource_path("config/rules/presets/production-ready.json")
    )
    with production_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    rules = data.get("rules", {})
    if not isinstance(rules, dict):
        return {}
    return rules


def get_production_rules() -> Dict[str, Dict[str, Any]]:
    """
    Return a deep copy of the production-ready rules.

    Returns:
        Dict[str, Dict[str, Any]]: canonical rule definitions.
    """
    return deepcopy(_load_production_rules())


def _merge_custom_settings(
    base: Optional[Dict[str, Any]], overlay: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    base = deepcopy(base or {})
    overlay = overlay or {}
    if not overlay:
        return base
    merged = base
    for key, value in overlay.items():
        merged[key] = value
    return merged


def normalize_config_rules(
    config_rules: Optional[Dict[str, Dict[str, Any]]],
    default_enabled: bool,
    production_rules: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Normalize a rule configuration against the production baseline.

    Args:
        config_rules: Existing rule configuration mapping.
        default_enabled: If True, newly introduced rules default to the production
            enabled flag. If False, missing rules are added disabled.
        production_rules: Optional override of production rules (primarily for tests).

    Returns:
        Normalized mapping of rules.
    """
    production = (
        deepcopy(production_rules) if production_rules is not None else get_production_rules()
    )
    existing = deepcopy(config_rules or {})
    normalized: Dict[str, Dict[str, Any]] = {}

    for rule_name, production_rule in production.items():
        production_rule = production_rule or {}
        current_rule = existing.get(rule_name, {})

        normalized_rule: Dict[str, Any] = {}

        if "enabled" in current_rule:
            normalized_rule["enabled"] = bool(current_rule["enabled"])
        else:
            production_enabled = bool(production_rule.get("enabled", True))
            normalized_rule["enabled"] = production_enabled if default_enabled else False

        if "severity_override" in current_rule:
            normalized_rule["severity_override"] = current_rule["severity_override"]
        else:
            normalized_rule["severity_override"] = production_rule.get("severity_override")

        normalized_rule["custom_settings"] = _merge_custom_settings(
            production_rule.get("custom_settings"),
            current_rule.get("custom_settings"),
        )

        normalized[rule_name] = normalized_rule

    # Preserve any custom/non-production rules the user may have defined.
    for rule_name, rule_config in existing.items():
        if rule_name in normalized:
            continue
        normalized[rule_name] = deepcopy(rule_config)

    return normalized

