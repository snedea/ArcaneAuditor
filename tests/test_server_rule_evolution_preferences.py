import asyncio
import importlib
import pytest

import web.routes.preferences as preferences_module


def test_get_rule_evolution_preferences(monkeypatch):
    """Test GET endpoint for rule evolution preferences."""
    monkeypatch.setattr("utils.preferences_manager.get_new_rule_default_enabled", lambda: True)
    importlib.reload(preferences_module)
    
    response = asyncio.run(preferences_module.get_rule_evolution_preferences_api())
    
    assert response["new_rule_default_enabled"] is True


def test_get_rule_evolution_preferences_default_false(monkeypatch):
    """Test GET endpoint with default enabled set to False."""
    monkeypatch.setattr("utils.preferences_manager.get_new_rule_default_enabled", lambda: False)
    importlib.reload(preferences_module)
    
    response = asyncio.run(preferences_module.get_rule_evolution_preferences_api())
    
    assert response["new_rule_default_enabled"] is False


def test_set_rule_evolution_preferences(monkeypatch):
    """Test POST endpoint for setting rule evolution preferences."""
    stored = {"value": None}
    
    def fake_set(enabled):
        stored["value"] = enabled
        return True
    
    monkeypatch.setattr("utils.preferences_manager.set_new_rule_default_enabled", fake_set)
    importlib.reload(preferences_module)
    
    response = asyncio.run(preferences_module.set_rule_evolution_preferences_api(
        preferences_module.RuleEvolutionPreferencesPayload(new_rule_default_enabled=True)
    ))
    
    assert response["success"] is True
    assert stored["value"] is True


def test_set_rule_evolution_preferences_disabled(monkeypatch):
    """Test POST endpoint for disabling new rule default."""
    stored = {"value": None}
    
    def fake_set(enabled):
        stored["value"] = enabled
        return True
    
    monkeypatch.setattr("utils.preferences_manager.set_new_rule_default_enabled", fake_set)
    importlib.reload(preferences_module)
    
    response = asyncio.run(preferences_module.set_rule_evolution_preferences_api(
        preferences_module.RuleEvolutionPreferencesPayload(new_rule_default_enabled=False)
    ))
    
    assert response["success"] is True
    assert stored["value"] is False

