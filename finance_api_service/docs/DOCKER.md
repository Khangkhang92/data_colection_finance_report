# Docker Compose Dev Stack

Stack dev hien tai chay:

- PostgreSQL + TimescaleDB: `timescale/timescaledb:latest-pg17`
- PostgREST: `postgrest/postgrest:latest`
- Redis: `redis:8-alpine`
- FastAPI API: `fireant-api`
- Celery worker: `fireant-celery-worker`
- Celery beat: `fireant-celery-beat`

## Chay lan dau

```bash
cd finance_api_service
cp .env.example .env
docker-compose up -d postgres postgrest redis api celery-worker celery-beat
```

## Service URLs mac dinh

```text
API:         http://localhost:8000/
Docs:        http://localhost:8000/docs
PostgREST:   http://localhost:3000/
Redis:       localhost:6379
PostgreSQL:  localhost:5432
```

## Database mac dinh

PostgreSQL tao database:

```text
finance  - database cho du lieu finance
```

Default credentials local dev:

```text
finance DB: finance / finance
```

PostgREST mac dinh dung:

```text
schema:    public
anon role: finance
```

## Celery va Redis

Compose da nap cac bien sau vao `api`, `celery-worker`, `celery-beat`:

```text
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

`celery-worker` chay voi `--concurrency=1` de uu tien tinh on dinh cho cac job
dong bo FireAnt dai va co retry.

## Reset local data

Lenh nay xoa toan bo database va redis local:

```bash
docker-compose down -v
```
