# Docker Compose Dev Stack

Stack dev hien tai chay:

- PostgreSQL + pgvector: `pgvector/pgvector:0.8.2-pg18-trixie`
- PostgREST: `postgrest/postgrest:latest`
- n8n: `n8nio/n8n:latest`

Finance API khong duoc start trong compose dev nay.

## Chay lan dau

May hien tai dang co `docker-compose` v1, nen lenh mac dinh la:

```bash
cd finance_api_service
cp .env.docker.example .env
docker-compose --env-file .env up -d
```

Neu may khac co Docker Compose v2 thi co the dung:

```bash
docker compose --env-file .env up -d
```

## URL mac dinh

```text
n8n:         http://localhost:5678/
PostgreSQL:  localhost:5432
PostgREST:   http://localhost:3001/
```

## Database mac dinh

PostgreSQL tao 2 database:

```text
finance  - database cho du lieu finance
n8n      - database rieng cho n8n
```

Database `finance` da enable extension:

```sql
CREATE EXTENSION vector;
```

Default credentials local dev:

```text
finance DB: finance / finance
n8n DB:     n8n / n8n
```

## Vector DB

Stack nay dung PostgreSQL + `pgvector` lam vector database. PostgREST expose PostgreSQL qua REST, nen n8n co the goi PostgREST de doc/ghi bang vector hoac goi function search vector.

Vi du SQL tao bang embedding:

```sql
CREATE TABLE documents (
    id bigserial PRIMARY KEY,
    content text NOT NULL,
    embedding vector(1536)
);

CREATE INDEX documents_embedding_hnsw
ON documents
USING hnsw (embedding vector_cosine_ops);
```

## Ket noi noi bo trong n8n

PostgREST:

```text
http://postgrest:3000
```

## Reset local data

Lenh nay xoa toan bo database va data n8n local:

```bash
docker-compose --env-file .env down -v
```
