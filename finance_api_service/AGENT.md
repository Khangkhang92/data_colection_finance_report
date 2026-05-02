# Agent Guide

Read this file before changing the project.

## What This Service Is

`fireant-data` is a FastAPI service for syncing FireAnt data into PostgreSQL.
The database schema and migrations are owned by the external `finance-schema`
package from `Khangkhang92/schema_lib`.

The service uses:

- FastAPI for HTTP trigger endpoints
- Celery for job execution and scheduling
- Redis as Celery broker/result backend
- PostgreSQL with TimescaleDB image
- `finance-schema` CLI for migrations

## First Files To Read

1. `README.md`
2. `docs/STRUCTURE.md`
3. `docs/RUNNING.md`
4. `docs/DOCKER.md`
5. `docs/ARCHITECTURE.md`
6. `src/finance_api/celery_app.py`
7. `src/finance_api/jobs.py`
8. `src/finance_api/api/v1.py`

## Non-Negotiable Runtime Rules

API endpoints must not run long sync jobs directly. They enqueue Celery tasks
and return `202 Accepted`.

Celery worker is responsible for all heavy sync work.

Celery Beat is responsible for scheduled sync jobs.

Database migrations must use:

```bash
finance-schema upgrade head
```

Do not call local Alembic migrations directly unless the schema package changes
and this is explicitly required.

## Environment Rules

Do not commit `.env`.

For Docker Compose, internal services use service names:

```text
DATABASE_URL=postgresql+psycopg2://finance:finance@postgres:5432/finance
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

For host-local development, `localhost` may be used only when running the API
outside containers.

The Docker build installs `finance-schema` from GitHub via SSH forwarding.
The server needs a working SSH agent for private repo access.

## Data Rules

Keep raw source data as the source of truth.

For history prices, keep `price_*` as raw values and `adj_ratio` as the
adjustment factor. Derived adjusted values should be computed from raw values.

Sync jobs should be resumable and batch-committed where possible.

Finance statement sync defaults to a `120` period backfill window so the first
run loads historical statements for all eligible companies. Do not reduce that
default unless the sync strategy changes.

Symbol processing should preserve alphabetical order from DB.

## Code Organization

Controller/API layer: `src/finance_api/api/v1.py`

Celery task layer: `src/finance_api/celery_app.py`

Job dispatch/status layer: `src/finance_api/jobs.py`

Business logic: `src/finance_api/services/`

Database access: `src/finance_api/repositories/`

DTOs: `src/finance_api/schemas/`

Shared utilities: `src/finance_api/utils/`

Core configuration/logging: `src/finance_api/config/`, `src/finance_api/observability/`

## Before Finishing Changes

Run at least:

```bash
python3 -m compileall finance_api_service/src
```

If Docker or dependency wiring changed, also review:

```bash
docker compose config
```

When committing, stage only relevant project files and avoid unrelated deleted
files outside `finance_api_service`.
