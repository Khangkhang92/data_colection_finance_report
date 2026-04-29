# Running the Service

Huong dan nay dung cho local development voi PostgreSQL trong `docker-compose.yml`,
Alembic migrations tu package `finance_schema_lib`, va backend FastAPI trong
`finance_api_service`.

## 1. Chuan bi moi truong

Tu thu muc `finance_api_service`:

```bash
conda env create -f environment.yml
conda activate finance-api-service
cp .env.example .env
```

`environment.yml` cai editable ca hai package:

```text
-e ../finance_schema_lib
-e .
```

Vi vay sau khi tao env, co the dung command `finance-api serve`. Neu chua cai
editable package trong env hien tai, dung cach dev o muc 4.

## 2. Chay PostgreSQL

```bash
docker-compose up -d postgres
docker-compose ps
```

Mac dinh `.env.example` dung:

```text
DATABASE_URL=postgresql+psycopg2://finance:finance@localhost:5432/finance
```

Gia tri nay khop voi default `POSTGRES_USER`, `POSTGRES_PASSWORD`,
`POSTGRES_DB` trong `docker-compose.yml`.

## 3. Chay Alembic migration

Service da cau hinh `alembic.ini` de tro vao migrations cua
`finance_schema_lib`:

```ini
script_location = finance_schema:migrations
```

Chay migration:

```bash
python -m alembic upgrade head
```

Kiem tra revision hien tai:

```bash
python -m alembic current
```

Ket qua dung hien tai:

```text
d05663267564 (head)
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

## 5. Kiem tra backend

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

Ket qua mong doi:

```json
{"status":"ok","service":"finance-api-service"}
```

OpenAPI docs:

```text
http://localhost:8000/docs
```

## 6. Sync symbols tu FireAnt

Endpoint webhook:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/symbols/sync
```

Mac dinh endpoint lay `ALL_SYMBOL_URL2` va chi upsert instruments co
`type=stock` vao bang `symbol`, cot khoa chinh `ticker`.

Neu muon sync tat ca instruments tu FireAnt:

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/symbols/sync \
  -H 'Content-Type: application/json' \
  -d '{"instrument_types": null}'
```
