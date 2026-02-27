# Plan: P3.1

## Dependencies
- list: [] (no new packages -- uses stdlib json, subprocess, logging only)
- commands: [] (no install commands required)

## File Operations (in execution order)

### 1. CREATE src/runner.py
- operation: CREATE
- reason: Implements run_audit() to invoke the parent Arcane Auditor subprocess and parse its JSON output into ScanResult

#### Imports / Dependencies
- `from __future__ import annotations`
- `import json`
- `import logging`
- `import subprocess`
- `from pathlib import Path`
- `from pydantic import ValidationError`
- `from src.models import AgentConfig, ExitCode, Finding, RunnerError, ScanManifest, ScanResult`

#### Structs / Types (if applicable)
- None (all models already defined in src/models.py)

#### Module-level
- `logger = logging.getLogger(__name__)`

#### Functions

**Function 1:**
- signature: `def run_audit(scan_manifest: ScanManifest, config: AgentConfig) -> ScanResult`
  - purpose: Invoke Arcane Auditor on the manifest's root_path, parse JSON output, return ScanResult
  - logic:
    1. Resolve `auditor_path = config.auditor_path.resolve()`
    2. Build `cmd: list[str] = ["uv", "run", "main.py", "review-app", str(scan_manifest.root_path), "--format", "json", "--quiet"]`
    3. Log at DEBUG: `logger.debug("run_audit: path=%s auditor=%s", scan_manifest.root_path, auditor_path)`
    4. Enter a try/except block:
       - Call `result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=300, cwd=auditor_path)`
       - Catch `subprocess.TimeoutExpired`: raise `RunnerError(f"Arcane Auditor timed out after 300 seconds for path: {scan_manifest.root_path}")`
       - Catch `OSError as exc`: raise `RunnerError(f"Failed to invoke Arcane Auditor subprocess: {exc}") from exc`
    5. Log at DEBUG: `logger.debug("run_audit: returncode=%d stdout_len=%d stderr_len=%d", result.returncode, len(result.stdout), len(result.stderr))`
    6. If `result.returncode == ExitCode.USAGE_ERROR` (value 2): raise `RunnerError(f"Arcane Auditor usage error (exit 2) for path '{scan_manifest.root_path}': {(result.stdout.strip() or result.stderr.strip())[:500]}")`
    7. If `result.returncode == ExitCode.RUNTIME_ERROR` (value 3): raise `RunnerError(f"Arcane Auditor runtime error (exit 3) for path '{scan_manifest.root_path}': {(result.stderr.strip() or result.stdout.strip())[:500]}")`
    8. If `result.returncode not in (ExitCode.CLEAN, ExitCode.ISSUES_FOUND)` (i.e., not 0 or 1): raise `RunnerError(f"Arcane Auditor returned unexpected exit code {result.returncode} for path '{scan_manifest.root_path}'")`
    9. Call `data = _parse_json_output(result.stdout, scan_manifest.root_path)` (see Function 2 below)
    10. Call `findings = _build_findings(data, scan_manifest.root_path)` (see Function 3 below)
    11. Set `exit_code = ExitCode(result.returncode)`
    12. Set `repo = scan_manifest.repo if scan_manifest.repo is not None else str(scan_manifest.root_path)`
    13. Return `ScanResult(repo=repo, findings_count=len(findings), findings=findings, exit_code=exit_code)`
  - calls:
    - `subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=300, cwd=auditor_path)`
    - `_parse_json_output(result.stdout, scan_manifest.root_path)`
    - `_build_findings(data, scan_manifest.root_path)`
  - returns: `ScanResult`
  - error handling:
    - `subprocess.TimeoutExpired` -> raise `RunnerError`
    - `OSError` -> raise `RunnerError`
    - exit code 2 -> raise `RunnerError`
    - exit code 3 -> raise `RunnerError`
    - any unexpected exit code -> raise `RunnerError`
    - JSON parse failure (from `_parse_json_output`) -> `RunnerError` propagates
    - Pydantic validation failure (from `_build_findings`) -> `RunnerError` propagates

