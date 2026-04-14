# TaskFlow

A task management REST API where users can register, log in, create projects, add tasks, and assign them to team members.

## Tech Stack

- **Language/Framework:** Python 3.14, Django 6.0, Django REST Framework
- **Database:** PostgreSQL 17
- **Auth:** JWT (RS256) via SimpleJWT, passwords hashed with bcrypt
- **Infrastructure:** Docker, Docker Compose, Gunicorn
- **Tooling:** uv (package manager), Ruff (linter/formatter), pytest

---

## Architecture Decisions

**RS256 over HS256 for JWT** — Asymmetric signing separates token creation (private key) from verification (public key). This is more secure for multi-service setups and allows the entrypoint to auto-generate a fresh keypair on startup if none is provided.

**Single-character enum storage** — Task status (`T`, `I`, `D`) and priority (`L`, `M`, `H`) are stored as single characters instead of full strings. Saves storage and index space while the API still returns human-readable display values.

**`uuid7` primary keys** — UUID v7 is time-ordered, so it works well with B-tree indexes and avoids the fragmentation issues of UUID v4. Python 3.14 ships `uuid7` in the standard library.

**`MetaSerializer` base class** — Provides `object_only_fields` support: fields like nested `tasks` appear in detail responses but are automatically excluded from list responses. This avoids N+1 queries on list endpoints without needing separate serializers.

**Custom exception handler** — All error responses follow a consistent format (`{"error": "...", "fields": {...}}`) as required by the spec, rather than DRF's default inconsistent shapes.

**Permission classes over queryset filtering** — `IsProjectOwner` and `IsTaskOwner` enforce write access at the object level, cleanly separating "can I see this?" (queryset) from "can I modify this?" (permission). This ensures non-owners get `403 Forbidden`, not a misleading `404`.

**What I intentionally left out:**
- No refresh token flow — the spec requires only a 24h access token.
- No rate limiting — out of scope for this assignment, but would add `django-ratelimit` in production.
- No email verification — the spec doesn't require it.

---

## Running Locally

```bash
git clone https://github.com/your-name/taskflow
cd taskflow
cp .env.example .env
docker compose up
# API available at http://localhost:8000
```

That's it. The container automatically:
1. Generates `DJANGO_SECRET_KEY` and JWT RS256 keys if left blank in `.env`
2. Waits for PostgreSQL to be ready
3. Runs migrations
4. Seeds the database with test data
5. Starts Gunicorn on port 8000

---

## Running Migrations

Migrations run automatically on container startup via `entrypoint.sh`. No manual steps needed.

To run manually (local development):
```bash
uv run python backend/manage.py migrate
```

---

## Test Credentials

The seed script creates a test user on first boot:

```
Email:    test@example.com
Password: password123
```

Also seeded: 1 project ("Website Redesign") with 3 tasks in different statuses (To Do, In Progress, Done).

---

## API Reference

A **Bruno collection** is included in the repo at [`greening_bruno/`](./greening_bruno). Open it in [Bruno](https://www.usebruno.com/) to try all endpoints interactively.

All endpoints return `Content-Type: application/json`. Non-auth endpoints require `Authorization: Bearer <token>`.

### Pagination

List endpoints support pagination via query params:
- `?page=1` — page number (default: 1)
- `?size=10` — page size (default: 10, max: 50)

---

## Running Tests

```bash
uv run pytest backend/core/tests.py -v
```

Tests cover: registration, login, project CRUD, task CRUD with filters, permission boundaries (403 vs 404), stats endpoint, and error response formats.

---

## Possible Enhancements

- **Rate limiting** — Add per-endpoint throttling to prevent abuse on auth endpoints.
- **Structured logging** — Replace print-based `QueryMonitor` with proper structured logging (e.g., `structlog`) for production observability.
- **Soft deletes** — Add `deleted_at` timestamps instead of hard deletes, with a manager to filter them out by default.
- **Task activity log** — Track status changes with timestamps and who made the change.
- **CI pipeline** — GitHub Actions workflow for lint, test, and Docker build on push.
- **More granular permissions** — Project members/roles instead of just "owner" vs "everyone else".
