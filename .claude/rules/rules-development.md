# Writing New Rules

## Structure

All rules live in `parser/rules/` organized by category:
- `script/core/` — variable, console, naming rules
- `script/complexity/` — cyclomatic, nesting, line count
- `script/logic/` — anti-patterns (string concat, magic numbers)
- `script/unused_code/` — dead code, unused vars/functions
- `structure/endpoints/` — endpoint validation
- `structure/widgets/` — widget ID/naming
- `structure/validation/` — security, hardcoded values
- `custom/user/` — user-defined rules (gitignored)

## Creating a Rule

1. Create a new file in the appropriate subdirectory
2. Inherit from `Rule` (from `parser.rules.base`)
3. Set class attributes: `ID`, `DESCRIPTION`, `SEVERITY`
4. Implement `analyze(self, context: ProjectContext) -> Generator[Finding, None, None]`
5. Yield `Finding` objects with `rule=self`, `message`, `line`, `file_path`

Rules are auto-discovered by `pkgutil.walk_packages()` — no registration needed.

## Severity Levels

- `ACTION` — must fix before production (blocking in CI with `--fail-on-advice=false`)
- `ADVICE` — should fix, not blocking by default

## Testing Rules

- Write tests in `tests/` matching `test_<rule_name>.py`
- Use inline JSON/script strings as test fixtures
- Verify both positive (finding raised) and negative (no false positive) cases
- Test edge cases: empty files, missing fields, malformed JSON

## Common Pitfalls

- Don't assume fields exist in PMD JSON — always check with `.get()` or optional chaining
- Script rules receive parsed AST via `ProjectContext` — use the AST cache, don't re-parse
- Line numbers must be accurate — use the line mapping from the parser
- Never yield findings for code that's correct — false positives erode trust
