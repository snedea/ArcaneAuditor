# Plan: P1.3

## Dependencies
- list: [pyyaml>=6.0 (already in pyproject.toml -- no new deps needed)]
- commands: []

## File Operations (in execution order)

### 1. MODIFY src/models.py
- operation: MODIFY
- reason: Add ConfigError exception so config.py can raise it for missing/invalid config files and invalid auditor paths
- anchor: `class FixerError(ArcaneAgentError):`

#### Functions
- No new functions -- only add a new exception class after the existing ones.

#### Structs / Types
- Add after the `FixerError` class (the last exception in the file):
  ```python
  class ConfigError(ArcaneAgentError):
      """Raised when configuration is missing, malformed, or fails validation."""
  ```

#### Wiring / Integration
- `ConfigError` will be imported by `src/config.py` via `from src.models import AgentConfig, ConfigError`

---

### 2. CREATE src/config.py
- operation: CREATE
- reason: Load AgentConfig from YAML or JSON file with defaults, apply env var overrides, validate auditor path

#### Imports / Dependencies
```python
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import yaml

from src.models import AgentConfig, ConfigError
```

#### Functions

- signature: `def load_config(config_path: Path | None = None) -> AgentConfig:`
  - purpose: Load AgentConfig from a YAML or JSON file (or defaults if no path given), apply env var overrides, then validate.
  - logic:
    1. Initialize `raw: dict = {}` as an empty dict.
    2. If `config_path` is not None:
       a. If `config_path` does not exist (i.e., `not config_path.exists()`), raise `ConfigError(f"Config file not found: {config_path}")`.
       b. Read the file text: `text = config_path.read_text(encoding="utf-8")`.
       c. If `config_path.suffix` is `.yaml` or `.yml`, set `raw = yaml.safe_load(text)`. If `yaml.safe_load` returns `None` (empty file), set `raw = {}`.
       d. If `config_path.suffix` is `.json`, set `raw = json.loads(text)`.
       e. If `config_path.suffix` is anything else, raise `ConfigError(f"Unsupported config format: {config_path.suffix}. Use .yaml, .yml, or .json")`.
    3. Apply environment variable overrides:
       a. Read `github_token_env = os.environ.get("GITHUB_TOKEN", "").strip()`. If `github_token_env` is non-empty, set `raw["github_token"] = github_token_env`.
       b. Read `auditor_path_env = os.environ.get("ARCANE_AUDITOR_PATH", "").strip()`. If `auditor_path_env` is non-empty, set `raw["auditor_path"] = auditor_path_env`.
    4. Construct `config = AgentConfig(**raw)`. If Pydantic raises `ValidationError`, catch it and re-raise as `ConfigError(f"Invalid configuration: {e}")`.
    5. Call `validate_config(config)`.
    6. Log at DEBUG level: `logger.debug("Config loaded: auditor_path=%s, repos=%d", config.auditor_path, len(config.repos))`.
    7. Return `config`.
  - calls: `validate_config(config)`
  - returns: `AgentConfig`
  - error handling:
    - `config_path` not None but file missing -> raise `ConfigError` (step 2a)
    - unsupported file extension -> raise `ConfigError` (step 2e)
    - `yaml.safe_load` raises `yaml.YAMLError` -> catch and re-raise as `ConfigError(f"Failed to parse YAML config: {e}")`
    - `json.loads` raises `json.JSONDecodeError` -> catch and re-raise as `ConfigError(f"Failed to parse JSON config: {e}")`
    - `AgentConfig(**raw)` raises `pydantic.ValidationError` -> catch and re-raise as `ConfigError(f"Invalid configuration: {e}")`

- signature: `def validate_config(config: AgentConfig) -> None:`
  - purpose: Check that the Arcane Auditor path exists and contains main.py. Raise ConfigError if not.
  - logic:
    1. Resolve the auditor path to absolute: `auditor_path = config.auditor_path.resolve()`.
    2. If `not auditor_path.exists()`, raise `ConfigError(f"Arcane Auditor path does not exist: {auditor_path}")`.
    3. If `not auditor_path.is_dir()`, raise `ConfigError(f"Arcane Auditor path is not a directory: {auditor_path}")`.
    4. `main_py = auditor_path / "main.py"`. If `not main_py.exists()`, raise `ConfigError(f"main.py not found in Arcane Auditor path: {auditor_path}")`.
    5. Log at DEBUG level: `logger.debug("Arcane Auditor validated at %s", auditor_path)`.
    6. Return (None).
  - calls: nothing external
  - returns: `None`
  - error handling: raises `ConfigError` on path or file missing (steps 2, 3, 4)

