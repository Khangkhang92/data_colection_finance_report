# Project Structure

```text
finance_api_service/
├── .env.example
├── .gitignore
├── README.md
├── environment.yml
├── pyproject.toml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DOCKER.md
│   ├── MIGRATION_PLAN.md
│   └── STRUCTURE.md
├── docker/
├── docker-compose.yml
├── Dockerfile
├── scripts/
├── tests/
└── src/
    └── finance_api/
        ├── __init__.py
        ├── app.py
        ├── main.py
        ├── api/
        │   ├── __init__.py
        │   ├── deps.py
        │   ├── router.py
        │   └── v1.py
        ├── clients/
        │   ├── __init__.py
        │   └── fireant.py
        ├── celery_app.py
        ├── config/
        │   ├── __init__.py
        │   └── settings.py
        ├── db/
        │   ├── __init__.py
        │   └── session.py
        ├── repositories/
        │   ├── __init__.py
        │   ├── base.py
        │   ├── company.py
        │   ├── finance_report.py
        │   ├── market.py
        │   └── posts.py
        ├── schemas/
        │   ├── __init__.py
        │   ├── jobs.py
        │   └── requests.py
        ├── jobs.py
        ├── services/
        │   ├── __init__.py
        │   ├── company.py
        │   ├── finance_report.py
        │   ├── market.py
        │   └── posts.py
        └── utils/
            ├── __init__.py
            └── dates.py
            └── prices.py
```

## Mapping tu script cu

`posts.py` -> `services/posts.py` + `repositories/posts.py` + `POST /fireant_data/webhooks/posts/sync`

`get_full_finance.py` -> `services/finance_report.py` + `repositories/finance_report.py` + `POST /fireant_data/webhooks/finance-statements/sync`

`company_detail.py` -> `services/company.py` + `repositories/company.py` + `POST /fireant_data/webhooks/company-details/sync`

`market_mention.py`, `session_quote.py`, `history_price.py` -> `services/market.py` + `repositories/market.py`

`getdata/base.py` -> `clients/fireant.py`

`common/db/*` -> `db/session.py`, dung `finance_schema.config.get_database_url`.

## Job Nen

Tat ca sync webhook deu enqueue job nen qua `jobs.py` va tra `job_id`.
Trang thai job duoc doc qua `GET /fireant_data/jobs/{job_id}`.

`finance-statements`, `session-quotes`, `history-prices` deu commit theo batch de
tranh mat toan bo tien do khi job dai bi dung giua chung.

## Job Dinh Ky

`celery_app.py` dinh nghia Celery app, Redis broker/backend, va lich mac dinh cho:

- `symbols`
- `company-details`
- `market-mentions`
- `session-quotes`
- `history-prices`
- `finance-statements`

FastAPI van giu webhook trigger thu cong. Celery phu trach worker va scheduler.
