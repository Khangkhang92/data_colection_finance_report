# Running the Service

Huong dan nay dung cho local development voi `FastAPI + Celery + Redis +
PostgreSQL` trong `docker-compose.yml`, Alembic migrations tu package
`finance-schema`, va backend trong `finance_api_service`.

## 1. Chuan bi moi truong

Tu thu muc `finance_api_service`:

```bash
conda env create -f environment.yml
conda activate finance-api-service
cp .env.example .env
```

`environment.yml` cai package service editable va `finance-schema` tu GitHub:

```text
finance-schema @ git+https://github.com/Khangkhang92/schema_lib.git@main
-e .
```

Vi vay sau khi tao env, co the dung command `finance-api serve`. Neu chua cai
editable package trong env hien tai, dung cach dev o muc 4.

Neu dung package release tach rieng tren GitHub, co the cai dependencies bang
`requirements.release.txt` thay vi editable path local. File nay dang tro toi
`https://github.com/Khangkhang92/schema_lib.git@main`; khi co tag release, nen
doi sang `@vX.Y.Z`.

## 2. Chay ha tang local

```bash
docker-compose up -d postgres redis
docker-compose ps
```

Mac dinh `.env.example` dung cho Docker Compose:

```text
DATABASE_URL=postgresql+psycopg2://finance:finance@postgres:5432/finance
```

Gia tri nay khop voi default `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB` trong `docker-compose.yml`.

Redis mac dinh:

```text
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

Neu chay trong Docker Compose, khong dung `localhost`. Service noi bo se dung:

```text
DATABASE_URL=postgresql+psycopg2://finance:finance@postgres:5432/finance
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

## 3. Chay Alembic migration

Service da cau hinh `alembic.ini` de tro vao migrations cua package
`finance-schema`:

```ini
script_location = finance_schema:migrations
```

Chay migration bang CLI cua `finance-schema`:

```bash
finance-schema upgrade head
```

Kiem tra revision hien tai:

```bash
finance-schema current -v
```

Ket qua dung hien tai:

```text
3e9b5d4b1a2c (head)
```

## 4. Chay backend

Neu da tao env tu `environment.yml` hoac da chay `pip install -e .`:

```bash
finance-api serve
```

Hoac chay truc tiep bang Uvicorn. Cach nay khong can install package service,
vi `--app-dir src` dua thu muc source vao Python import path:

```bash
python -m uvicorn --app-dir src finance_api.app:create_app --factory --reload
```

Neu package service chua duoc install editable trong env hien tai, chay theo
kieu dev bang `PYTHONPATH`:

```bash
PYTHONPATH=src python -m finance_api.main serve
```

Backend se listen tai:

```text
http://localhost:8000
```

## 5. Chay Celery worker va scheduler

Neu chay local khong qua Docker:

```bash
PYTHONPATH=src celery -A finance_api.celery_app:celery_app worker --loglevel=INFO --concurrency=1
PYTHONPATH=src celery -A finance_api.celery_app:celery_app beat --loglevel=INFO
```

Neu chay qua Docker Compose:

```bash
docker-compose up -d api celery-worker celery-beat
```

`api` se tu chay `finance-schema upgrade head` truoc khi boot, sau do `worker` va
`beat` moi noi theo.

Webhook API khong tu xu ly long task. Moi endpoint sync chi enqueue task vao
Celery, worker moi la noi thuc thi business job.

## 6. Kiem tra backend

Health check:

```bash
curl http://localhost:8000/fireant_data/health
```

Ket qua mong doi:

```json
{"status":"ok","service":"fireant-data"}
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

## 7. Sync symbols tu FireAnt

Endpoint webhook:

```bash
curl -X POST http://localhost:8000/fireant_data/webhooks/symbols/sync
```

Response tra `202 Accepted` sau khi task duoc dua vao Celery:

```json
{
  "job_name": "symbols_sync",
  "accepted": true,
  "message": "Symbols sync job accepted"
}
```

Mac dinh endpoint lay `ALL_SYMBOL_URL2` va chi upsert instruments co `type=stock`
vao bang `symbol`, cot khoa chinh `ticker`.

Neu muon sync tat ca instruments tu FireAnt:

```bash
curl -X POST http://localhost:8000/fireant_data/webhooks/symbols/sync \
  -H 'Content-Type: application/json' \
  -d '{"instrument_types": null}'
```

## 8. Sync finance statements

Endpoint nay khong can body. Service se:

- lay ticker tu DB theo thu tu alphabet
- tu dong suy ra ky bao cao gan nhat theo thoi diem hien tai
- lan dau backfill toi da `120` ky ve truoc cho moi cong ty/report type
- chi fetch cac batch `symbol + report_type` con thieu du lieu
- commit theo batch va resume tu dong khi goi lai

Goi job:

```bash
curl -X POST http://localhost:8000/fireant_data/webhooks/finance-statements/sync
```

## 9. Sync market mentions

Endpoint nay khong can body. Service se tu dong lay du 3 period:

- `today`
- `weekly`
- `monthly`

Goi job:

```bash
curl -X POST http://localhost:8000/fireant_data/webhooks/market-mentions/sync
```

## 10. Sync session quotes

Endpoint nay khong can body. Service se:

- lay ticker tu DB theo thu tu alphabet
- dong bo tung `symbol`
- commit theo batch tung `symbol`

Goi job:

```bash
curl -X POST http://localhost:8000/fireant_data/webhooks/session-quotes/sync
```

## 11. Sync history prices

Endpoint nay khong can body. Service se:

- lay ticker tu DB theo thu tu alphabet
- mac dinh lay du lieu 1 nam tro lai day
- neu mot `symbol` da co trong DB thi lay tiep tu `latest_date` cua ma do den hom nay
- commit theo batch tung `symbol`

Goi job:

```bash
curl -X POST http://localhost:8000/fireant_data/webhooks/history-prices/sync
```

## 12. Lich Celery mac dinh

- `symbols`: 06:00, ngay 02 cua cac thang `01, 04, 07, 10`
- `company-details`: 06:30, ngay 03 cua cac thang `01, 04, 07, 10`
- `market-mentions`: 08:00
- `session-quotes`: 16:15
- `history-prices`: 17:00
- `finance-statements`: 19:00, ngay 15 cua cac thang `01, 04, 07, 10`

Mui gio cua scheduler: `Asia/Ho_Chi_Minh`

`finance-statements` duoc lap lich theo quy, o thang `T+1` sau khi quy dong lai.

`symbols` va `company-details` hien cung chay theo quy thay vi hang ngay.

Ca webhook API va Celery Beat deu day task vao worker theo cung mot co che.
