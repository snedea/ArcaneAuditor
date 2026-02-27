# Review Report — P1.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -m py_compile src/config.py src/models.py`)
- Tests: PASS (14/14 passed — `uv run pytest tests/test_config.py -v`)
- Lint: SKIPPED (no linter configured in pyproject.toml)
- Docker: SKIPPED (no compose files changed)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/config.py",
      "line": 36,
      "issue": "read_text() is not wrapped in try/except. If the config file exists but is unreadable (PermissionError) or is a directory (IsADirectoryError on Unix), a raw OS exception propagates to the caller instead of ConfigError. The function's docstring contract states 'Raises: ConfigError: If the config file is missing, malformed, or fails validation' and the plan spec states 'All errors raise ConfigError'. Both are violated for I/O errors after the exists() guard.",
      "category": "api-contract"
    }
  ],
  "low": [
    {
      "file": "src/config.py",
      "line": 38,
      "issue": "Suffix comparison (.yaml, .yml, .json) is case-sensitive. A file named 'config.YAML' or 'config.YML' falls through to the else branch and raises 'Unsupported config format: .YAML' instead of being parsed as YAML. Unlikely in practice but diverges from conventional file-type detection.",
      "category": "inconsistency"
    },
    {
      "file": "src/models.py",
      "line": 114,
      "issue": "auditor_path defaults to Path('../'). This is a CWD-relative path that is correct only when the process runs from agents/. In GitHub Actions (where CWD is repo root by default) or any cron/CI setup not chdir-ing to agents/ first, '../' resolves to the repo's parent directory. validate_config() catches this and raises ConfigError immediately (fail-fast), but the error message does not hint at the CWD dependency, making diagnosis harder.",
      "category": "hardcoded"
    },
    {
      "file": "tests/test_config.py",
      "line": 55,
      "issue": "No test for JSON non-dict content (e.g., a JSON array '[1,2,3]' or null). The code path at config.py:54-57 raises ConfigError for non-dict JSON, but this branch has zero test coverage. The analogous YAML case (list YAML) is tested at line 178.",
      "category": "inconsistency"
    },
    {
      "file": ".buildloop/current-plan.md",
      "line": 58,
      "issue": "Plan enumerates 13 tests to confirm present, but the implementation has 14. test_env_var_whitespace_arcane_auditor_path_ignored (test_config.py:122) is absent from the plan's numbered list. Extra test is a net positive, but the count mismatch means the plan's verification checklist is stale.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "All 14 pytest tests pass with exit code 0",
    "from __future__ import annotations present in both config.py and models.py",
    "yaml.safe_load used (not yaml.load) — no YAML deserialization vulnerability",
    "GITHUB_TOKEN whitespace-only value stripped and ignored (config.py:63-65), backed by test at line 105",
    "ARCANE_AUDITOR_PATH whitespace-only value stripped and ignored (config.py:67-69), backed by test at line 122",
    "Empty YAML file (yaml.safe_load returns None) correctly treated as {} and uses defaults (config.py:43-44)",
    "yaml.YAMLError wrapped in ConfigError (config.py:41-42)",
    "json.JSONDecodeError wrapped in ConfigError (config.py:52-53)",
    "pydantic.ValidationError wrapped in ConfigError (config.py:73-74)",
    "validate_config checks exists(), is_dir(), and main.py presence in that order — no logic inversion",
    "env vars override file config (applied after raw dict is built from file)",
    "All public functions have Google-style docstrings",
    "logging module used throughout, no print() calls",
    "pathlib.Path used for all path operations, no string paths",
    "ConfigError defined in models.py and imported cleanly into config.py"
  ]
}
```
