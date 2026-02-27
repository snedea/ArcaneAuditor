# Plan: P5.2

## Status Assessment

The P5.1 builder already implemented the full P5.2 orchestration inside `src/cli.py`.
All eight P5.2 requirements are present in that file. No new code is needed.

This plan directs the BUILDER to:
1. Verify each P5.2 requirement against the existing `src/cli.py` implementation.
2. Confirm the build passes (import check, lint, tests).
3. Mark P5.2 as done in `IMPL_PLAN.md`.

---

## Dependencies

- list: []
- commands: []

---

## Pre-flight: Verify P5.2 Requirements Are Met

Before doing anything else, the BUILDER must read `src/cli.py` and confirm each of
the following is present. Reference line numbers are from the current file -- do NOT
blindly trust them; locate each item by its anchor text.

| # | Requirement | Anchor text in cli.py | Expected location |
|---|-------------|-----------------------|-------------------|
| 1 | If `path` is not None, call `scan_local(path)` | `if path is not None:` | ~line 102 |
| 2 | Else call `scan_github(repo, "main", token)` | `manifest = scan_github(repo,` | ~line 105 |
| 3 | `--pr` without `--repo` exits with code 2 | `if pr is not None and repo is None:` | ~line 79 |
| 4 | `run_audit(manifest, agent_config)` called | `scan_result = run_audit(manifest, agent_config)` | ~line 111 |
| 5 | `shutil.rmtree(manifest.temp_dir)` in `finally` | `finally:` then `shutil.rmtree` | ~lines 115-117 |
| 6 | Dispatch to `report_findings` / `format_github_issues` / `format_pr_comment` | `if format == CliFormat.GITHUB_ISSUES:` | ~line 120 |
| 7 | `output.write_text(formatted)` when `--output` given, else `typer.echo(formatted)` | `if output is not None:` | ~lines 131-136 |
| 8 | `raise typer.Exit(code=int(scan_result.exit_code))` as the final statement | `raise typer.Exit(code=int(scan_result.exit_code))` | ~line 138 |

If ALL 8 items are confirmed, proceed to File Operations below.

If any item is MISSING, add it to `src/cli.py` following the logic described here:

- Item 1 & 2 missing: inside the `scan()` function body, after all validation blocks,
  add:
  ```python
  try:
      if path is not None:
          manifest = scan_local(path)
      else:
          manifest = scan_github(repo, "main", token)
  except ScanError as exc:
      _error(str(exc))
      raise typer.Exit(code=int(ExitCode.USAGE_ERROR))
  ```

- Item 3 missing: add before the scan dispatch block:
  ```python
  if pr is not None and repo is None:
      _error("--pr requires --repo")
      raise typer.Exit(code=int(ExitCode.USAGE_ERROR))
  ```

- Item 4 & 5 missing: after the scan dispatch block, add:
  ```python
  try:
      scan_result = run_audit(manifest, agent_config)
  except RunnerError as exc:
      _error(str(exc))
      raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))
  finally:
      if manifest.temp_dir is not None:
          shutil.rmtree(manifest.temp_dir, ignore_errors=True)
  ```

- Item 6 missing: add after the audit block:
  ```python
  try:
      if report_fmt == CliFormat.GITHUB_ISSUES:
          urls = format_github_issues(scan_result, repo, token)
          formatted: str = "\n".join(urls) if urls else "No issues created."
      elif report_fmt == CliFormat.PR_COMMENT:
          formatted = format_pr_comment(scan_result, repo, pr, token)
      else:
          formatted = report_findings(scan_result, _FORMAT_MAP[report_fmt])
  except ReporterError as exc:
      _error(str(exc))
      raise typer.Exit(code=int(ExitCode.RUNTIME_ERROR))
  ```
  Note: use `report_fmt` not `format` to avoid shadowing the built-in.

- Item 7 missing: add after the formatting block:
  ```python
  if output is not None:
      output.write_text(formatted, encoding="utf-8")
      if not quiet:
          typer.echo(f"Output written to {output}", err=True)
  else:
      typer.echo(formatted)
  ```

- Item 8 missing: add as the final line of the `scan()` function body:
  ```python
  raise typer.Exit(code=int(scan_result.exit_code))
  ```

---

## File Operations (in execution order)

### 1. MODIFY IMPL_PLAN.md

- operation: MODIFY
- reason: Mark P5.2 as completed -- implementation verified in src/cli.py
- anchor: `- [ ] P5.2: Implement \`scan\` command orchestration`

#### Change

Replace exactly this line (including the leading `- [ ]`):

```
- [ ] P5.2: Implement `scan` command orchestration -- if path given, use scan_local; if --repo given, use scan_github; if --pr given, validate --repo is also given. After scanning, run audit, then format. Write to --output file or stdout. Return appropriate exit codes (mirror parent tool: 0, 1, 2, 3)
```

With:

```
- [x] P5.2: Implement `scan` command orchestration -- if path given, use scan_local; if --repo given, use scan_github; if --pr given, validate --repo is also given. After scanning, run audit, then format. Write to --output file or stdout. Return appropriate exit codes (mirror parent tool: 0, 1, 2, 3)
```

The only change is `[ ]` -> `[x]`. Do not alter any other line in IMPL_PLAN.md.

---

## Verification

- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.cli import app; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run ruff check src/cli.py`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -x -q 2>&1 | head -60`
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m src.cli scan --help` -- confirm output shows: `PATH`, `--repo`, `--pr`, `--format`, `--output`, `--config`, `--quiet` in the usage text

---

## Constraints

- Do NOT add any new source files.
- Do NOT modify `src/cli.py` unless a verification check above reveals a missing item.
- Do NOT modify `src/scanner.py`, `src/runner.py`, `src/reporter.py`, `src/models.py`, or `src/config.py`.
- Do NOT add or remove any dependencies in `pyproject.toml`.
- Do NOT modify any test files.
- Only modify `IMPL_PLAN.md` to flip the `[ ]` -> `[x]` for P5.2.
