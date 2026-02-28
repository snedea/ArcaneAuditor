# Testing Conventions

## Framework

pytest with `uv run pytest`.

## Test Organization

- `tests/test_<rule_name>.py` — one file per rule
- `tests/test_autofix.py` — autofix endpoint tests
- `tests/test_explain_endpoint.py` — explain endpoint tests
- `tests/test_revalidate.py` — revalidation tests
- `tests/test_snippets.py` — snippet extraction tests
- `tests/test_export_zip.py` — ZIP export tests
- `agents/tests/` — agent system tests (separate)

## Test Fixtures

- `agents/tests/fixtures/dirty_app/` — files with known violations
- `agents/tests/fixtures/clean_app/` — minimal clean files
- `web/frontend/dirty-app-sample.zip` — ZIP for manual/Playwright testing
- `web/frontend/clean-app-sample.zip` — clean ZIP for manual testing

## Mocking AI Endpoints

AI endpoint tests mock `_get_anthropic_client` (not subprocess):

```python
@patch('web.server._get_anthropic_client')
def test_autofix_success(mock_get_client):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='fixed content')]
    )
    mock_get_client.return_value = mock_client
    # ... test endpoint
```

## Running Tests

```bash
uv run pytest tests/ -v                    # All tests
uv run pytest tests/test_autofix.py -v     # Specific file
uv run pytest tests/ -x --tb=short         # Stop on first failure
uv run pytest tests/ -k "magic_number"     # Filter by name
```

## Writing New Tests

- Test both positive cases (rule fires) and negative cases (no false positive)
- Use inline JSON/script strings, not external fixture files for rule tests
- Verify finding attributes: `rule_id`, `message`, `line`, `severity`
- For endpoint tests: use FastAPI `TestClient`
