# Multi-stage build
FROM python:3.14-alpine AS runtime

FROM runtime AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --no-install-project --no-dev

COPY backend/ ./backend/

# --- Runtime stage ---
FROM runtime

RUN apk add --no-cache libpq openssl

WORKDIR /app

RUN adduser -D appuser

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/backend /app/backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=greening.settings
    
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app/backend

USER appuser

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