#### Module-level setup
- After imports and before function definitions, add:
  ```python
  logger = logging.getLogger(__name__)
  ```

#### Wiring / Integration
- `load_config` is the only public entry point. It will be called by `src/cli.py` (future task P5.1) to build the `AgentConfig` used throughout the pipeline.
- No other existing files need modification for this task.

---

### 3. CREATE tests/test_config.py
- operation: CREATE
- reason: Every module must have a test file per CLAUDE.md convention

#### Imports / Dependencies
```python
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml

from src.config import load_config, validate_config
from src.models import AgentConfig, ConfigError, ReportFormat
```

#### Test functions

- signature: `def test_load_config_defaults(tmp_path: Path) -> None:`
  - purpose: Calling load_config(None) returns AgentConfig with defaults when ARCANE_AUDITOR_PATH points to a valid path.
  - logic:
    1. Create a fake auditor dir: `auditor_dir = tmp_path / "auditor"`, `auditor_dir.mkdir()`, `(auditor_dir / "main.py").write_text("# stub")`.
    2. Set `os.environ["ARCANE_AUDITOR_PATH"] = str(auditor_dir)`.
    3. Call `config = load_config(None)`.
    4. Assert `config.repos == []`.
    5. Assert `config.config_preset is None`.
    6. Assert `config.output_format == ReportFormat.JSON`.
    7. Assert `config.github_token is None`.
    8. Clean up env var with `del os.environ["ARCANE_AUDITOR_PATH"]` (or use monkeypatch).
  - note: Use `monkeypatch.setenv` from pytest fixtures to avoid leaving env vars behind.

- signature: `def test_load_config_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
  - purpose: load_config reads a YAML file and populates AgentConfig fields.
  - logic:
    1. Create a fake auditor dir and `main.py` stub as in test above.
    2. Write a YAML config file at `tmp_path / "config.yaml"` with content:
       ```yaml
       repos:
         - owner/repo1
       config_preset: production-ready
       output_format: json
       ```
    3. Set `ARCANE_AUDITOR_PATH` env var to `str(auditor_dir)` via `monkeypatch.setenv`.
    4. Call `config = load_config(tmp_path / "config.yaml")`.
    5. Assert `config.repos == ["owner/repo1"]`.
    6. Assert `config.config_preset == "production-ready"`.
    7. Assert `config.output_format == ReportFormat.JSON`.

- signature: `def test_load_config_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
  - purpose: load_config reads a JSON file and populates AgentConfig fields.
  - logic:
    1. Create a fake auditor dir and `main.py` stub.
    2. Write a JSON config file at `tmp_path / "config.json"` with content `{"repos": ["a/b"], "auditor_path": str(auditor_dir)}`.
    3. Call `config = load_config(tmp_path / "config.json")` (no env var override needed since auditor_path is in the JSON).
    4. Assert `config.repos == ["a/b"]`.

- signature: `def test_load_config_unsupported_extension(tmp_path: Path) -> None:`
  - purpose: load_config raises ConfigError for unsupported file extensions.
  - logic:
    1. Create a file `tmp_path / "config.toml"` with any text content.
    2. Call `load_config(tmp_path / "config.toml")` and expect it to raise `ConfigError`.
    3. Assert the exception message contains "Unsupported config format".

- signature: `def test_load_config_missing_file(tmp_path: Path) -> None:`
  - purpose: load_config raises ConfigError when the config file does not exist.
  - logic:
    1. Call `load_config(tmp_path / "nonexistent.yaml")` and expect it to raise `ConfigError`.
    2. Assert the exception message contains "Config file not found".

- signature: `def test_env_var_github_token_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
  - purpose: GITHUB_TOKEN env var overrides github_token in the loaded config.
  - logic:
    1. Create fake auditor dir with `main.py`.
    2. Write a minimal YAML config with no `github_token` field at `tmp_path / "config.yaml"`. Set `auditor_path` to `str(auditor_dir)` in the YAML.
    3. Set `monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_token")`.
    4. Call `config = load_config(tmp_path / "config.yaml")`.
    5. Assert `config.github_token` is not None.
    6. Assert `config.github_token.get_secret_value() == "ghp_test_token"`.

