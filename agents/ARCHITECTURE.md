# Arcane Auditor Agent System -- Architecture

## Vision

Demonstrate that **deterministic rules can run reliably inside an LLM agent loop** without the false positive/negative problems Chris (Developers and Dragons) identified with Workday's LLM approach.

The key insight: the LLM never invents rules. It is a **transport and orchestration layer** that executes Arcane Auditor's existing 42 deterministic rules against real Workday Extend repos, then structures the results for humans. The LLM's job is:

1. **Navigate** -- clone repos, find Extend artifacts (.pmd, .pod, .script, .amd, .smd)
2. **Execute** -- invoke `main.py review-app` with appropriate config
3. **Report** -- parse JSON output, create structured GitHub issues or PR comments
4. **Fix** (Phase 2) -- propose deterministic fixes based on rule-specific fix templates

The LLM does NOT evaluate code quality. The 42 rules do that. The LLM is plumbing.

## Architecture Overview

```
agents/
├── ARCHITECTURE.md          # This file
├── CLAUDE.md                # Project conventions for the foundry loop
├── IMPL_PLAN.md             # Task checklist (foundry-compatible)
├── docs/                    # Detailed design docs
│   └── PLAN_agent-system.md # This implementation plan
├── src/
│   ├── __init__.py
│   ├── scanner.py           # GitHub repo scanner -- finds Extend artifacts
│   ├── runner.py            # Arcane Auditor execution wrapper
│   ├── reporter.py          # Findings -> structured reports (GitHub issues, PR comments, SARIF)
│   ├── fixer.py             # Deterministic fix generator (Phase 2)
│   ├── config.py            # Agent configuration (repos, rules, schedules)
│   ├── cli.py               # CLI entry point (Click/Typer)
│   └── models.py            # Pydantic models for scan results, reports
├── fix_templates/           # Deterministic fix templates per rule
│   ├── __init__.py
│   ├── script_fixes.py      # Fixes for script rules (var->let, template literals, etc.)
│   └── structure_fixes.py   # Fixes for structure rules (missing IDs, naming, etc.)
├── tests/
│   ├── __init__.py
│   ├── test_scanner.py
│   ├── test_runner.py
│   ├── test_reporter.py
│   ├── test_fixer.py
│   └── fixtures/            # Test Extend apps (minimal .pmd/.pod/.script samples)
│       ├── clean_app/       # App with no violations
│       ├── dirty_app/       # App with known violations per rule
│       └── expected/        # Expected JSON output for each fixture
├── pyproject.toml           # Python project config
└── README.md                # How to use the agent system
```

## Tech Stack

- **Language**: Python 3.10+ with type hints everywhere
- **CLI**: Typer (matches existing Arcane Auditor CLI)
- **Models**: Pydantic v2 for all data structures
- **GitHub**: PyGithub for API access (issues, PR comments, SARIF upload)
- **Testing**: pytest
- **Parent tool**: Arcane Auditor (invoked as subprocess via `uv run main.py`)

## Key Design Decisions

### 1. The LLM Never Judges Code

The agent system is a **wrapper** around `main.py review-app`. All code quality decisions come from the 42 deterministic rules. The LLM:
- Finds files to scan
- Invokes the tool
- Formats the output
- (Phase 2) Applies fix templates

This is the answer to Chris's concern: "I want something deterministic and repeatable." The rules ARE deterministic. The agent just automates running them.

### 2. Fix Templates Are Deterministic

Each rule has a corresponding fix template that produces exactly one correct fix. Examples:
- `ScriptVarUsageRule` -> replace `var` with `let` (or `const` if never reassigned)
- `ScriptConsoleLogRule` -> remove `console.log` statements
- `WidgetIdLowerCamelCaseRule` -> convert ID to lowerCamelCase
- `EndpointNameLowerCamelCaseRule` -> convert name to lowerCamelCase

The LLM applies these templates. It does NOT generate creative fixes.

### 3. SARIF Output for GitHub Integration

SARIF (Static Analysis Results Interchange Format) is the standard for uploading static analysis results to GitHub Code Scanning. By outputting SARIF, the agent integrates natively with GitHub's security tab.

### 4. Separation of Concerns

- `scanner.py` -- pure I/O (clone, find files)
- `runner.py` -- pure execution (invoke Arcane Auditor, parse JSON)
- `reporter.py` -- pure formatting (JSON -> issues, comments, SARIF)
- `fixer.py` -- pure transformation (finding + template -> fix)
- `cli.py` -- orchestration only

## Execution Modes

### Mode 1: Scan (Phase 1)
```bash
# Scan a local directory
python -m agents.src.cli scan ./my-extend-app --format sarif --output report.sarif

# Scan a GitHub repo
python -m agents.src.cli scan --repo owner/repo --format github-issues

# Scan and comment on a PR
python -m agents.src.cli scan --repo owner/repo --pr 42 --format pr-comment
```

### Mode 2: Fix (Phase 2)
```bash
# Generate fixes for all findings
python -m agents.src.cli fix ./my-extend-app --output ./fixed-app

# Generate fixes and create a PR
python -m agents.src.cli fix --repo owner/repo --create-pr
```

### Mode 3: Watch (Phase 3)
```bash
# Watch a repo for new PRs and auto-comment
python -m agents.src.cli watch --repo owner/repo --interval 300
```

## Integration with Context Foundry

This project is designed to be built by the Context Foundry loop:
1. IMPL_PLAN.md contains atomic, verifiable tasks
2. Each task produces testable output
3. Tests use fixtures with known violations
4. The foundry loop can build, review, and commit each task autonomously
