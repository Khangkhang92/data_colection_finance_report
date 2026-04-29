#!/usr/bin/env bash
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
  -v n8n_user="${N8N_DB_USER:-n8n}" \
  -v n8n_password="${N8N_DB_PASSWORD:-n8n}" \
  -v n8n_database="${N8N_DB_NAME:-n8n}" \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" <<'SQL'
CREATE EXTENSION IF NOT EXISTS vector;

SELECT format('CREATE ROLE %I LOGIN PASSWORD %L', :'n8n_user', :'n8n_password')
WHERE NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = :'n8n_user')\gexec

SELECT format('CREATE DATABASE %I OWNER %I', :'n8n_database', :'n8n_user')
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'n8n_database')\gexec
SQL
