from __future__ import annotations

import sys
from celery.bin.celery import main as celery_main


def main() -> None:
    sys.argv = [
        "celery",
        "-A",
        "services.finance_rag_service.worker.processes.celery_app:celery_app",
        "worker",
        "--loglevel=INFO",
        "--concurrency=1",
    ]
    celery_main()


if __name__ == "__main__":
    main()
