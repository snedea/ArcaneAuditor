# Plan: P1.2 -- Create src/models.py with Pydantic Models and Custom Exceptions

Date: 2026-02-26
Version: v1
Status: planning

## Context

This is the second task in Phase 1 (Foundation). P1.1 (pyproject.toml, src/__init__.py, tests/__init__.py) is complete. This task creates the core data models that every other module depends on: scanner, runner, reporter, and fixer all consume or produce these models.

## Current State

- `pyproject.toml` exists with pydantic>=2.0 as a dependency
- `src/__init__.py` exists (one-line docstring)
- `tests/__init__.py` exists (empty)
- No `src/models.py` or `tests/test_models.py` exist yet

## Parent Tool JSON Output (the source of truth for Finding fields)

The parent Arcane Auditor at `../` outputs JSON with this structure:

```json
{
  "summary": {
    "total_files": 3,
    "total_rules": 42,
    "total_findings": 2,
    "findings_by_severity": {"ACTION": 1, "ADVICE": 1}
  },
  "findings": [
    {
      "rule_id": "ScriptConsoleLogRule",
      "severity": "ACTION",
      "message": "Console.log statement found in script",
      "file_path": "myapp.pmd",
      "line": 42
    }
  ],
  "context": { ... }
}
```

Severity values are exactly `"ACTION"` and `"ADVICE"`. Exit codes: 0 (clean), 1 (issues found), 2 (usage error), 3 (runtime error).

## Files to Create

### 1. `src/models.py` (NEW)

The single models file containing all Pydantic models, enums, and custom exceptions.

#### Imports

```python
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, SecretStr
```

#### Enums

**`Severity`** (str, Enum):
- `ACTION = "ACTION"`
- `ADVICE = "ADVICE"`

**`ReportFormat`** (str, Enum):
- `JSON = "json"`
- `SARIF = "sarif"`
- `GITHUB_ISSUES = "github_issues"`
- `PR_COMMENT = "pr_comment"`

**`Confidence`** (str, Enum):
- `HIGH = "HIGH"`
- `MEDIUM = "MEDIUM"`
- `LOW = "LOW"`

Use `str, Enum` (not StrEnum) for Python 3.10+ compat as stated in CLAUDE.md conventions, though pyproject.toml requires 3.12+. Using `str, Enum` is fine and conventional with Pydantic v2.

**`ExitCode`** (int, Enum):
- `CLEAN = 0`
- `ISSUES_FOUND = 1`
- `USAGE_ERROR = 2`
- `RUNTIME_ERROR = 3`

#### Models

**`Finding`** (BaseModel):
Mirrors a single finding from the parent tool's JSON output.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `rule_id` | `str` | required | e.g. `"ScriptConsoleLogRule"` |
| `severity` | `Severity` | required | `ACTION` or `ADVICE` |
| `message` | `str` | required | Human-readable description |
| `file_path` | `str` | required | Relative path to the file |
| `line` | `int` | `0` | Line number (0 = unknown) |