- signature: `def test_env_var_whitespace_github_token_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
  - purpose: A whitespace-only GITHUB_TOKEN env var is not applied (guards against pattern 8).
  - logic:
    1. Create fake auditor dir with `main.py`.
    2. Write minimal YAML config with `auditor_path` set to auditor dir.
    3. Set `monkeypatch.setenv("GITHUB_TOKEN", "   ")`.
    4. Call `config = load_config(tmp_path / "config.yaml")`.
    5. Assert `config.github_token is None`.

- signature: `def test_validate_config_missing_auditor_path(tmp_path: Path) -> None:`
  - purpose: validate_config raises ConfigError when auditor_path does not exist.
  - logic:
    1. Create `config = AgentConfig(auditor_path=tmp_path / "nonexistent")`.
    2. Call `validate_config(config)` and expect `ConfigError`.
    3. Assert message contains "does not exist".

- signature: `def test_validate_config_missing_main_py(tmp_path: Path) -> None:`
  - purpose: validate_config raises ConfigError when auditor_path exists but contains no main.py.
  - logic:
    1. Create a directory: `empty_dir = tmp_path / "auditor"`, `empty_dir.mkdir()`.
    2. Create `config = AgentConfig(auditor_path=empty_dir)`.
    3. Call `validate_config(config)` and expect `ConfigError`.
    4. Assert message contains "main.py not found".

- signature: `def test_validate_config_valid(tmp_path: Path) -> None:`
  - purpose: validate_config returns None (no exception) when auditor_path and main.py both exist.
  - logic:
    1. Create `auditor_dir = tmp_path / "auditor"`, `auditor_dir.mkdir()`, `(auditor_dir / "main.py").write_text("# stub")`.
    2. Create `config = AgentConfig(auditor_path=auditor_dir)`.
    3. Call `validate_config(config)` -- assert it does not raise (no assertion needed beyond no exception).

- signature: `def test_load_config_invalid_yaml(tmp_path: Path) -> None:`
  - purpose: load_config raises ConfigError for malformed YAML.
  - logic:
    1. Write a file at `tmp_path / "bad.yaml"` with content `": invalid: yaml: content: [unclosed"`.
    2. Call `load_config(tmp_path / "bad.yaml")` and expect `ConfigError`.
    3. Assert message contains "Failed to parse YAML config".

- signature: `def test_load_config_empty_yaml_uses_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:`
  - purpose: An empty YAML file results in default AgentConfig values (not an error).
  - logic:
    1. Create fake auditor dir with `main.py`.
    2. Write an empty file at `tmp_path / "empty.yaml"` (zero bytes).
    3. Set `monkeypatch.setenv("ARCANE_AUDITOR_PATH", str(auditor_dir))`.
    4. Call `config = load_config(tmp_path / "empty.yaml")`.
    5. Assert `config.repos == []`.

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.config import load_config, validate_config; print('import ok')"`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_config.py -v`
- smoke: Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.config import load_config; c = load_config(); print('auditor_path:', c.auditor_path.resolve())"` -- should print the resolved path to `../` (one directory up from `agents/`) without error, because `../main.py` exists at `/Users/name/homelab/ArcaneAuditor/main.py`.

## Constraints
- Do NOT add any new entries to `pyproject.toml` -- `pyyaml` is already present.
- Do NOT modify `IMPL_PLAN.md`, `CLAUDE.md`, or `ARCHITECTURE.md`.
- Do NOT add `print()` calls anywhere -- use `logging` only.
- Do NOT use string paths -- all path operations must use `pathlib.Path`.
- The `validate_config` function must resolve relative paths before checking existence (use `.resolve()`), so that the default `auditor_path=Path("../")` resolves correctly regardless of cwd.
- Do NOT catch bare `Exception` -- only catch `yaml.YAMLError`, `json.JSONDecodeError`, and `pydantic.ValidationError` specifically.
- The `load_config` function must apply env var overrides AFTER parsing the file, so env vars always win over file values.
- Do NOT import from `pydantic` directly in config.py for anything other than catching `ValidationError`. The `AgentConfig` model lives in `src/models.py`.
