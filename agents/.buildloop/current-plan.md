# Plan: P1.3

## Status: ALREADY IMPLEMENTED -- verify and close

`src/config.py` and `tests/test_config.py` were written in a prior WIP commit
(`21e9e7a`) but P1.3 is still marked `[ ]` in IMPL_PLAN.md. The builder must
verify correctness, run tests, and mark the task complete. No new code to write.

## Dependencies
- list: [] (pyyaml is already in pyproject.toml; all deps installed)
- commands: [] (no new installs needed)

## File Operations (in execution order)

### 1. VERIFY src/config.py
- operation: VERIFY (read-only, no changes expected)
- reason: Confirm the WIP implementation satisfies the P1.3 spec before closing

#### Functions present (confirm each exists with correct signature)

- signature: `load_config(config_path: Path | None = None) -> AgentConfig`
  - purpose: Load AgentConfig from YAML/JSON file (or defaults), apply env overrides, validate
  - logic:
    1. Initialize `raw: dict = {}`
    2. If `config_path` is not None:
       a. Raise `ConfigError` if `config_path.exists()` is False (message must contain "Config file not found")
       b. Read file text with `config_path.read_text(encoding="utf-8")`
       c. If suffix in `(".yaml", ".yml")`: call `yaml.safe_load(text)`, raise `ConfigError` on `yaml.YAMLError`, raise `ConfigError` if result is not a dict (message must contain "must contain a YAML mapping"), treat `None` result as `{}`
       d. If suffix is `".json"`: call `json.loads(text)`, raise `ConfigError` on `json.JSONDecodeError`, raise `ConfigError` if result is not a dict
       e. Else: raise `ConfigError` with message containing "Unsupported config format"
    3. Read `os.environ.get("GITHUB_TOKEN", "").strip()` -- if non-empty, set `raw["github_token"]`
    4. Read `os.environ.get("ARCANE_AUDITOR_PATH", "").strip()` -- if non-empty, set `raw["auditor_path"]`
    5. Construct `AgentConfig(**raw)`, wrapping `pydantic.ValidationError` in `ConfigError`
    6. Call `validate_config(config)`
    7. Log at DEBUG level: `"Config loaded: auditor_path=%s, repos=%d"`
    8. Return `config`
  - returns: `AgentConfig`
  - error handling: All errors raise `ConfigError` (never raw `ValidationError`, `yaml.YAMLError`, or `json.JSONDecodeError`)

- signature: `validate_config(config: AgentConfig) -> None`
  - purpose: Assert the auditor path exists and contains main.py
  - logic:
    1. `auditor_path = config.auditor_path.resolve()`
    2. If not `auditor_path.exists()`: raise `ConfigError` with message containing "does not exist"
    3. If not `auditor_path.is_dir()`: raise `ConfigError` with message containing "not a directory"
    4. `main_py = auditor_path / "main.py"` -- if not `main_py.exists()`: raise `ConfigError` with message containing "main.py not found"
    5. Log at DEBUG level: `"Arcane Auditor validated at %s"`
  - returns: `None`
  - error handling: Raises `ConfigError` for all three failure conditions

#### Guard behavior to confirm
- Whitespace-only `GITHUB_TOKEN` env var (`"   "`) must NOT be applied (`.strip()` makes it falsy)
- Whitespace-only `ARCANE_AUDITOR_PATH` env var must NOT be applied
- Empty YAML file (`yaml.safe_load` returns `None`) must result in `raw = {}`, not a crash

### 2. VERIFY tests/test_config.py
- operation: VERIFY (read-only, no changes expected)
- reason: Confirm the 13 tests cover the spec; no gaps that would block close

#### Tests to confirm present
1. `test_load_config_defaults` -- no file, env sets ARCANE_AUDITOR_PATH
2. `test_load_config_yaml` -- reads .yaml file
3. `test_load_config_json` -- reads .json file
4. `test_load_config_unsupported_extension` -- .toml raises ConfigError
5. `test_load_config_missing_file` -- nonexistent path raises ConfigError
6. `test_env_var_github_token_override` -- GITHUB_TOKEN sets github_token
7. `test_env_var_whitespace_github_token_ignored` -- "   " is ignored
8. `test_validate_config_missing_auditor_path` -- nonexistent dir raises ConfigError
9. `test_validate_config_missing_main_py` -- dir without main.py raises ConfigError
10. `test_validate_config_valid` -- valid dir + main.py returns None
11. `test_load_config_invalid_yaml` -- malformed YAML raises ConfigError
12. `test_load_config_non_mapping_yaml` -- list YAML raises ConfigError
13. `test_load_config_empty_yaml_uses_defaults` -- empty file uses defaults

### 3. MODIFY IMPL_PLAN.md
- operation: MODIFY
- reason: Mark P1.3 complete after tests pass
- anchor: `- [ ] P1.3: Create src/config.py -- load AgentConfig from a YAML or JSON file, with defaults.`

#### Change
Replace:
```
- [ ] P1.3: Create src/config.py -- load AgentConfig from a YAML or JSON file, with defaults. Support environment variable overrides for GITHUB_TOKEN and ARCANE_AUDITOR_PATH. Validate that the parent Arcane Auditor path exists and main.py is present
```
With:
```
- [x] P1.3: Create src/config.py -- load AgentConfig from a YAML or JSON file, with defaults. Support environment variable overrides for GITHUB_TOKEN and ARCANE_AUDITOR_PATH. Validate that the parent Arcane Auditor path exists and main.py is present
```

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv sync`
- lint: (no linter configured -- skip)
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/test_config.py -v`
- smoke: All 13 tests must pass with exit code 0. If any fail, diagnose and fix `src/config.py` before marking IMPL_PLAN.md complete.

## Constraints
- Do NOT modify ARCHITECTURE.md, CLAUDE.md, or any file other than IMPL_PLAN.md (after tests pass)
- Do NOT add new dependencies
- Do NOT rewrite src/config.py unless a test is failing and the fix is in config.py, not the test
- If a test is wrong (e.g., wrong match string), fix the test, not the implementation -- only if the implementation actually satisfies the P1.3 spec
- The IMPL_PLAN.md checkbox must only be flipped to [x] after `pytest tests/test_config.py` exits 0
