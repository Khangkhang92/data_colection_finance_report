# finance-api-service

Du an moi tach rieng de refactor cac script call API cu thanh he thong API-first cho n8n.

## Muc tieu

- Moi script cu tro thanh mot service co endpoint kich hoat rieng.
- API client quan ly tap trung auth, base headers, timeout, retry va error handling.
- Data duoc clean/transform truoc khi upsert vao PostgreSQL.
- Response luon la JSON de n8n de goi va xu ly workflow.
- Models/migrations dung chung tu package `finance-schema`.

## Chay nhanh bang Miniconda

```bash
cd finance_api_service
conda env create -f environment.yml
conda activate finance-api-service
cp .env.example .env
docker-compose up -d postgres
python -m alembic upgrade head
python -m uvicorn --app-dir src finance_api.app:create_app --factory --reload
```

Mo docs:

```text
http://localhost:8000/docs
```

## Endpoint n8n webhook

```bash
POST /api/v1/webhooks/posts/sync
POST /api/v1/webhooks/symbols/sync
POST /api/v1/webhooks/finance-statements/sync
POST /api/v1/webhooks/company-details/sync
POST /api/v1/webhooks/market-mentions/sync
POST /api/v1/webhooks/session-quotes/sync
POST /api/v1/webhooks/history-prices/sync
```

## Tai lieu

- [docs/STRUCTURE.md](docs/STRUCTURE.md)
- [docs/RUNNING.md](docs/RUNNING.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/N8N.md](docs/N8N.md)
- [docs/DOCKER.md](docs/DOCKER.md)
- [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md)
