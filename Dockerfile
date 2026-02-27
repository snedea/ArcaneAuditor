# Stage 1: Install Claude CLI via npm
FROM node:20-slim AS node-builder
RUN npm install -g @anthropic-ai/claude-code

# Stage 2: Final image
FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy Node.js binary + Claude CLI from builder
COPY --from=node:20-slim /usr/local/bin/node /usr/local/bin/
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/@anthropic-ai/claude-code/cli.js /usr/local/bin/claude

# Create non-root user with UID 1001 (matches host chuck user)
RUN adduser --disabled-password --gecos '' --uid 1001 appuser

# Copy dependency files first for caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=appuser:appuser . .

# Create .claude dir and set ownership
RUN mkdir -p /home/appuser/.claude && chown -R appuser:appuser /home/appuser

USER appuser
ENV HOME=/home/appuser

EXPOSE 8080

CMD ["uv", "run", "python", "web/server.py", "--host", "0.0.0.0", "--port", "8080"]
