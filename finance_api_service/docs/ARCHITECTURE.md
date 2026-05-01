# Architecture

```text
n8n
  |
  | HTTP JSON
  v
FastAPI routes
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
```

## Layers

API layer: FastAPI endpoints, request validation, JSON response.

Client layer: HTTP auth, headers, timeout, retry, error handling.

Service layer: orchestration, pagination, batching, symbol loops.

Repository layer: database upsert and transaction handling.

Schema package: `finance-schema` owns SQLAlchemy models and Alembic migrations.

## Database strategy

The database schema is not duplicated in this project. `fireant-data` imports models from `finance_schema.models` and uses `finance-schema upgrade head` for migrations.

## n8n strategy

Every sync job is exposed as an HTTP endpoint. n8n can trigger the endpoint through HTTP Request node and receive a JSON summary:

```json
{
  "service": "posts",
  "status": "ok",
  "fetched": 100,
  "saved": 100,
  "errors": []
}
```
