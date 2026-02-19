# ---- Build stage: install dependencies ----
FROM python:3.13-slim AS builder

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (layer caching — only re-installs when these change)
COPY pyproject.toml uv.lock ./

# Install production dependencies only (no dev tools like pytest, ruff)
RUN uv sync --no-dev --frozen

# ---- Runtime stage: lean final image ----
FROM python:3.13-slim

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Don't buffer Python output (so logs appear immediately)
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Copy startup script
COPY start.sh .
RUN chmod +x start.sh

# Run migrations, then start uvicorn
CMD ["./start.sh"]
