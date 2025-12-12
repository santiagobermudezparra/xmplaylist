FROM python:3.13-alpine AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy workspace root files
COPY pyproject.toml uv.lock ./

# Copy frontend package
COPY src/frontend ./src/frontend

# Install
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --package frontend

FROM python:3.13-alpine

RUN addgroup -S -g 1000 app && adduser -S -u 1000 -G app app

COPY --from=builder --chown=app:app /app /app

WORKDIR /app

USER app
EXPOSE 22111

CMD ["/app/.venv/bin/python", "-m", "frontend.main"]
