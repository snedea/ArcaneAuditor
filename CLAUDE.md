# CLAUDE.md — Arcane Auditor

## What This Is

A code review tool for Workday Extend applications. 42 deterministic rules analyze .pmd, .pod, .amd, .smd, and .script files for quality, structure, and convention violations. A web UI provides drag-and-drop analysis with AI-powered explanations and auto-fix.

## Essential Commands

```bash
# Run CLI analysis
uv run main.py review-app <path-or-zip> --format console
uv run main.py review-app <path-or-zip> --format json --output report.json
uv run main.py review-app <path-or-zip> --format excel --output report.xlsx

# Run web server (local dev)
uv run python web/server.py --host 0.0.0.0 --port 8080

# Run tests
uv run pytest tests/ -v
uv run pytest tests/test_autofix.py tests/test_explain_endpoint.py -v  # AI endpoint tests
uv run pytest tests/ -x --tb=short  # Stop on first failure

# Docker
docker compose build --no-cache
docker compose up -d
docker logs arcane-auditor --tail 20

# Install deps
uv sync
```

## Architecture

```
main.py              → CLI entry point (Typer)
web/server.py        → FastAPI web server (port 8080, mapped to 8082 in Docker)
parser/              → Core analysis engine
  rules/             → 42 rules auto-discovered via pkgutil
  rules/base.py      → Abstract Rule class, Finding dataclass
  models.py          → PMDModel, PodModel, ScriptModel, ProjectContext
  pmd_script_parser.py → Lark-based script parser
config/              → Layered config: presets/ → teams/ → personal/
prompts/             → LLM system prompts (mounted read-only in Docker)
web/frontend/        → Vanilla JS (ES6 modules), no build step
output/              → Formatters: console, JSON, Excel
agents/              → Separate CLI agent system (has its own CLAUDE.md)
```

## Key Patterns

- **Rules are auto-discovered**: drop a `Rule` subclass into `parser/rules/` and it's picked up automatically
- **Rules yield Findings**: `analyze(context: ProjectContext) -> Generator[Finding, None, None]`
- **Config is hierarchical**: personal > teams > presets (highest priority wins)
- **Prompts are hot-reloadable**: mtime-cached, no restart needed to update
- **LLM calls use Anthropic SDK directly**: `_call_claude()` in server.py wraps `asyncio.to_thread()`
- **Autofix uses temperature 0**: deterministic output for code fixes
- **Explain uses temperature 0.3**: slight creativity for explanations
- **Frontend is vanilla JS**: ES6 modules in `web/frontend/js/`, no framework, no build step
- **AST caching**: ProjectContext caches parsed ASTs by content hash

## Exit Codes (CLI)

- 0 = clean (or ADVICE-only)
- 1 = ACTION issues found
- 2 = usage error
- 3 = runtime error

## Git & Deployment

- Remote: `origin` → `snedea/ArcaneAuditor.git`
- Branch: `main`
- Deployed at: `arcane.llam.ai` (via Docker on port 8082)
- Never commit `.env` or API keys
- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`

## Testing

- pytest with fixtures in `tests/` and `agents/tests/fixtures/`
- `dirty-app-sample.zip` and `clean-app-sample.zip` in `web/frontend/` for manual testing
- AI endpoint tests mock `_get_anthropic_client` (not subprocess)
- Rule tests use inline PMD/Pod/Script JSON structures

## Environment Variables

- `ANTHROPIC_API_KEY` — required for AI explain and autofix
- `LLM_MODEL` — model override (default: `claude-sonnet-4-6`)
- `PORT` — server port (default: 8080)
