# Plan: P3.2

## Dependencies
- list: []
- commands: []
  (No new packages required. All imports already present in runner.py.)

## File Operations (in execution order)

### 1. MODIFY src/runner.py
- operation: MODIFY
- reason: Add `--config <preset>` to the subprocess command when `config.config_preset` is set

#### Imports / Dependencies
No new imports needed. All required imports (`logging`, `subprocess`, `pathlib.Path`, models) are already present.

#### Functions

- signature: `_build_cmd(scan_manifest: ScanManifest, config: AgentConfig) -> list[str]`
  - purpose: Construct the subprocess command list for invoking Arcane Auditor, including optional `--config` flag
  - logic:
    1. Initialize `cmd` as `["uv", "run", "main.py", "review-app", str(scan_manifest.root_path), "--format", "json", "--quiet"]`
    2. Evaluate `preset = config.config_preset.strip() if config.config_preset is not None else ""`
    3. If `preset` is truthy (non-empty after strip), append `"--config"` to `cmd`, then append `preset` to `cmd`
    4. Return `cmd`
  - calls: nothing
  - returns: `list[str]` — the complete command list ready for `subprocess.run`
  - error handling: none — pure list construction, no I/O

- signature: `run_audit(scan_manifest: ScanManifest, config: AgentConfig) -> ScanResult` (existing, MODIFY body only)
  - purpose: unchanged — invoke Arcane Auditor subprocess and parse results
  - logic: Replace the inline `cmd` construction block with a call to `_build_cmd(scan_manifest, config)`. All other logic remains identical.
    1. Set `auditor_path = config.auditor_path.resolve()`
    2. Call `cmd = _build_cmd(scan_manifest, config)` (replaces the previous inline `cmd: list[str] = [...]` block)
    3. Call `logger.debug("run_audit: path=%s auditor=%s preset=%s", scan_manifest.root_path, auditor_path, config.config_preset)`  (replace existing debug log line to include preset)
    4. All remaining logic (subprocess.run, exit code handling, _parse_json_output, _build_findings, ScanResult construction) is unchanged
  - calls: `_build_cmd(scan_manifest, config)`, then all existing helpers unchanged
  - returns: `ScanResult`
  - error handling: unchanged from existing implementation

#### Wiring / Integration
`_build_cmd` is a module-private helper (underscore prefix). It is called only from `run_audit`. No other files need changes.

#### Exact diff description

**Remove** this block (lines 31-34 of the current file):
```
    cmd: list[str] = [
        "uv", "run", "main.py", "review-app",
        str(scan_manifest.root_path), "--format", "json", "--quiet",
    ]
    logger.debug("run_audit: path=%s auditor=%s", scan_manifest.root_path, auditor_path)
```

**Replace with**:
```
    cmd = _build_cmd(scan_manifest, config)
    logger.debug(
        "run_audit: path=%s auditor=%s preset=%s",
        scan_manifest.root_path, auditor_path, config.config_preset,
    )
```

**Add** the following new private function immediately before the existing `_parse_json_output` function (i.e., after the closing of `run_audit` and before `def _parse_json_output`):

```python
def _build_cmd(scan_manifest: ScanManifest, config: AgentConfig) -> list[str]:
    """Build the subprocess command list for invoking Arcane Auditor.

    Includes --config <preset> when config.config_preset is set to a non-empty string.
    Preset values may be:
    - A built-in preset name: 'development' or 'production-ready'
    - An absolute path to a custom JSON config file

    Note: The parent tool resolves relative paths against its own cwd (auditor_path).
    Use absolute paths for custom config files to avoid ambiguity.

    Args:
        scan_manifest: The scan manifest describing what to audit.
        config: Agent configuration, including optional config_preset.

    Returns:
        A list of strings suitable for passing to subprocess.run.
    """
    cmd: list[str] = [
        "uv", "run", "main.py", "review-app",
        str(scan_manifest.root_path), "--format", "json", "--quiet",
    ]
    preset = config.config_preset.strip() if config.config_preset is not None else ""
    if preset:
        cmd.extend(["--config", preset])
    return cmd
```

## Verification
- build: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.runner import run_audit, _build_cmd; print('import ok')"`
- lint: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -m py_compile src/runner.py && echo 'syntax ok'`
- test: `cd /Users/name/homelab/ArcaneAuditor/agents && uv run pytest tests/ -v` (no runner-specific tests exist yet per IMPL_PLAN P3.3, but existing scanner tests must still pass)
- smoke:
  1. Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.models import AgentConfig, ScanManifest; from src.runner import _build_cmd; from pathlib import Path; m = ScanManifest(root_path=Path('/tmp')); c = AgentConfig(); print(_build_cmd(m, c))"` and verify output is `['uv', 'run', 'main.py', 'review-app', '/tmp', '--format', 'json', '--quiet']`
  2. Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.models import AgentConfig, ScanManifest; from src.runner import _build_cmd; from pathlib import Path; m = ScanManifest(root_path=Path('/tmp')); c = AgentConfig(config_preset='development'); print(_build_cmd(m, c))"` and verify output is `['uv', 'run', 'main.py', 'review-app', '/tmp', '--format', 'json', '--quiet', '--config', 'development']`
  3. Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.models import AgentConfig, ScanManifest; from src.runner import _build_cmd; from pathlib import Path; m = ScanManifest(root_path=Path('/tmp')); c = AgentConfig(config_preset='  '); print(_build_cmd(m, c))"` and verify output does NOT include `--config` (whitespace-only preset is ignored)
  4. Run `cd /Users/name/homelab/ArcaneAuditor/agents && uv run python -c "from src.models import AgentConfig, ScanManifest; from src.runner import _build_cmd; from pathlib import Path; m = ScanManifest(root_path=Path('/tmp')); c = AgentConfig(config_preset='/abs/path/to/config.json'); print(_build_cmd(m, c))"` and verify output ends with `['--config', '/abs/path/to/config.json']`

## Constraints
- Do NOT modify src/models.py — `AgentConfig.config_preset: str | None = None` already exists and requires no changes
- Do NOT modify src/config.py
- Do NOT modify any test files
- Do NOT add any new dependencies to pyproject.toml
- The `_build_cmd` function must use `.strip()` on `config.config_preset` before checking truthiness — a whitespace-only string must not produce a `--config` argument (follows known pattern #2 from reference data)
- The `_build_cmd` function must be placed between the closing of `run_audit` and the existing `def _parse_json_output` function
- Do NOT change the subprocess.run call signature, timeout, cwd, or error handling in `run_audit`
- The parent tool's `--config` flag is documented as accepting both preset names and file paths; no validation of the preset value is performed in the agent — the parent tool will exit 2 if the value is invalid, and `run_audit` already handles exit code 2 as `RunnerError`
