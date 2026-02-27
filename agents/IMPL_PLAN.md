# Implementation Plan: Arcane Auditor Agent System

**Goal**: Build an autonomous agent that runs Arcane Auditor's 42 deterministic rules against Workday Extend repos, reports findings, and (Phase 2) fixes them -- proving that deterministic rules work reliably in an LLM agent loop.

## Phase 1: Foundation -- Project Scaffold and Data Models

- [x] P1.1: Create pyproject.toml with dependencies (typer, pydantic>=2.0, pygithub, pytest) and project metadata. Create src/__init__.py and tests/__init__.py. Verify with `uv sync`
- [x] P1.2: Create src/models.py with Pydantic models -- ScanResult (repo, timestamp, findings_count, findings, exit_code), Finding (rule_id, description, severity, message, line, file_path), FixResult (finding, original_content, fixed_content, confidence), AgentConfig (repos list, config_preset, output_format, github_token optional), ReportFormat enum (JSON, SARIF, GITHUB_ISSUES, PR_COMMENT). Include custom exceptions: ScanError, RunnerError, ReporterError, FixerError
- [x] P1.3: Create src/config.py -- load AgentConfig from a YAML or JSON file, with defaults. Support environment variable overrides for GITHUB_TOKEN and ARCANE_AUDITOR_PATH. Validate that the parent Arcane Auditor path exists and main.py is present

## Phase 2: Scanner -- Find Extend Artifacts

- [x] P2.1: Create src/scanner.py with a scan_local(path: Path) function that walks a directory tree and returns list of paths to .pmd, .pod, .script, .amd, .smd files. Must handle nested directories. Return a ScanManifest model (root_path, files found by type, total count)
- [x] P2.2: Add scan_github(repo: str, branch: str, token: str) to scanner.py -- clone a GitHub repo to a temp directory using subprocess git clone (not pygithub), then delegate to scan_local. Clean up temp dir on completion. Return ScanManifest with repo metadata
- [x] P2.3: Create test fixtures -- tests/fixtures/clean_app/ with a minimal valid .pmd file (valid pageId, script with const/let, proper naming), a valid .pod file, a valid .script file. Create tests/fixtures/dirty_app/ with files containing known violations: one .pmd with var usage, console.log, magic numbers, and a widget missing id; one .pod with hardcoded workday URL; one .script with unused function
- [x] P2.4: Write tests/test_scanner.py -- test scan_local finds all artifact types in both fixtures, test it returns correct counts, test it ignores non-Extend files (e.g., .js, .py), test it handles empty directories gracefully

## Phase 3: Runner -- Execute Arcane Auditor

- [x] P3.1: Create src/runner.py with run_audit(scan_manifest: ScanManifest, config: AgentConfig) -> ScanResult function. Invoke parent `uv run main.py review-app <path> --format json --quiet` as subprocess. Parse JSON stdout into Finding models. Handle all 4 exit codes (0, 1, 2, 3). Set timeout of 300 seconds
- [x] P3.2: Add support for passing config presets to the runner -- if config.config_preset is set, pass `--config <preset>` to the CLI. Support both built-in presets (development, production-ready) and custom config file paths
- [x] P3.3: Write tests/test_runner.py -- test with clean_app fixture (expect exit 0, zero findings), test with dirty_app fixture (expect exit 1, specific findings matching known violations), test timeout handling, test invalid path handling (expect exit 2)

## Phase 4: Reporter -- Format and Deliver Results

- [x] P4.1: Create src/reporter.py with a base report_findings(scan_result: ScanResult, format: ReportFormat) dispatcher function. Implement format_json(scan_result) that returns the ScanResult as a pretty-printed JSON string. Implement format_summary(scan_result) that returns a human-readable text summary with counts by severity, rule, and file
- [x] P4.2: Implement format_sarif(scan_result) in reporter.py -- produce a valid SARIF v2.1.0 JSON document. Map Arcane Auditor rule IDs to SARIF rule descriptors. Map severity ACTION->error, ADVICE->warning. Include file paths and line numbers as SARIF locations. The SARIF output must pass validation against the SARIF schema
- [x] P4.3: Implement format_github_issues(scan_result, repo: str, token: str) in reporter.py -- create one GitHub issue per ACTION finding, group ADVICE findings into a single summary issue. Use PyGithub. Label issues with "arcane-auditor" and severity labels. Check for duplicate issues before creating (by title match). Return list of created issue URLs
- [x] P4.4: Implement format_pr_comment(scan_result, repo: str, pr_number: int, token: str) in reporter.py -- post a single PR comment with a summary table (rule, severity, file, line, message). If no findings, post a "clean" comment. Use PyGithub. Include a collapsible details section for ADVICE findings
- [x] P4.5: Write tests/test_reporter.py -- test JSON output is valid JSON matching ScanResult schema, test SARIF output structure (has runs, results, rules sections), test summary format contains expected counts. Mock PyGithub for issue and PR comment tests