**Function 2:**
- signature: `def _parse_json_output(stdout: str, path: Path) -> dict`
  - purpose: Extract and parse the JSON object from noisy stdout (parent tool emits non-JSON lines even with --quiet)
  - logic:
    1. Find first `{` with `idx = stdout.find("{")`
    2. If `idx == -1`: raise `RunnerError(f"No JSON found in Arcane Auditor stdout for path '{path}'. stdout snippet: {stdout[:300]!r}")`
    3. Create `decoder = json.JSONDecoder()`
    4. Try: `data, _ = decoder.raw_decode(stdout, idx)`
    5. Catch `json.JSONDecodeError as exc`: raise `RunnerError(f"Failed to parse Arcane Auditor JSON output for path '{path}': {exc}") from exc`
    6. If `not isinstance(data, dict)`: raise `RunnerError(f"Arcane Auditor JSON output is not an object for path '{path}'")`
    7. Return `data`
  - calls: `json.JSONDecoder().raw_decode(stdout, idx)`
  - returns: `dict` -- the parsed JSON object (expected keys: "summary", "findings")
  - error handling:
    - No `{` in stdout -> raise `RunnerError`
    - `json.JSONDecodeError` -> raise `RunnerError`
    - Parsed value is not a dict -> raise `RunnerError`

**Function 3:**
- signature: `def _build_findings(data: dict, path: Path) -> list[Finding]`
  - purpose: Validate and construct Finding models from the parsed JSON data
  - logic:
    1. Extract `raw_findings = data.get("findings", [])`
    2. If `not isinstance(raw_findings, list)`: raise `RunnerError(f"'findings' key in Arcane Auditor output is not a list for path '{path}'")`
    3. Initialize `findings: list[Finding] = []`
    4. Try: for each `item` in `raw_findings`, call `findings.append(Finding.model_validate(item))`
    5. Catch `ValidationError as exc`: raise `RunnerError(f"Failed to validate Finding from Arcane Auditor output for path '{path}': {exc}") from exc`
    6. Return `findings`
  - calls: `Finding.model_validate(item)` for each item in raw_findings
  - returns: `list[Finding]`
  - error handling:
    - `"findings"` value not a list -> raise `RunnerError`
    - `pydantic.ValidationError` on any item -> raise `RunnerError`

#### Wiring / Integration
- `run_audit` is the public API; `_parse_json_output` and `_build_findings` are private helpers called only by `run_audit`
- Imports `ScanManifest`, `AgentConfig`, `ScanResult`, `Finding`, `ExitCode`, `RunnerError` from `src.models`
- No circular imports: `src.models` has no imports from `src.runner`
- `run_audit` will be imported by `src.cli` (Phase 5) as `from src.runner import run_audit`

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.runner import run_audit; print('import OK')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/runner.py && echo 'syntax OK'`
- test: no existing tests for runner yet (P3.3 creates tests/test_runner.py)
- smoke: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "
from src.runner import run_audit, _parse_json_output
from pathlib import Path
# Test _parse_json_output extracts JSON from noisy stdout
noisy = 'Scanning directory: /foo\nFound 3 files\n{\n  \"summary\": {},\n  \"findings\": []\n}\nTotal time: 1.2s'
data = _parse_json_output(noisy, Path('/foo'))
assert data == {'summary': {}, 'findings': []}, f'Got {data}'
print('_parse_json_output OK')
"`

## Constraints
- Do NOT modify src/models.py, src/scanner.py, src/config.py, pyproject.toml, or any test files
- Do NOT add any new pip dependencies -- stdlib json, subprocess, and logging are sufficient
- Do NOT use print() -- use logging.getLogger(__name__) only
- Do NOT use string paths -- use pathlib.Path everywhere
- The subprocess cwd MUST be set to config.auditor_path.resolve() so that `uv run main.py` resolves correctly relative to the parent project
- The timeout MUST be exactly 300 seconds (not 299, not 301)
- subprocess.run() MUST use check=False -- parse exit codes manually; never use check=True
- The function names _parse_json_output and _build_findings are private (underscore prefix); run_audit is the only public export
- Do NOT pre-validate scan_manifest.total_count -- let exit code 2 handle empty manifests
- The `repo` field in ScanResult: use scan_manifest.repo if it is not None, otherwise use str(scan_manifest.root_path)
