"""Tests for src/config module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.config import load_config, validate_config
from src.models import AgentConfig, ConfigError, ReportFormat


def test_load_config_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Calling load_config(None) returns AgentConfig with defaults when ARCANE_AUDITOR_PATH points to a valid path."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    monkeypatch.setenv("ARCANE_AUDITOR_PATH", str(auditor_dir))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    config = load_config(None)

    assert config.repos == []
    assert config.config_preset is None
    assert config.output_format == ReportFormat.JSON
    assert config.github_token is None


def test_load_config_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config reads a YAML file and populates AgentConfig fields."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({
        "repos": ["owner/repo1"],
        "config_preset": "production-ready",
        "output_format": "json",
    }))

    monkeypatch.setenv("ARCANE_AUDITOR_PATH", str(auditor_dir))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    config = load_config(tmp_path / "config.yaml")

    assert config.repos == ["owner/repo1"]
    assert config.config_preset == "production-ready"
    assert config.output_format == ReportFormat.JSON


def test_load_config_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """load_config reads a JSON file and populates AgentConfig fields."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"repos": ["a/b"], "auditor_path": str(auditor_dir)}))

    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("ARCANE_AUDITOR_PATH", raising=False)

    config = load_config(tmp_path / "config.json")

    assert config.repos == ["a/b"]


def test_load_config_unsupported_extension(tmp_path: Path) -> None:
    """load_config raises ConfigError for unsupported file extensions."""
    config_file = tmp_path / "config.toml"
    config_file.write_text("key = 'value'")

    with pytest.raises(ConfigError, match="Unsupported config format"):
        load_config(tmp_path / "config.toml")


def test_load_config_missing_file(tmp_path: Path) -> None:
    """load_config raises ConfigError when the config file does not exist."""
    with pytest.raises(ConfigError, match="Config file not found"):
        load_config(tmp_path / "nonexistent.yaml")


def test_env_var_github_token_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """GITHUB_TOKEN env var overrides github_token in the loaded config."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"auditor_path": str(auditor_dir)}))

    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")
    monkeypatch.delenv("ARCANE_AUDITOR_PATH", raising=False)

    config = load_config(tmp_path / "config.yaml")

    assert config.github_token is not None
    assert config.github_token.get_secret_value() == "ghp_test_token"


def test_env_var_whitespace_github_token_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A whitespace-only GITHUB_TOKEN env var is not applied."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml.dump({"auditor_path": str(auditor_dir)}))

    monkeypatch.setenv("GITHUB_TOKEN", "   ")
    monkeypatch.delenv("ARCANE_AUDITOR_PATH", raising=False)

    config = load_config(tmp_path / "config.yaml")

    assert config.github_token is None


def test_validate_config_missing_auditor_path(tmp_path: Path) -> None:
    """validate_config raises ConfigError when auditor_path does not exist."""
    config = AgentConfig(auditor_path=tmp_path / "nonexistent")

    with pytest.raises(ConfigError, match="does not exist"):
        validate_config(config)


def test_validate_config_missing_main_py(tmp_path: Path) -> None:
    """validate_config raises ConfigError when auditor_path exists but contains no main.py."""
    empty_dir = tmp_path / "auditor"
    empty_dir.mkdir()

    config = AgentConfig(auditor_path=empty_dir)

    with pytest.raises(ConfigError, match="main.py not found"):
        validate_config(config)


def test_validate_config_valid(tmp_path: Path) -> None:
    """validate_config returns None when auditor_path and main.py both exist."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    config = AgentConfig(auditor_path=auditor_dir)

    validate_config(config)


def test_load_config_invalid_yaml(tmp_path: Path) -> None:
    """load_config raises ConfigError for malformed YAML."""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text('": invalid: yaml: content: [unclosed')

    with pytest.raises(ConfigError, match="Failed to parse YAML config"):
        load_config(tmp_path / "bad.yaml")


def test_load_config_non_mapping_yaml(tmp_path: Path) -> None:
    """load_config raises ConfigError when YAML top-level value is a list, not a mapping."""
    list_yaml = tmp_path / "list.yaml"
    list_yaml.write_text("- item1\n- item2\n")

    with pytest.raises(ConfigError, match="must contain a YAML mapping"):
        load_config(tmp_path / "list.yaml")


def test_load_config_empty_yaml_uses_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty YAML file results in default AgentConfig values."""
    auditor_dir = tmp_path / "auditor"
    auditor_dir.mkdir()
    (auditor_dir / "main.py").write_text("# stub")

    empty_yaml = tmp_path / "empty.yaml"
    empty_yaml.write_text("")

    monkeypatch.setenv("ARCANE_AUDITOR_PATH", str(auditor_dir))
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    config = load_config(tmp_path / "empty.yaml")

    assert config.repos == []