## Phase 5: CLI -- Orchestration Entry Point

- [x] P5.1: Create src/cli.py with Typer app. Implement `scan` command that accepts: path (positional, optional), --repo (GitHub repo), --pr (PR number), --format (json|sarif|summary|github-issues|pr-comment), --output (file path), --config (Arcane Auditor config preset), --quiet flag. Wire scan -> runner -> reporter pipeline
- [x] P5.2: Implement `scan` command orchestration -- if path given, use scan_local; if --repo given, use scan_github; if --pr given, validate --repo is also given. After scanning, run audit, then format. Write to --output file or stdout. Return appropriate exit codes (mirror parent tool: 0, 1, 2, 3)
- [x] P5.3: Write tests/test_cli.py -- test scan with local fixture path, test scan with --format json produces valid output, test scan with --format summary produces text output, test missing --repo when --pr given returns exit 2, test --help produces usage text

## Phase 6: Fix Templates -- Deterministic Fixes (The Loop Closer)

- [x] P6.1: Create fix_templates/__init__.py and fix_templates/base.py with a FixTemplate abstract base class: match(finding: Finding) -> bool, apply(finding: Finding, source_content: str) -> FixResult | None, confidence: Literal["HIGH", "MEDIUM", "LOW"]. Create a FixTemplateRegistry that auto-discovers templates (same pattern as RulesEngine in parent)
- [x] P6.2: Create fix_templates/script_fixes.py with HIGH-confidence fix templates: VarToLetConst (ScriptVarUsageRule -> replace var with let/const using regex, const if no reassignment found), RemoveConsoleLog (ScriptConsoleLogRule -> remove console.log/warn/error lines), TemplateLiteralFix (ScriptStringConcatRule -> convert string concatenation to template literals for simple cases only)
- [x] P6.3: Create fix_templates/structure_fixes.py with HIGH-confidence fix templates: LowerCamelCaseWidgetId (WidgetIdLowerCamelCaseRule -> convert widget id to lowerCamelCase), LowerCamelCaseEndpointName (EndpointNameLowerCamelCaseRule -> convert endpoint name to lowerCamelCase), AddFailOnStatusCodes (EndpointFailOnStatusCodesRule -> add failOnStatusCodes field with sensible defaults)
- [x] P6.4: Create src/fixer.py with fix_findings(scan_result: ScanResult, source_dir: Path) -> list[FixResult] function. For each finding, iterate fix templates, apply first matching HIGH-confidence template. Return list of FixResults. Do not modify files in place -- return new content strings. A separate apply_fixes(fix_results, target_dir) function writes the fixed files
- [ ] P6.5: Write tests/test_fixer.py -- for each fix template: create a minimal file with the violation, apply the fix, re-scan with Arcane Auditor, verify the violation is gone. Test that LOW confidence fixes are not auto-applied. Test that fixes do not introduce new violations (re-scan after fix must not increase finding count)

## Phase 7: Full Loop Integration

- [ ] P7.1: Add `fix` command to cli.py -- accepts same args as scan, plus --create-pr flag and --target-dir for local output. Pipeline: scan -> audit -> fix -> (optional) re-audit to verify -> (optional) create PR with fixes
- [ ] P7.2: Add `watch` command to cli.py -- poll a GitHub repo for new PRs at --interval seconds (default 300). For each new PR: scan changed files, run audit, post PR comment. Track seen PRs in a local JSON state file to avoid duplicate comments. Support graceful shutdown via SIGINT
- [ ] P7.3: Create a GitHub Actions workflow template at agents/docs/github-action-template.yml -- reusable workflow that installs uv, installs Arcane Auditor, runs the agent scan on PR changed files, uploads SARIF to GitHub Code Scanning, and optionally posts a PR comment
- [ ] P7.4: Write integration test -- test_integration.py that runs the full pipeline: scan dirty_app fixture -> audit -> fix -> re-audit -> verify finding count decreased. This proves the deterministic loop works end-to-end

## Phase 8: Documentation and Polish

- [ ] P8.1: Write agents/README.md -- overview, installation, usage examples for all three modes (scan, fix, watch), configuration reference, how fix templates work, how to add custom fix templates
- [ ] P8.2: Add inline help to all CLI commands with examples. Ensure --help on every command shows clear usage
- [ ] P8.3: Add a docs/DETERMINISTIC_LOOP.md document explaining the philosophy -- why this approach avoids the Workday LLM problems, how deterministic rules + LLM transport = reliable results, comparison with pure-LLM code review approaches, and how the pattern learning in context-foundry makes the loop self-improving without sacrificing determinism
