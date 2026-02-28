"""Shared test fixtures."""
import pytest
from web.server import limiter


@pytest.fixture(autouse=True)
def _disable_rate_limiting():
    """Disable rate limiting during tests so rapid API calls don't 429."""
    limiter.enabled = False
    yield
    limiter.enabled = True
