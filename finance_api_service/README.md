# fireant-data

Du an `FastAPI + Celery + Redis` de dong bo du lieu FireAnt theo job nen va lich dinh ky.

## Muc tieu

- Moi script cu tro thanh mot service co endpoint kich hoat rieng.
- API client quan ly tap trung auth, base headers, timeout, retry va error handling.
- Data duoc clean/transform truoc khi upsert vao PostgreSQL.
- Response luon la JSON de API client goi va xu ly workflow.
- Models/migrations dung chung tu package `finance-schema`.
- Khi `finance-schema` duoc publish rieng, service nay chi can nang version dependency roi chay migration.
- `Celery` chay worker va scheduler (`beat`) cho cac job dong bo dai.
- `Redis` dong vai tro broker/result backend cho `Celery`.

## Chay nhanh bang Miniconda

```bash
cd finance_api_service
conda env create -f environment.yml
conda activate finance-api-service
cp .env.example .env
docker-compose up -d postgres redis
finance-schema upgrade head
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

## Tech stack

- API: FastAPI
- Job queue va scheduler: Celery
- Broker/result backend: Redis
- Database: PostgreSQL + TimescaleDB
- Shared schema/migrations: `finance-schema`

## Endpoint webhook / manual trigger

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

Webhook API chi enqueue task vao Celery. Moi xu ly dong bo ton thoi gian deu
chay trong `celery-worker`, khong chay long task trong process API.

## Job dinh ky bang Celery

Compose dev stack da co san:

- `api`
- `celery-worker`
- `celery-beat`
- `redis`
- `postgres`
Lich mac dinh hien tai:

- `symbols`: 06:00, ngay 02 cua cac thang `01, 04, 07, 10`
- `company-details`: 06:30, ngay 03 cua cac thang `01, 04, 07, 10`
- `market-mentions`: 08:00
- `session-quotes`: 16:15
- `history-prices`: 17:00
- `finance-statements`: 19:00, ngay 15 cua cac thang `01, 04, 07, 10`

Mui gio: `Asia/Ho_Chi_Minh`

`finance-statements` duoc chot theo quy, o thang `T+1` sau khi quy ket thuc, de
giam rui ro keo du lieu qua som khi FireAnt chua cap nhat du.

`symbols` va `company-details` cung duoc chot theo quy de dong bo cung nhip voi
chu ky cap nhat doanh nghiep.

`GET /fireant_data/jobs/{job_id}` doc trang thai tu Celery backend. Ca webhook
API va Celery Beat deu day task vao worker theo cung mot co che.

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
- [docs/DOCKER.md](docs/DOCKER.md)
- [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md)
