# Plan: Arcane Auditor Agent System

Date: 2026-02-26
Version: v1
Status: planning

## Context

Chris (author of Arcane Auditor / Developers and Dragons) is skeptical of LLMs in code review because of non-determinism -- he saw Workday's LLM approach produce false positives and false negatives. His tool uses 42 deterministic rules instead.

Our goal: demonstrate that you CAN put deterministic rules in an LLM loop. The LLM is the transport layer, not the judge. The 42 rules are the judge. The LLM just automates running them, collecting results, and applying fix templates.

This is the "rest loop" -- the Context Foundry build loop will construct this agent system overnight while the developer sleeps.

## Current State

- Arcane Auditor v1.0 exists at `/Users/name/homelab/ArcaneAuditor/`
- 42 rules are fully implemented and tested (23 script, 19 structure)
- CLI supports `review-app` with JSON output and CI-friendly exit codes
- No automation wrapper exists yet
- Context Foundry loop is operational at `/Users/name/homelab/context-foundry/`

## The Core Argument (for Chris)

```
Traditional approach (what Workday did):
  LLM reads code -> LLM decides what's wrong -> non-deterministic, unreliable

Our approach:
  LLM finds files -> Deterministic rules run -> LLM formats output -> deterministic, repeatable
  LLM finds files -> Deterministic rules run -> Deterministic fix templates -> LLM applies templates -> deterministic fixes
```

The LLM touches code exactly twice:
1. To locate it (finding .pmd/.pod/.script files -- this is trivially deterministic)
2. To apply fix templates (regex-based transformations -- deterministic by construction)

The LLM NEVER evaluates code quality. That's what the 42 rules do.

## Implementation Steps

### Phase 1: Foundation (P1.1 - P1.3)
Scaffold the project with proper Python packaging, Pydantic models for all data structures, and configuration management. This is pure boilerplate -- no business logic.

### Phase 2: Scanner (P2.1 - P2.4)
Build the "eyes" of the agent -- finding Extend artifacts in local directories and GitHub repos. This is file I/O and git operations, nothing LLM-specific.

### Phase 3: Runner (P3.1 - P3.3)
Build the "hands" of the agent -- invoking `main.py review-app` as a subprocess and parsing its JSON output. This is the critical bridge between the agent and the deterministic rules.

### Phase 4: Reporter (P4.1 - P4.5)
Build the "voice" of the agent -- formatting findings as JSON, SARIF, GitHub issues, or PR comments. SARIF is the key format for GitHub Code Scanning integration.

### Phase 5: CLI (P5.1 - P5.3)
Wire it all together with a Typer CLI that supports scan/fix/watch modes.

### Phase 6: Fix Templates (P6.1 - P6.5)
Build the "closing the loop" piece -- deterministic fix templates that transform violations into clean code. Each template is a pure function: (violation, source) -> fixed_source.

### Phase 7: Full Loop (P7.1 - P7.4)
Wire the fix command, add GitHub Actions template, and prove the full loop works end-to-end.

### Phase 8: Documentation (P8.1 - P8.3)
Write the README, CLI help, and the philosophical document explaining why this works.

## Architecture Decisions

1. **Subprocess invocation over library import**: We invoke `main.py` as a subprocess rather than importing the parser module directly. This keeps the agent decoupled from Arcane Auditor's internals and means the agent works with any version of the tool.

2. **JSON output as the contract**: The `--format json` flag is the API contract between the agent and Arcane Auditor. If the JSON schema changes, only `models.py` needs updating.

3. **Fix templates over LLM generation**: Fix templates are regex/AST transformations, not LLM-generated code. This ensures determinism. The LLM's role is just to apply the right template to the right finding.

4. **SARIF for GitHub integration**: SARIF is the industry standard for static analysis results. GitHub Code Scanning accepts SARIF natively, making the agent's output immediately actionable in GitHub's security tab.

5. **Confidence levels on fixes**: HIGH = always safe to apply (var->let, remove console.log). MEDIUM = usually safe but should be reviewed. LOW = needs human review. Only HIGH is auto-applied.

## Risks & Open Questions

- The parent tool's JSON output format is not formally documented -- we'll need to reverse-engineer it from actual output
- GitHub API rate limits may affect the watch mode at scale
- Some fix templates (like string concatenation -> template literals) have edge cases that may not be HIGH confidence
- The SARIF spec is large -- we only need a subset but must validate against the schema
- Cross-file fixes (e.g., removing an unused include that's referenced elsewhere) are not safe for automated fixing

## Verification

After each phase:
1. `uv run pytest tests/` must pass
2. `uv run python -m agents.src.cli scan ../tests/` should work on Arcane Auditor's own test fixtures
3. The fix loop test (Phase 7.4) must show finding count decreasing after fixes
