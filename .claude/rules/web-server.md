# Web Server (FastAPI)

## File: `web/server.py`

FastAPI application serving the web UI and REST API.

## Key Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serves index.html |
| `/api/upload` | POST | Upload ZIP or files, returns job ID |
| `/api/job/{id}` | GET | Poll job status and results |
| `/api/configs` | GET | List available analysis configurations |
| `/api/explain` | POST | AI explanation of findings (temp 1.0) |
| `/api/autofix` | POST | AI auto-fix single finding (temp 0) |
| `/api/revalidate` | POST | Re-run rules on modified file content |
| `/api/export-zip` | POST | Bundle fixed files into ZIP download |

## LLM Integration

- Uses Anthropic SDK directly (`anthropic.Anthropic().messages.create()`)
- Singleton client via `_get_anthropic_client()`
- Async wrapper: `_call_claude()` uses `asyncio.to_thread()` for non-blocking calls
- System prompts loaded from `prompts/` directory with mtime caching
- Model configurable via `LLM_MODEL` env var (default: `claude-sonnet-4-6`)

## Patterns

- Async job queue for long-running analyses
- Static files served from `web/frontend/` at `/static/`
- CORS enabled
- Pydantic models for request/response validation
- Code fence stripping on LLM responses (regex)
- Error mapping: `APITimeoutError` → 504, `AuthenticationError` → 503

## Adding New Endpoints

Follow the existing pattern:
1. Define Pydantic request/response models near the top
2. Add the endpoint after related endpoints
3. Use `async def` with `asyncio.to_thread()` for blocking operations
4. Return proper HTTP error codes with detail messages
