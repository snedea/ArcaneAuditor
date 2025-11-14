import asyncio
import importlib
import pytest

from web.server import RuleEvolutionPreferencesPayload, set_rule_evolution_preferences_api, get_rule_evolution_preferences_api
import web.server as server


def test_get_rule_evolution_preferences(monkeypatch):
    """Test GET endpoint for rule evolution preferences."""
    importlib.reload(server)
    
    monkeypatch.setattr(server, "get_new_rule_default_enabled", lambda: True)
    
    response = asyncio.run(get_rule_evolution_preferences_api())
    
    assert response["new_rule_default_enabled"] is True


def test_get_rule_evolution_preferences_default_false(monkeypatch):
    """Test GET endpoint with default enabled set to False."""
    importlib.reload(server)
    
    monkeypatch.setattr(server, "get_new_rule_default_enabled", lambda: False)
    
    response = asyncio.run(get_rule_evolution_preferences_api())
    
    assert response["new_rule_default_enabled"] is False


def test_set_rule_evolution_preferences(monkeypatch):
    """Test POST endpoint for setting rule evolution preferences."""
    stored = {"value": None}
    
    def fake_set(enabled):
        stored["value"] = enabled
        return True
    
    monkeypatch.setattr(server, "set_new_rule_default_enabled", fake_set)
    
    response = asyncio.run(set_rule_evolution_preferences_api(
        RuleEvolutionPreferencesPayload(new_rule_default_enabled=True)
    ))
    
    assert response["success"] is True
    assert stored["value"] is True


def test_set_rule_evolution_preferences_disabled(monkeypatch):
    """Test POST endpoint for disabling new rule default."""
    stored = {"value": None}
    
    def fake_set(enabled):
        stored["value"] = enabled
        return True
    
    monkeypatch.setattr(server, "set_new_rule_default_enabled", fake_set)
    
    response = asyncio.run(set_rule_evolution_preferences_api(
        RuleEvolutionPreferencesPayload(new_rule_default_enabled=False)
    ))
    
    assert response["success"] is True
    assert stored["value"] is False

