# Docker Compose Dev Stack

Stack dev hien tai chay:

- PostgreSQL + TimescaleDB: `timescale/timescaledb:latest-pg17`
- Redis: `redis:8-alpine`
- FastAPI API: `fireant-api`
- Celery worker: `fireant-celery-worker`
- Celery beat: `fireant-celery-beat`
- Flower monitor: `fireant-flower`

## Chay lan dau

```bash
cd finance_api_service
cp .env.example .env
docker-compose up -d postgres redis api celery-worker celery-beat flower
```

## Service URLs mac dinh

```text
API:         http://localhost:8000/
Docs:        http://localhost:8000/docs
Flower:      http://localhost:5555/
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

Trong network cua Compose, service backend ket noi DB/Redis bang ten service:

```text
postgres
redis
```

Vi vay `DATABASE_URL` va `CELERY_BROKER_URL` trong `.env` mau da duoc dat theo
ten container noi bo, khong dung `localhost`.

## Celery va Redis

Compose da nap cac bien sau vao `api`, `celery-worker`, `celery-beat`:

```text
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
CELERY_WORKER_CONCURRENCY=
CELERY_WORKER_CONCURRENCY_MODE=io
FLOWER_PORT=5555
```

`celery-worker` tu tinh concurrency khi `CELERY_WORKER_CONCURRENCY` de rong:

- `CELERY_WORKER_CONCURRENCY_MODE=cpu`: concurrency bang so core CPU.
- `CELERY_WORKER_CONCURRENCY_MODE=io`: concurrency bang `CPU * 2`.
- Neu set `CELERY_WORKER_CONCURRENCY=4` thi gia tri nay se override auto sizing.

Voi job FireAnt, `io` hop ly hon vi phan lon thoi gian la doi HTTP/DB. Neu bi
rate-limit hoac connection reset nhieu, giam ve `cpu` hoac set so cu the thap hon.

`api` tu chay `finance-schema upgrade head` truoc khi boot FastAPI.

`flower` la monitor nhe cho Celery. No doc broker/backend de hien worker, queue,
task history va task state. Neu can auth co the set `FLOWER_BASIC_AUTH=user:pass`.

## Reset local data

Lenh nay xoa toan bo database va redis local:

```bash
docker-compose down -v
```
