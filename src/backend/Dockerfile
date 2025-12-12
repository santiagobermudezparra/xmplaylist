FROM python:3.13-alpine AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy workspace root files first
COPY pyproject.toml uv.lock ./

# Copy backend package
COPY src/backend ./src/backend

# Install the workspace and backend
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --package backend

FROM python:3.13-alpine

RUN addgroup -S -g 1000 app && adduser -S -u 1000 -G app app

COPY --from=builder --chown=app:app /app /app

WORKDIR /app

USER app
EXPOSE 22112

CMD ["/app/.venv/bin/python", "-m", "backend.main"]
