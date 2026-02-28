FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create non-root user with UID 1001 (matches host chuck user)
RUN adduser --disabled-password --gecos '' --uid 1001 appuser

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=appuser:appuser . .

USER appuser
ENV HOME=/home/appuser

EXPOSE 8080

CMD ["uv", "run", "python", "web/server.py", "--host", "0.0.0.0", "--port", "8080"]
