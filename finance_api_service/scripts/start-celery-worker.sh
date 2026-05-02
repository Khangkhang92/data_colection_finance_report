#!/usr/bin/env sh
set -eu

python_bin="python3"
if ! command -v "${python_bin}" >/dev/null 2>&1; then
  python_bin="python"
fi

cpu_count="$("${python_bin}" - <<'PY'
import os

print(os.cpu_count() or 1)
PY
)"

mode="${CELERY_WORKER_CONCURRENCY_MODE:-io}"

if [ -n "${CELERY_WORKER_CONCURRENCY:-}" ]; then
  concurrency="${CELERY_WORKER_CONCURRENCY}"
elif [ "${mode}" = "cpu" ]; then
  concurrency="${cpu_count}"
else
  concurrency=$((cpu_count * 2))
fi

if [ "${concurrency}" -lt 1 ]; then
  concurrency=1
fi

echo "Starting Celery worker mode=${mode} cpu_count=${cpu_count} concurrency=${concurrency}"
exec celery -A finance_api.celery_app:celery_app worker --loglevel="${CELERY_WORKER_LOG_LEVEL:-INFO}" --concurrency="${concurrency}"
