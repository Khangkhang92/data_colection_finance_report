# Project Structure

`fireant-data` la service dong bo du lieu FireAnt. API chi nhan trigger va
enqueue task vao Celery; worker moi la noi chay cac job ton thoi gian.

```text
finance_api_service/
├── AGENT.md
├── .env.example
├── .gitignore
├── Dockerfile
├── README.md
├── docker-compose.yml
├── environment.yml
├── pyproject.toml
├── requirements.txt
├── requirements.release.txt
├── docs/
│   ├── ALEMBIC.md
│   ├── ARCHITECTURE.md
│   ├── DOCKER.md
│   ├── MIGRATION_PLAN.md
│   ├── RUNNING.md
│   └── STRUCTURE.md
└── src/
    └── finance_api/
        ├── __init__.py
        ├── app.py
        ├── celery_app.py
        ├── jobs.py
        ├── main.py
        ├── api/
        │   ├── __init__.py
        │   ├── deps.py
        │   ├── router.py
        │   └── v1.py
        ├── clients/
        │   ├── __init__.py
        │   └── fireant.py
        ├── config/
        │   ├── __init__.py
        │   └── settings.py
        ├── db/
        │   ├── __init__.py
        │   └── session.py
        ├── observability/
        │   ├── __init__.py
        │   └── logging.py
        ├── repositories/
        │   ├── __init__.py
        │   ├── base.py
        │   ├── company.py
        │   ├── finance_report.py
        │   ├── market.py
        │   ├── posts.py
        │   └── symbols.py
        ├── schemas/
        │   ├── __init__.py
        │   ├── jobs.py
        │   └── requests.py
        ├── services/
        │   ├── __init__.py
        │   ├── company.py
        │   ├── finance_report.py
        │   ├── market.py
        │   ├── posts.py
        │   └── symbols.py
        └── utils/
            ├── __init__.py
            ├── dates.py
            └── prices.py
```

## Main Modules

`app.py`: FastAPI app factory, logging middleware, startup bootstrap hook.

`api/v1.py`: HTTP controller layer. Sync endpoints return `202 Accepted` and
enqueue Celery tasks. They must not run long sync work directly.

`jobs.py`: Celery dispatch helpers and shared runner functions used by Celery
tasks.

`celery_app.py`: Celery app, task definitions, Redis backend/broker config,
and Beat schedule.

`clients/fireant.py`: FireAnt HTTP client with auth, retry, timeout, and
error handling.

`services/*`: Business orchestration for each sync domain.

`repositories/*`: Database read/write/upsert logic. SQLAlchemy models come
from `finance-schema`.

`schemas/*`: Request/response DTOs for API and Celery payloads.

`utils/*`: Shared helpers for dates and adjusted price calculations.

## Runtime Flow

Manual trigger:

```text
FastAPI endpoint
  -> jobs.enqueue_job(...)
  -> Redis broker
  -> celery-worker
  -> service
  -> repository
  -> PostgreSQL
```

Scheduled trigger:

```text
celery-beat
  -> Redis broker
  -> celery-worker
  -> service
  -> repository
  -> PostgreSQL
```

## Data And Migration Ownership

Database schema is owned by `finance-schema`, installed from
`Khangkhang92/schema_lib`.

The API container runs:

```bash
finance-schema upgrade head
```

before starting FastAPI.

## Sync Jobs

`posts.py` -> `services/posts.py` + `repositories/posts.py` + `POST /fireant_data/webhooks/posts/sync`

`get_full_finance.py` -> `services/finance_report.py` + `repositories/finance_report.py` + `POST /fireant_data/webhooks/finance-statements/sync`

`company_detail.py` -> `services/company.py` + `repositories/company.py` + `POST /fireant_data/webhooks/company-details/sync`

`market_mention.py`, `session_quote.py`, `history_price.py` -> `services/market.py` + `repositories/market.py`

`getdata/base.py` -> `clients/fireant.py`

`common/db/*` -> `db/session.py`, using `finance_schema.config.get_database_url`.

## Operational Notes

`finance-statements`, `session-quotes`, and `history-prices` commit by batch so
long sync jobs do not lose all progress if interrupted.

`finance-statements` defaults to a long backfill window of `120` periods so the
first run loads the available history for every company/report type. Subsequent
runs use DB coverage checks and only fetch missing batches.

`history-prices` stores raw prices plus `adj_ratio`. Adjusted prices are
derived data and should be computed from raw data when needed.

`symbols` are loaded from DB in alphabetical order for downstream sync jobs.

`finance-statements` skips ETF/index-like symbols that do not have financial
reports.
