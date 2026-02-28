# Docker & Deployment

## Build & Run

```bash
docker compose build --no-cache
docker compose up -d
docker logs arcane-auditor --tail 20
```

## Architecture

- Base image: `python:3.12-slim`
- Package manager: UV (copied from `ghcr.io/astral-sh/uv:latest`)
- Non-root user: `appuser` (UID 1001)
- Port: 8080 internal, 8082 external
- Deployed at: `arcane.llam.ai`

## Key Details

- `.venv` created by `uv sync` during build — must `chown` to appuser after
- `.dockerignore` excludes `.venv`, `.git`, `.env`, `__pycache__` to prevent host artifacts overwriting container builds
- `prompts/` mounted read-only (`./prompts:/app/prompts:ro`) for hot-reload without rebuild
- `ANTHROPIC_API_KEY` passed via environment from `.env`
- No Tailscale sidecar — this service runs standalone

## Common Issues

- **Crash loop after rebuild**: check `.venv` permissions (`chown` in Dockerfile)
- **Blank page**: check `docker logs` for Python import errors
- **AI features broken**: verify `ANTHROPIC_API_KEY` in `.env`
