# CLAUDE.md -- Arcane Auditor Agent System

## Project Overview

This is the **agent wrapper** for Arcane Auditor, the deterministic code review tool for Workday Extend applications. The agent system automates scanning GitHub repos, running the 42 validation rules, and reporting/fixing findings.

**Critical principle**: The LLM never judges code quality. The 42 deterministic rules do that. The LLM is plumbing -- it finds files, invokes the tool, formats output, and applies fix templates.

## Tech Stack

- Python 3.10+ with `from __future__ import annotations` in every file
- Type hints everywhere -- no exceptions
- Typer for CLI (matches parent project)
- Pydantic v2 for all data models
- pytest for testing
- PyGithub for GitHub API interactions

## Project Structure

```
agents/
├── src/           # Source code
│   ├── cli.py     # Entry point
│   ├── scanner.py # Find Extend artifacts in repos
│   ├── runner.py  # Execute Arcane Auditor
│   ├── reporter.py # Format results
│   ├── fixer.py   # Apply fix templates
│   ├── config.py  # Configuration
│   └── models.py  # Pydantic models
├── fix_templates/ # Deterministic fix templates per rule
├── tests/         # pytest tests
│   └── fixtures/  # Test Extend apps
└── pyproject.toml
```

## Coding Conventions

1. **Imports**: Use `from __future__ import annotations` as first import in every .py file
2. **Models**: All data structures must be Pydantic BaseModel subclasses
3. **Error handling**: Raise specific exceptions, never catch-all. Define custom exceptions in models.py
4. **Logging**: Use `logging` module, never `print()` (the parent project uses print, we do not)
5. **Subprocess calls**: Always use `subprocess.run()` with `capture_output=True, text=True, check=False`. Parse exit codes explicitly (0=clean, 1=issues, 2=usage error, 3=crash)
6. **Paths**: Use `pathlib.Path` everywhere, never string paths
7. **Tests**: Every module gets a test file. Use fixtures in `tests/fixtures/`
8. **Docstrings**: Google style. Required on all public functions and classes

## Parent Project Integration

The parent Arcane Auditor lives at `../` (one directory up from `agents/`). Key commands:

```bash
# Run a scan (from parent directory)
cd .. && uv run main.py review-app <path> --format json --output report.json --quiet

# Exit codes
# 0 = clean (or ADVICE only)
# 1 = ACTION issues found
# 2 = usage error
# 3 = runtime error
```

The `runner.py` module invokes this as a subprocess. It MUST:
- Use `--format json` for machine-readable output
- Use `--quiet` to suppress console noise
- Parse the JSON output into Pydantic models
- Handle all 4 exit codes explicitly

## Fix Template Rules

Fix templates must be **deterministic** -- given the same input, they always produce the same output. No LLM creativity in fixes.

Each fix template:
1. Takes a `Finding` (from Arcane Auditor JSON output) and the source file content
2. Returns the modified source file content (or None if the fix cannot be applied safely)
3. Has a confidence level: HIGH (always safe), MEDIUM (usually safe), LOW (needs review)

Only HIGH confidence fixes are applied automatically. MEDIUM and LOW are suggested in PR comments.

## Testing Strategy

- `tests/fixtures/clean_app/` -- minimal Extend app with zero violations
- `tests/fixtures/dirty_app/` -- one or more violations per rule (known violations)
- `tests/fixtures/expected/` -- expected JSON output for each fixture

Every test:
1. Runs the scanner on a fixture
2. Invokes the runner
3. Verifies findings match expected output exactly
4. (For fixer tests) Verifies fix produces clean output when re-scanned

## Git Conventions

- Conventional commits: `feat(agents):`, `fix(agents):`, `test(agents):`
- Never push to `origin` (technovangelist). Push to `snedea` remote only
- Never commit `.env`, credentials, or API keys

## CI/CD Considerations

The agent system must work in these contexts:
1. **Local CLI** -- developer runs it manually
2. **GitHub Actions** -- triggered on PR, push, or schedule
3. **Context Foundry loop** -- the foundry loop builds this project
4. **Cron job** -- periodic scanning of repos

All four contexts use the same `cli.py` entry point with different flags.
