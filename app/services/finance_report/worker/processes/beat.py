from __future__ import annotations

import sys
from celery.bin.celery import main as celery_main


def main() -> None:
    sys.argv = [
        "celery",
        "-A",
        "services.finance_report.worker.processes.celery_app:celery_app",
        "beat",
        "--loglevel=INFO",
    ]
    celery_main()


if __name__ == "__main__":
    main()
