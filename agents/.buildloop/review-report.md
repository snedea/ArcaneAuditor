# Review Report — P7.1

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -m py_compile src/cli.py tests/test_fix_command.py` -- both clean)
- Tests: PASS (319 passed, 0 failed -- full suite including new 18 tests)
- Lint: PASS (`uv run ruff check src/cli.py tests/test_fix_command.py` -- all checks passed)
- Docker: SKIPPED (no Docker files changed in this task)

## Findings

```json
{
  "high": [],
  "medium": [
    {
      "file": "src/cli.py",
      "line": 339,
      "issue": "When --repo is used without --create-pr and without --target-dir, fixed files are silently discarded. output_dir is set to manifest.root_path (line 339), which for a GitHub clone equals manifest.temp_dir. apply_fixes writes into that directory, the user sees 'Applied N fix(es).' (line 348), and then the finally block at line 375-377 runs shutil.rmtree(manifest.temp_dir), deleting all fixed files. No warning is emitted. Confirmed by scanner.py:105+117-120 -- scan_github sets manifest.root_path = tmp_path and manifest.temp_dir = tmp_path (the same object). The --create-pr path is safe (push happens before finally), and --target-dir is safe (writes outside temp dir), but the --repo-only path produces useless output.",
      "category": "logic"
    }
  ],
  "low": [
    {
      "file": "src/cli.py",
      "line": 100,
      "issue": "The quiet parameter in _create_fix_pr signature is accepted but never read inside the function body. Plan step 8 for _create_fix_pr specifies: 'If not quiet, log the PR URL via typer.echo(f\"PR created: {url}\", err=True)'. That stderr informational message is absent. The quiet parameter is dead code. The PR URL is echoed unconditionally by the caller at line 371, which is correct for machine-readable output, but the quiet-suppressable status message is missing.",
      "category": "inconsistency"
    },
    {
      "file": "tests/test_fix_command.py",
      "line": 1,
      "issue": "Zero test coverage for _create_fix_pr. The function contains 4 subprocess calls each with distinct error handling, a GIT_ASKPASS tempfile lifecycle, and a PyGithub API call. None of this is exercised. The plan did not specify a TestFixPR class, so this is a plan gap rather than an implementation defect, but it is a notable audit gap for a function that touches secrets and external systems.",
      "category": "resource-leak"
    },
    {
      "file": "src/cli.py",
      "line": 162,
      "issue": "base='main' is hardcoded in repo_obj.create_pull(). Repos whose default branch is master, develop, or any other name will receive a GitHub API 422 (unprocessable entity) error, which is caught as FixerError and exits 3. The value is plan-specified but the limitation is undocumented and could surprise users of repos that do not use main as their default branch.",
      "category": "hardcoded"
    }
  ],
  "validated": [
    "Import block is complete and correct: subprocess, shutil, os, stat, github.Auth/Github/GithubException, src.fixer.apply_fixes/fix_findings, FixerError/ScanResult in models import",
    "Boolean Typer options use typer.Option(False, ...) pattern throughout -- no is_flag=True",
    "Validation order in fix command is correct: mutual exclusion checks before token extraction, token check before target_dir+create_pr check",
    "_create_fix_pr uses GIT_ASKPASS tempfile (chmod 700, deleted in finally) to avoid token in argv -- same pattern as scan_github in scanner.py",
    "manifest = None initialization at line 305 ensures the finally block at line 375 is safe even if scan_local/scan_github raises before manifest is assigned",
    "typer.Exit propagates through the outer try and correctly triggers the finally block for temp_dir cleanup in all code paths",
    "Re-audit manifest (from scan_local) never has temp_dir set (scanner.py:56 confirms scan_local returns ScanManifest without temp_dir), so no resource leak from re-audit",
    "All 18 new tests pass; all 319 suite tests pass",
    "fix --help smoke test shows --create-pr, --target-dir, and PATH as required by plan",
    "_DefaultScanGroup.parse_args correctly passes 'fix' invocations through unchanged since 'fix' is in self.commands"
  ]
}
```
