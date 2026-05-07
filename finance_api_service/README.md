# fireant-data

Du an `FastAPI + Celery + Redis` de dong bo du lieu FireAnt theo job nen va lich dinh ky.
`Flower` duoc them vao Compose de monitor worker va task.

## Muc tieu

- Moi script cu tro thanh mot service co endpoint kich hoat rieng.
- API client quan ly tap trung auth, base headers, timeout, retry va error handling.
- Data duoc clean/transform truoc khi upsert vao PostgreSQL.
- Response luon la JSON de API client goi va xu ly workflow.
- Models/migrations dung chung tu package `finance-schema`.
- Khi `finance-schema` duoc publish rieng, service nay chi can nang version dependency roi chay migration.
- `Celery` chay worker va scheduler (`beat`) cho cac job dong bo dai.
- `Redis` dong vai tro broker/result backend cho `Celery`.
- `Flower` monitor worker, queue va task state.

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

Data local cua PostgreSQL va Redis duoc bind mount vao `./volumes/postgres` va
`./volumes/redis` ngay tai root cua service de de kiem soat, backup hoac reset.

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
POST /fireant_data/webhooks/industries/sync
POST /fireant_data/webhooks/finance-statements/sync
POST /fireant_data/webhooks/company-details/sync
POST /fireant_data/webhooks/market-mentions/sync
POST /fireant_data/webhooks/fundamentals/sync
POST /fireant_data/webhooks/extended-instruments/sync
POST /fireant_data/webhooks/session-quotes/sync
POST /fireant_data/webhooks/history-prices/sync
```

Tat ca endpoint sync deu tra `202 Accepted` sau khi task duoc dua vao Celery.

Webhook API chi enqueue task vao Celery. Moi xu ly dong bo ton thoi gian deu
chay trong `celery-worker`, khong chay long task trong process API.

## Job dinh ky bang Celery

Compose dev stack da co san:

- `api`
- `celery-worker`
- `celery-beat`
- `flower`
- `redis`
- `postgres`
Lich mac dinh hien tai:

- `symbols`: 06:00, ngay 02 cua cac thang `01, 04, 07, 10`
- `industries`: 06:15, ngay 02 cua cac thang `01, 04, 07, 10`
- `company-details`: 06:30, ngay 03 cua cac thang `01, 04, 07, 10`
- `fundamentals`: 07:30
- `extended-instruments`: 07:45
- `market-mentions`: 08:00
- `session-quotes`: 16:15
- `history-prices`: 17:00
- `finance-statements`: 19:00, ngay 15 cua cac thang `01, 04, 07, 10`

Mui gio: `Asia/Ho_Chi_Minh`

`finance-statements` duoc chot theo quy, o thang `T+1` sau khi quy ket thuc, de
giam rui ro keo du lieu qua som khi FireAnt chua cap nhat du.

`symbols` va `company-details` cung duoc chot theo quy de dong bo cung nhip voi
chu ky cap nhat doanh nghiep.

Ca webhook API va Celery Beat deu day task vao worker theo cung mot co che.
Worker tu tinh concurrency theo CPU neu `CELERY_WORKER_CONCURRENCY` de rong:
`CELERY_WORKER_CONCURRENCY_MODE=cpu` dung so core CPU, con `io` dung `CPU * 2`
cho cac job cho HTTP/DB nhieu.

Flower mac dinh mo tai `http://localhost:5555`.

## Dong bo tu dong

- `finance-statements/sync`: khong can body, tu dong chay theo ky bao cao hien tai;
  lan dau backfill toi da `120` ky quy va `30` bao cao nam (`quarter=0`) cho moi
  cong ty/report type, cac lan sau chi lay batch con thieu, commit theo
  `symbol + report_type`, va resume khi goi lai.
- `market-mentions/sync`: khong can body, mac dinh lay du `today`, `weekly`,
  `monthly`.
- `industries/sync`: mac dinh `include_symbols=true`, cap nhat bang `industry`
  va mapping `symbol.industry_code`, `symbol.icb_code`.
- `fundamentals/sync`: khong can body, lay `/symbols/{symbol}/fundamental` cho
  toan bo ticker trong DB, ghi snapshot theo ngay vao bang `market` cac cot
  `shares`, `shares_out_standing`, `market_cap`, `market_capitalization`,
  `free_shares`. Day la du lieu can cho LCDT de tinh ty trong von hoa/free-float.
- `extended-instruments/sync`: lay futures/warrant/fund detail va MXV contracts.
  Job nay cap nhat `symbol.instrument_type`, `symbol.instrument_code`,
  `symbol.is_listing`, `derivative_contract`, `covered_warrant_info`,
  `commodity_contract`.
- `session-quotes/sync`: khong can body, lay toan bo ticker trong DB, commit theo
  tung `symbol`.
- `history-prices/sync`: khong can body, mac dinh lay 1 nam tro lai day; neu DB
  da co du lieu cho mot ma thi tiep tuc tu `latest_date` cua ma do den hien tai.
  Endpoint nay nhan body tuy chon `{ "limit": 100 }`.

## Tai lieu

- [docs/STRUCTURE.md](docs/STRUCTURE.md)
- [docs/RUNNING.md](docs/RUNNING.md)
- [docs/ALEMBIC.md](docs/ALEMBIC.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DOCKER.md](docs/DOCKER.md)
- [docs/MIGRATION_PLAN.md](docs/MIGRATION_PLAN.md)
