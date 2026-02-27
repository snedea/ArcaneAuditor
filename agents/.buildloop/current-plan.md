# Plan: P7.1

## Pre-flight Verification

P7.1 is **already fully implemented** by a prior builder. All code and tests exist and pass (319/319 green).

### Evidence -- Existing Anchors

| Requirement | File | Anchor (unique line) | Status |
|---|---|---|---|
| `fix` command registered in Typer app | `src/cli.py:259` | `@app.command()` followed by `def fix(` | PRESENT |
| `--create-pr` flag | `src/cli.py:264` | `create_pr: bool = typer.Option(False, "--create-pr"` | PRESENT |
| `--target-dir` flag | `src/cli.py:263` | `target_dir: Optional[Path] = typer.Option(None, "--target-dir"` | PRESENT |
| Same args as scan (path, --repo, --config, --quiet) | `src/cli.py:261-266` | All 6 params present | PRESENT |
| Pipeline: scan -> audit | `src/cli.py:307-321` | `manifest = scan_local(path)` and `scan_result = run_audit(manifest, agent_config)` | PRESENT |
| Pipeline: fix | `src/cli.py:328-337` | `fix_results = fix_findings(scan_result, manifest.root_path)` | PRESENT |
| Pipeline: apply fixes | `src/cli.py:341-345` | `written = apply_fixes(fix_results, output_dir)` | PRESENT |
| Pipeline: re-audit to verify | `src/cli.py:350-362` | `reaudit_manifest = scan_local(reaudit_dir)` and `reaudit_result = run_audit(reaudit_manifest, agent_config)` | PRESENT |
| Pipeline: optional create PR | `src/cli.py:364-371` | `pr_url = _create_fix_pr(repo, token, manifest.root_path, written, scan_result, quiet)` | PRESENT |
| PR body builder helper | `src/cli.py:68` | `def _build_fix_pr_body(scan_result: ScanResult, written_files: list[Path]) -> str:` | PRESENT |
| PR creation helper (git + GitHub API) | `src/cli.py:100` | `def _create_fix_pr(repo: str, token: str, source_dir: Path, written_files: list[Path], scan_result: ScanResult, quiet: bool) -> str:` | PRESENT |
| Secure token handling (GIT_ASKPASS) | `src/cli.py:134` | `fd, askpass_path = tempfile.mkstemp(suffix=".py", prefix="arcane_askpass_")` | PRESENT |
| Argument validation tests (5 tests) | `tests/test_fix_command.py:82-121` | `class TestFixArgumentValidation:` | PRESENT |
| Pipeline tests (7 tests) | `tests/test_fix_command.py:129-237` | `class TestFixPipelineLocal:` | PRESENT |
| Exit code tests (5 tests) | `tests/test_fix_command.py:244-312` | `class TestFixExitCodes:` | PRESENT |
| Quiet flag test (1 test) | `tests/test_fix_command.py:320-338` | `class TestFixQuietFlag:` | PRESENT |

### Test Results

- `tests/test_fix_command.py`: **18/18 passed**
- `tests/test_cli.py`: **35/35 passed**
- Full suite: **319/319 passed** (0 failures, 0 errors)

## Dependencies

- list: [] (no new dependencies needed)
- commands: [] (no install commands needed)

## File Operations (in execution order)

### 1. MODIFY IMPL_PLAN.md

- operation: MODIFY
- reason: Mark P7.1 as complete (checkbox flip from `[ ]` to `[x]`)
- anchor: `- [ ] P7.1: Add \`fix\` command to cli.py -- accepts same args as scan`

#### Changes

Replace the single line:
```
- [ ] P7.1: Add `fix` command to cli.py -- accepts same args as scan, plus --create-pr flag and --target-dir for local output. Pipeline: scan -> audit -> fix -> (optional) re-audit to verify -> (optional) create PR with fixes
```

With:
```
- [x] P7.1: Add `fix` command to cli.py -- accepts same args as scan, plus --create-pr flag and --target-dir for local output. Pipeline: scan -> audit -> fix -> (optional) re-audit to verify -> (optional) create PR with fixes
```

No other files require modification. All code and tests are already implemented and passing.

## Verification

- build: `uv sync`
- lint: `uv run python -m py_compile src/cli.py`
- test: `uv run python -m pytest tests/test_fix_command.py tests/test_cli.py -v`
- smoke: `uv run python -m pytest --tb=short` (full suite, expect 319 passed, 0 failed)

## Constraints

- Do NOT modify any file in `src/` -- the implementation is complete and all tests pass
- Do NOT modify any file in `tests/` -- all 18 fix command tests pass
- Do NOT modify any file in `fix_templates/` -- no changes needed
- Do NOT modify ARCHITECTURE.md or CLAUDE.md
- The ONLY file change is the checkbox flip in IMPL_PLAN.md