- Use `model_config = ConfigDict(frozen=True)` so findings are hashable/immutable.
- Add a `description` property that returns `message` (the IMPL_PLAN mentions `description` as a field, but the parent tool's JSON uses `message` as the description). Use `@property` to alias it for convenience.

**`ScanResult`** (BaseModel):
Represents the full output of running Arcane Auditor on a repo/path.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `repo` | `str` | required | Repo name or local path |
| `timestamp` | `datetime` | `Field(default_factory=datetime.utcnow)` | When scan ran |
| `findings_count` | `int` | required | Total findings |
| `findings` | `list[Finding]` | required | List of findings |
| `exit_code` | `ExitCode` | required | Parent tool exit code |

- Add a `@property` named `has_issues` that returns `self.exit_code == ExitCode.ISSUES_FOUND`.
- Add a `@property` named `action_count` that returns count of ACTION-severity findings.
- Add a `@property` named `advice_count` that returns count of ADVICE-severity findings.

**`FixResult`** (BaseModel):
Represents the result of applying a fix template to a finding.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `finding` | `Finding` | required | The finding being fixed |
| `original_content` | `str` | required | File content before fix |
| `fixed_content` | `str` | required | File content after fix |
| `confidence` | `Confidence` | required | HIGH, MEDIUM, or LOW |

- Add a `@property` named `is_auto_applicable` that returns `self.confidence == Confidence.HIGH`.

**`AgentConfig`** (BaseModel):
Configuration for the agent system.

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `repos` | `list[str]` | `[]` | GitHub repos to scan |
| `config_preset` | `str \| None` | `None` | Arcane Auditor config preset name |
| `output_format` | `ReportFormat` | `ReportFormat.JSON` | Default output format |
| `github_token` | `SecretStr \| None` | `None` | GitHub PAT, optional |
| `auditor_path` | `Path` | `Path("../")` | Path to parent Arcane Auditor |

- Use `SecretStr` for `github_token` to prevent accidental logging.
- The `auditor_path` default assumes agents/ is a subdirectory of the parent project.

#### Custom Exceptions

All inherit from a common base for easy catch-all when needed.

```python
class ArcaneAgentError(Exception):
    """Base exception for all agent errors."""

class ScanError(ArcaneAgentError):
    """Raised when scanning for Extend artifacts fails."""

class RunnerError(ArcaneAgentError):
    """Raised when invoking Arcane Auditor subprocess fails."""

class ReporterError(ArcaneAgentError):
    """Raised when formatting or delivering a report fails."""

class FixerError(ArcaneAgentError):
    """Raised when applying a fix template fails."""
```

Each exception:
- Has a Google-style docstring (one line).
- Inherits from `ArcaneAgentError` (not directly from `Exception`).
- No custom `__init__` needed -- standard `Exception(message)` suffices.

### 2. `tests/test_models.py` (NEW)

Test file validating all models, enums, and exceptions.

#### Imports

```python
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.models import (
    AgentConfig,
    ArcaneAgentError,
    Confidence,
    ExitCode,
    Finding,
    FixerError,
    FixResult,
    ReportFormat,
    ReporterError,
    RunnerError,
    ScanError,
    ScanResult,
    Severity,
)
```

#### Test Cases

**Enum tests:**
- `test_severity_values`: Assert `Severity.ACTION.value == "ACTION"` and `Severity.ADVICE.value == "ADVICE"`.
- `test_report_format_values`: Assert all 4 ReportFormat enum values match expected strings.
- `test_confidence_values`: Assert HIGH, MEDIUM, LOW string values.
- `test_exit_code_values`: Assert 0, 1, 2, 3 integer values.

**Finding tests:**
- `test_finding_creation`: Create a Finding with all fields, assert values match.
- `test_finding_default_line`: Create a Finding without `line`, assert it defaults to 0.
- `test_finding_frozen`: Create a Finding, attempt to mutate `rule_id`, assert `ValidationError` is raised.
- `test_finding_from_parent_json`: Create a Finding using `model_validate()` with a dict matching the parent tool's JSON output format. Assert all fields parsed correctly.
- `test_finding_invalid_severity`: Attempt to create a Finding with `severity="INVALID"`, assert `ValidationError`.

**ScanResult tests:**
- `test_scan_result_creation`: Create with required fields, assert values.
- `test_scan_result_timestamp_default`: Create without explicit timestamp, assert `timestamp` is a `datetime` instance and is recent.
- `test_scan_result_has_issues_property`: Create with `exit_code=ExitCode.ISSUES_FOUND`, assert `has_issues` is True. Create with `exit_code=ExitCode.CLEAN`, assert `has_issues` is False.
- `test_scan_result_action_advice_counts`: Create with a mix of ACTION and ADVICE findings, assert `action_count` and `advice_count` return correct values.

**FixResult tests:**
- `test_fix_result_creation`: Create with all fields, assert values.
- `test_fix_result_is_auto_applicable`: Assert True for HIGH confidence, False for MEDIUM and LOW.

**AgentConfig tests:**
- `test_agent_config_defaults`: Create with no args, assert `repos == []`, `config_preset is None`, `output_format == ReportFormat.JSON`, `github_token is None`.
- `test_agent_config_with_token`: Create with `github_token="ghp_test123"`, assert `github_token.get_secret_value() == "ghp_test123"` and `str(github_token) != "ghp_test123"` (SecretStr masks the value).
- `test_agent_config_auditor_path`: Create with `auditor_path=Path("/custom/path")`, assert it stores correctly.

**Exception tests:**
- `test_exceptions_inherit_from_base`: Assert all four exceptions are subclasses of `ArcaneAgentError`.
- `test_exceptions_inherit_from_exception`: Assert `ArcaneAgentError` is a subclass of `Exception`.
- `test_exception_messages`: Raise each exception with a message, catch it, assert `str(exc) == message`.
- `test_catch_all_base_exception`: Raise `ScanError`, catch with `except ArcaneAgentError`, assert it's caught.

## Dependencies

No new dependencies needed. All imports come from:
- `pydantic` (already in pyproject.toml as `pydantic>=2.0`)
- Python stdlib (`datetime`, `enum`, `pathlib`, `typing`)
- `pytest` (already in dev dependencies)

## Docker / Config Changes

None required.

## Verification Steps

From the `agents/` directory:

```bash
# 1. Verify the module imports cleanly
uv run python -c "from src.models import Finding, ScanResult, FixResult, AgentConfig, ReportFormat, Severity, Confidence, ExitCode, ScanError, RunnerError, ReporterError, FixerError, ArcaneAgentError; print('All imports OK')"

# 2. Run the tests
uv run pytest tests/test_models.py -v

# 3. Verify no type errors (optional, if mypy/pyright available)
uv run python -c "
from src.models import Finding, Severity
f = Finding(rule_id='TestRule', severity=Severity.ACTION, message='test', file_path='test.pmd', line=1)
print(f'Finding: {f.rule_id}, frozen={f.model_config.get(\"frozen\", False)}')
print(f'Description property: {f.description}')
"
```

All tests must pass. Zero findings from the test suite itself.

## Implementation Notes for Builder

1. **`from __future__ import annotations`** must be the first import in both files (per CLAUDE.md).
2. **Frozen Finding model**: Use `model_config = ConfigDict(frozen=True)` from pydantic, not `class Config`.
3. **SecretStr**: Import from `pydantic`, not a third-party lib.
4. **Severity enum validation**: Pydantic v2 validates enum fields automatically when the type is `Severity`. No custom validator needed.
5. **`description` property on Finding**: The IMPL_PLAN lists `description` as a field, but the parent tool's JSON has `rule_description` as a separate concept (the rule's class-level DESCRIPTION, not the finding's message). Map `description` as a property returning `self.message` to keep the interface the IMPL_PLAN expects without diverging from the parent JSON format.
6. **No `print()` calls**: Per CLAUDE.md, use `logging` module only. Models shouldn't log at all.
7. **Google-style docstrings**: Required on all public classes and the module itself.
