# Architecture

```text
Celery Beat
  |
  | enqueue periodic tasks
  v
Redis broker <---- FastAPI routes
  |
  | dispatch tasks
  v
Celery worker
  |
  v
Service layer
  |
  | fetch raw API data
  v
Base API client
  |
  | clean + transform
  v
Repository layer
  |
  | upsert
  v
PostgreSQL
  ^
  | optional REST facade
  |
PostgREST
```

## Layers

API layer: FastAPI endpoints, request validation, manual trigger, JSON response.

Queue layer: Celery tasks and Celery Beat schedules.

Broker layer: Redis for Celery broker and result backend.

Client layer: HTTP auth, headers, timeout, retry, error handling.

Service layer: orchestration, pagination, batching, symbol loops.

Repository layer: database upsert and transaction handling.

Schema package: `finance-schema` owns SQLAlchemy models and Alembic migrations.

## Database strategy

The database schema is not duplicated in this project. `fireant-data` imports models from `finance_schema.models` and uses `finance-schema upgrade head` for migrations.

## Scheduling strategy

Celery Beat la scheduler mac dinh cho cac dong bo dinh ky. Redis giu queue va ket qua trung gian. Celery worker chay cac job dai de tranh block API process.

## API strategy

Moi sync job deu co HTTP endpoint rieng de trigger thu cong, quan sat, hoac noi
vao he thong orchestration ben ngoai khi can.
