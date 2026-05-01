# fireant-data

Du an API-first de dong bo du lieu FireAnt theo job nen, phuc vu n8n va cac workflow ingestion.

## Muc tieu

- Moi script cu tro thanh mot service co endpoint kich hoat rieng.
- API client quan ly tap trung auth, base headers, timeout, retry va error handling.
- Data duoc clean/transform truoc khi upsert vao PostgreSQL.
- Response luon la JSON de n8n de goi va xu ly workflow.
- Models/migrations dung chung tu package `finance-schema`.
- Khi `finance-schema` duoc publish rieng, service nay chi can nang version dependency roi chay migration.

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

Workflow tren dung cho local mono-repo. Neu deploy theo kieu package release, co
the dung `requirements.release.txt` de cai `finance-schema` truc tiep tu GitHub
repo `Khangkhang92/schema_lib`. Khi da co tag release on dinh, chi can doi
`@main` thanh `@vX.Y.Z`.

Mo docs:

```text
http://localhost:8000/docs
```

## Endpoint n8n webhook

```bash
POST /fireant_data/webhooks/posts/sync
POST /fireant_data/webhooks/symbols/sync
POST /fireant_data/webhooks/finance-statements/sync
POST /fireant_data/webhooks/company-details/sync
POST /fireant_data/webhooks/market-mentions/sync
POST /fireant_data/webhooks/session-quotes/sync
POST /fireant_data/webhooks/history-prices/sync
GET  /fireant_data/jobs/{job_id}
```

Tat ca endpoint sync deu tra `202 Accepted` va `job_id`. Theo doi tien do qua
`GET /fireant_data/jobs/{job_id}`.

## Dong bo tu dong

- `finance-statements/sync`: khong can body, tu dong chay theo ky bao cao hien tai,
  chi lay batch con thieu, commit theo `symbol + report_type`, va resume khi goi lai.
- `market-mentions/sync`: khong can body, mac dinh lay du `today`, `weekly`,
  `monthly`.
- `session-quotes/sync`: khong can body, lay toan bo ticker trong DB, commit theo
  tung `symbol`.
- `history-prices/sync`: khong can body, mac dinh lay 1 nam tro lai day; neu DB
  da co du lieu cho mot ma thi tiep tuc tu `latest_date` cua ma do den hien tai.

## Tai lieu

- [docs/STRUCTURE.md](docs/STRUCTURE.md)
- [docs/RUNNING.md](docs/RUNNING.md)
- [docs/ALEMBIC.md](docs/ALEMBIC.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/N8N.md](docs/N8N.md)
- [docs/DOCKER.md](docs/DOCKER.md)
- [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md)
