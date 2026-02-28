# Arcane Auditor CLI -- Architecture

## Vision

Build a deterministic automation tool for Workday Extend code review that addresses Chris's (Developers and Dragons) concern about Workday's LLM-based approach: unreliable, non-repeatable results with false positives and missed violations.

This tool runs Arcane Auditor's 42 deterministic rules against Extend repos, reports findings, and applies mechanical fixes. The pipeline is:

1. **Scan** -- clone repos or walk local directories, find Extend artifacts (.pmd, .pod, .script, .amd, .smd)
2. **Audit** -- invoke `main.py review-app` as a subprocess, parse JSON output
3. **Report** -- format results as JSON, SARIF, GitHub issues, or PR comments
4. **Fix** -- apply deterministic regex/JSON transforms via fix templates

## Current State: No LLM at Runtime

As built, this tool uses **zero LLM inference at runtime**. The entire pipeline is deterministic Python -- subprocess calls, regex, JSON parsing, string formatting. There are no AI/ML dependencies in `pyproject.toml`. An LLM (Context Foundry) wrote the code, but the code itself never calls one.

This validates Chris's core claim: **the rules should be deterministic**. You don't want an LLM deciding whether `var` is bad -- that's a binary check. Same input, same output, every time, with 301 tests to prove it.

## Where Deterministic Rules Fall Short

Deterministic rules handle the "what's wrong" part. They don't handle "so what?"

What the 42 rules do well:
- Find known violations with zero false positives
- Produce consistent, reproducible results across runs
- Run in CI without surprises
- Apply safe, mechanical fixes (var -> let/const, remove console.log, fix naming)

What deterministic rules cannot do:
- **Explain context** -- why does this finding matter for *this specific app*?
- **Triage** -- you have 50 findings, which 3 should you fix first?
- **Prioritize by impact** -- a hardcoded WID in a checkout page matters more than one in a test helper
- **Handle follow-ups** -- "is this really a problem if I'm only using it in tests?"
- **Fix complex cases** -- the LOW-confidence findings that regex can't safely transform
- **Spot cross-file patterns** -- "you have this same anti-pattern in 12 files, here's a shared utility"
- **Write human-quality PR comments** -- not a linter dump, but a colleague's review

## Where an LLM Adds Value (Future)

The right architecture is layered: deterministic rules produce findings (source of truth), an LLM explains, prioritizes, and communicates them. The LLM never overrides or invents findings. It makes existing ones useful.

```
Layer 1: Deterministic Rules (Arcane Auditor)
  - Source of truth for all findings
  - Same input = same output, always
  - No LLM involvement

Layer 2: Deterministic Fixes (fix_templates/)
  - Regex/JSON transforms for HIGH-confidence cases
  - No LLM involvement

Layer 3: LLM Communication Layer (not yet built)
  - Triage: "fix these 3 first, the rest are cleanup"
  - Explain: "this hardcoded WID breaks when deployed to a different tenant"
  - Suggest: complex fixes that regex can't handle safely
  - Converse: answer developer questions about specific findings
```

The LLM layer would consume the same JSON output that the CLI produces today. It adds no new findings and removes none. It's a presentation and interaction layer, not a judgment layer.

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

### 1. Deterministic Rules as Source of Truth

All code quality decisions come from the 42 rules in the parent Arcane Auditor tool. The CLI automates running them -- it finds files, invokes the tool, formats the output, and applies fix templates. No judgment, no creativity, no inference.

### 2. Fix Templates Are Mechanical

Each fix template is a Python class with regex or JSON transforms. Same input, same output:
- `ScriptVarUsageRule` -> replace `var` with `let` (or `const` if never reassigned)
- `ScriptConsoleLogRule` -> remove `console.log` statements
- `WidgetIdLowerCamelCaseRule` -> convert ID to lowerCamelCase
- `EndpointNameLowerCamelCaseRule` -> convert name to lowerCamelCase

Only HIGH-confidence fixes auto-apply. If a template can't guarantee correctness, it returns None.

### 3. SARIF Output for GitHub Integration

SARIF (Static Analysis Results Interchange Format) is the standard for uploading static analysis results to GitHub Code Scanning. By outputting SARIF, the tool integrates natively with GitHub's security tab.

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
