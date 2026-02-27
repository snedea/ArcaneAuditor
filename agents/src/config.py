"""Load and validate AgentConfig from YAML/JSON files with environment variable overrides."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.models import AgentConfig, ConfigError

logger = logging.getLogger(__name__)


def load_config(config_path: Path | None = None) -> AgentConfig:
    """Load AgentConfig from a YAML or JSON file (or defaults), apply env var overrides, then validate.

    Args:
        config_path: Path to a YAML or JSON config file. If None, uses defaults.

    Returns:
        A validated AgentConfig instance.

    Raises:
        ConfigError: If the config file is missing, malformed, or fails validation.
    """
    raw: dict = {}

    if config_path is not None:
        if not config_path.exists():
            raise ConfigError(f"Config file not found: {config_path}")

        text = config_path.read_text(encoding="utf-8")

        if config_path.suffix in (".yaml", ".yml"):
            try:
                raw = yaml.safe_load(text)
            except yaml.YAMLError as e:
                raise ConfigError(f"Failed to parse YAML config: {e}") from e
            if raw is None:
                raw = {}
            elif not isinstance(raw, dict):
                raise ConfigError(
                    f"Config file must contain a YAML mapping at the top level, got {type(raw).__name__}"
                )
        elif config_path.suffix == ".json":
            try:
                raw = json.loads(text)
            except json.JSONDecodeError as e:
                raise ConfigError(f"Failed to parse JSON config: {e}") from e
            if not isinstance(raw, dict):
                raise ConfigError(
                    f"Config file must contain a JSON object at the top level, got {type(raw).__name__}"
                )
        else:
            raise ConfigError(
                f"Unsupported config format: {config_path.suffix}. Use .yaml, .yml, or .json"
            )

    github_token_env = os.environ.get("GITHUB_TOKEN", "").strip()
    if github_token_env:
        raw["github_token"] = github_token_env

    auditor_path_env = os.environ.get("ARCANE_AUDITOR_PATH", "").strip()
    if auditor_path_env:
        raw["auditor_path"] = auditor_path_env

    try:
        config = AgentConfig(**raw)
    except ValidationError as e:
        raise ConfigError(f"Invalid configuration: {e}") from e

    validate_config(config)

    logger.debug("Config loaded: auditor_path=%s, repos=%d", config.auditor_path, len(config.repos))

    return config


def validate_config(config: AgentConfig) -> None:
    """Check that the Arcane Auditor path exists and contains main.py.

    Args:
        config: The AgentConfig to validate.

    Raises:
        ConfigError: If the auditor path or main.py is missing.
    """
    auditor_path = config.auditor_path.resolve()

    if not auditor_path.exists():
        raise ConfigError(f"Arcane Auditor path does not exist: {auditor_path}")

    if not auditor_path.is_dir():
        raise ConfigError(f"Arcane Auditor path is not a directory: {auditor_path}")

    main_py = auditor_path / "main.py"
    if not main_py.exists():
        raise ConfigError(f"main.py not found in Arcane Auditor path: {auditor_path}")

    logger.debug("Arcane Auditor validated at %s", auditor_path)
