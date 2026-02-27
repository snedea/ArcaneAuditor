# Arcane Auditor Agent System

Autonomous agent wrapper for [Arcane Auditor](../README.md) that scans Workday Extend repos, runs the 42 deterministic rules, reports findings, and applies fixes.

The LLM never judges code quality. The 42 rules do that. The LLM is plumbing -- it finds files, invokes the tool, formats output, and applies fix templates.

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (handles Python automatically)
- Git

## Setup

```bash
git clone https://github.com/snedea/ArcaneAuditor.git
cd ArcaneAuditor

# Install parent tool dependencies
uv sync

# Install agent dependencies
cd agents
uv sync
```

## Usage

All commands run from the `agents/` directory.

### Scan a local Extend app

```bash
# Human-readable summary
uv run python -m src /path/to/extend/app --format summary

# JSON output
uv run python -m src /path/to/extend/app --format json

# SARIF for GitHub Code Scanning
uv run python -m src /path/to/extend/app --format sarif --output report.sarif

# Write output to file
uv run python -m src /path/to/extend/app --format json --output results.json
```

### Scan a GitHub repo

Requires a `GITHUB_TOKEN` environment variable with repo read access.

```bash
# Summary of a repo's main branch
GITHUB_TOKEN=ghp_xxx uv run python -m src --repo owner/repo --format summary

# Create GitHub issues for each ACTION finding
GITHUB_TOKEN=ghp_xxx uv run python -m src --repo owner/repo --format github-issues

# Post a PR comment with findings
GITHUB_TOKEN=ghp_xxx uv run python -m src --repo owner/repo --pr 42 --format pr-comment
```

### Use a config preset

```bash
# Use the production-ready preset (stricter rules)
uv run python -m src /path/to/app --config production-ready --format summary

# Use a custom config file (absolute path)
uv run python -m src /path/to/app --config /path/to/my-config.json --format summary
```

### Quick test with built-in fixtures

```bash
# Should find 9 violations (3 ACTION, 6 ADVICE)
uv run python -m src tests/fixtures/dirty_app --format summary

# Should find 0 violations
uv run python -m src tests/fixtures/clean_app --format summary
```

## Output Formats

| Format | Flag | Description |
|---|---|---|
| JSON | `--format json` | Machine-readable ScanResult (default) |
| Summary | `--format summary` | Human-readable breakdown by severity, rule, and file |
| SARIF | `--format sarif` | SARIF v2.1.0 for GitHub Code Scanning integration |
| GitHub Issues | `--format github-issues` | Creates one issue per ACTION finding (requires `--repo`) |
| PR Comment | `--format pr-comment` | Posts a summary comment on a PR (requires `--repo` and `--pr`) |

## Exit Codes

| Code | Meaning |
|---|---|
| 0 | Clean -- no findings (or ADVICE only) |
| 1 | Issues found -- ACTION-level findings present |
| 2 | Usage error -- bad arguments or config |
| 3 | Runtime error -- tool crashed |

## Fix Templates

The agent includes 6 deterministic fix templates that auto-correct HIGH-confidence findings:

**Script fixes:**
- `VarToLetConst` -- replaces `var` with `let` or `const` (uses mutation analysis)
- `RemoveConsoleLog` -- removes `console.log/warn/error` calls
- `TemplateLiteralFix` -- converts string concatenation to template literals

**Structure fixes:**
- `LowerCamelCaseWidgetId` -- converts widget IDs to lowerCamelCase
- `LowerCamelCaseEndpointName` -- converts endpoint names to lowerCamelCase
- `AddFailOnStatusCodes` -- adds missing `failOnStatusCodes` to endpoints

Fix templates are applied via the `fixer` module. Only HIGH-confidence fixes are auto-applied; MEDIUM and LOW are reported as suggestions. The `fix` CLI command is not yet wired up (Phase 7).

## Adding a Fix Template

1. Create a class in `fix_templates/` that subclasses `FixTemplate`
2. Set `confidence = "HIGH"` (or `"MEDIUM"` / `"LOW"`)
3. Implement `match(finding)` to return `True` for your target rule
4. Implement `apply(finding, source_content)` to return a `FixResult`

The registry auto-discovers all `FixTemplate` subclasses at runtime.

## Project Structure

```
agents/
├── src/
│   ├── cli.py           # Typer CLI entry point
│   ├── scanner.py       # Find Extend artifacts locally or via GitHub clone
│   ├── runner.py        # Invoke parent Arcane Auditor as subprocess
│   ├── reporter.py      # Format results (JSON, SARIF, Summary, GitHub)
│   ├── fixer.py         # Apply fix templates to findings
│   ├── config.py        # YAML/JSON config loader with env var overrides
│   └── models.py        # Pydantic v2 models and enums
├── fix_templates/
│   ├── base.py          # FixTemplate ABC and registry
│   ├── script_fixes.py  # VarToLetConst, RemoveConsoleLog, TemplateLiteralFix
│   └── structure_fixes.py  # Widget ID, Endpoint Name, FailOnStatusCodes
├── tests/               # 301 tests
│   ├── fixtures/        # clean_app/ and dirty_app/ test Extend apps
│   └── ...
└── pyproject.toml
```

## Running Tests

```bash
cd agents
uv run pytest           # all 301 tests
uv run pytest -q        # quiet mode
uv run pytest -x        # stop on first failure
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GITHUB_TOKEN` | For GitHub features | GitHub personal access token with repo scope |
| `ARCANE_AUDITOR_PATH` | No | Override path to parent Arcane Auditor (default: `../`) |
