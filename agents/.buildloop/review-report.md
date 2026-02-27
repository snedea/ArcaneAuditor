# Review Report — P1.3

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv sync` resolved cleanly, no new deps needed)
- Lint: PASS (`ruff check` on `src/config.py`, `src/models.py`, `tests/test_config.py` -- all clean)
- Tests: PASS (13/13 passed in `pytest tests/test_config.py -v`)
- Docker: SKIPPED (no Docker files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "tests/test_config.py",
      "line": 1,
      "issue": "No test for invalid JSON config. The json.JSONDecodeError handler at src/config.py:52-53 is completely untested. The plan specifies test_load_config_invalid_yaml but omits the JSON equivalent. A regression in this path (e.g., catching bare Exception instead of JSONDecodeError) would go undetected. The YAML and JSON parsing paths are symmetric in config.py but only YAML error handling is exercised.",
      "category": "error-handling"
    },
    {
      "file": "tests/test_config.py",
      "line": 1,
      "issue": "No test verifies env var wins over file value when both are present. The plan states 'env vars always win over file values' (current-plan.md line 61) and the constraint repeats it (line 243). The existing tests either set auditor_path only in the file (with env var deleted) or only via env var (not in the file). No test exercises the conflict: file has auditor_path=/file/path AND ARCANE_AUDITOR_PATH=/env/path -- the env var should overwrite. If the env var block were moved above the file-parsing block, this contract would silently invert with no test failure.",
      "category": "api-contract"
    }
  ],
  "low": [
    {
      "file": "src/models.py",
      "line": 107,
      "issue": "AgentConfig has no model_config = ConfigDict(extra='forbid'). Unrecognized keys in a YAML or JSON config file (e.g., 'github_tken' as a typo) are silently dropped by Pydantic v2's default extra='ignore'. Users get no feedback that their config key was unrecognized.",
      "category": "inconsistency"
    },
    {
      "file": "tests/test_config.py",
      "line": 1,
      "issue": "No test for whitespace-only ARCANE_AUDITOR_PATH env var. test_env_var_whitespace_github_token_ignored exists for GITHUB_TOKEN but there is no equivalent for ARCANE_AUDITOR_PATH. The implementation at config.py:67-69 handles it correctly (strips then guards), but it is untested.",
      "category": "error-handling"
    },
    {
      "file": "src/config.py",
      "line": 101,
      "issue": "main_py.exists() does not assert the path is a file. A directory literally named 'main.py' inside auditor_path would pass validation. Should be main_py.is_file() to match the documented intent ('main.py is present').",
      "category": "logic"
    }
  ],
  "validated": [
    "All 13 tests pass with pytest 9.0.2 on Python 3.12.12",
    "ruff reports zero lint violations across all three changed files",
    "from __future__ import annotations present in both src/config.py and tests/test_config.py",
    "yaml.safe_load None guard (empty YAML -> {}) is present and tested",
    "Non-mapping YAML (list at top level) raises ConfigError -- present and tested",
    "Non-object JSON at top level raises ConfigError -- present and tested",
    "Whitespace-only GITHUB_TOKEN is stripped and ignored before being set in raw dict",
    "ARCANE_AUDITOR_PATH env var strip+guard mirrors GITHUB_TOKEN pattern",
    "validate_config uses .resolve() before existence checks -- relative Path('../') resolves correctly",
    "validate_config checks exists(), is_dir(), and main.py presence in that order",
    "ConfigError is raised (not re-used from pydantic.ValidationError) with from e chaining",
    "No print() calls -- logging module used exclusively",
    "No string paths -- pathlib.Path used everywhere",
    "IMPL_PLAN.md change is only marking P1.2 complete (- [ ] -> - [x]), not a P1.3 modification",
    "Default auditor_path=Path('../') smoke test resolves to /Users/name/homelab/ArcaneAuditor which contains main.py",
    "Pydantic ValidationError is caught and re-raised as ConfigError with context chaining"
  ]
}
```
