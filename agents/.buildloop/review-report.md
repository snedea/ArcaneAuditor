# Review Report — P2.2

## Verdict: FAIL

## Runtime Checks
- Build: PASS (`uv run python -m py_compile src/scanner.py src/models.py` — no errors)
- Tests: PASS (19/19 passed, `uv run pytest tests/test_scanner.py -v`)
- Lint: PASS (`uv run ruff check` — all checks passed)
- Docker: SKIPPED (no compose files changed in this task)

## Findings

```json
{
  "high": [
    {
      "file": "src/scanner.py",
      "line": 100,
      "issue": "Shell injection via unescaped token in GIT_ASKPASS script. The token is embedded directly in a shell script using single-quote delimiters: `f.write(f\"echo '{token}'\\n\")`. A token containing a single quote breaks out of the quoted context and injects arbitrary shell commands. Example: token='x\\'; cat /etc/passwd; echo \\'' produces `echo 'x'; cat /etc/passwd; echo ''` in the script. This allows arbitrary code execution if the token value is attacker-controlled (e.g., via a malicious config file). Fix: use shlex.quote(token) or set the token in the script via an exported shell variable with a heredoc so the value is never interpreted as shell syntax.",
      "category": "security"
    }
  ],
  "medium": [],
  "low": [
    {
      "file": "src/scanner.py",
      "line": 99,
      "issue": "GIT_ASKPASS script returns the token unconditionally regardless of what git is prompting for (username vs. password). Git calls the askpass binary twice — once with a 'Username for ...' prompt and once with a 'Password for ...' prompt. The script always echoes the token. For GitHub this happens to work because GitHub ignores the username field when a valid PAT is supplied as the password, but this behavior is GitHub-specific. For GitLab, Bitbucket, or self-hosted Gitea instances, authentication may fail silently. No test covers a non-GitHub host.",
      "category": "api-contract"
    },
    {
      "file": "src/scanner.py",
      "line": 104,
      "issue": "The temporary clone directory (tmp_path) is not cleaned up when git clone fails (returncode != 0) or when scan_local raises ScanError. The docstring documents this as intentional. However, the agent is explicitly intended to run in a Context Foundry loop (CLAUDE.md) that may scan many failing repos in rapid succession. On that code path, /tmp will accumulate arcane_auditor_* directories indefinitely — each being a full shallow clone that could be hundreds of MB. The OS does not reclaim /tmp between loop iterations on Linux systems that mount /tmp as tmpfs with a fixed size. This is a documented design choice but the practical impact in a loop context is more serious than the plan acknowledges.",
      "category": "resource-leak"
    },
    {
      "file": "src/scanner.py",
      "line": 87,
      "issue": "Plan-vs-implementation inconsistency: the plan's final import block for scanner.py included `import shutil`, but the implementation correctly omits it (shutil is unused inside scanner.py). Separately, the plan specified building the clone URL as `https://{token}@github.com/{repo}.git` (plan lines 114-117), but the implementation diverged to use GIT_ASKPASS (a security improvement). The test class name changed from test_token_injected_into_clone_url to test_token_passed_via_askpass_not_in_url. These deviations are improvements, but the plan was not updated to reflect them, creating a gap if a future agent re-reads the plan.",
      "category": "inconsistency"
    }
  ],
  "validated": [
    "All 19 tests pass, including 10 new TestScanGithub tests and 9 pre-existing TestScanLocal tests.",
    "Ruff finds zero lint issues across scanner.py, models.py, and test_scanner.py.",
    "ScanManifest gains repo/branch/temp_dir fields with None defaults — backward-compatible with all existing scan_local callers and tests.",
    "scan_github correctly raises ScanError with message 'Invalid repo format' for noslash, /repo, and owner/ inputs (no mocking needed — validated without network).",
    "Token does NOT appear in subprocess argv — the clone URL is always the unauthenticated form https://github.com/owner/repo.git; GIT_ASKPASS carries the credential.",
    "GIT_TERMINAL_PROMPT=0 is set, preventing interactive prompts if askpass fails.",
    "askpass temp file is always deleted in the finally block (missing_ok=True handles the case where creation failed) — no askpass file leaks.",
    "askpass file is created with mkstemp (0600) then chmod'd to 0700 (S_IRWXU) — owner-only read/write/execute, correct for an askpass script.",
    "result.stderr is stripped before inclusion in the ScanError message — clone_url (which never contains the token in this implementation) is not included in errors.",
    "ScanManifest is mutable (no frozen ConfigDict) — manifest.repo = repo / manifest.branch = branch / manifest.temp_dir = tmp_path attribute assignments are valid in Pydantic v2.",
    "subprocess.run is called with check=False and timeout=120 per the project convention in CLAUDE.md.",
    "from __future__ import annotations is present as line 1 in all three changed files.",
    "scan_local is not modified — only scan_github is appended after it."
  ]
}
```
