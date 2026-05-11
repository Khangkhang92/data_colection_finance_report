from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", "sqlite+pysqlite:///./finance.db")


def get_engine():
    return create_engine(get_database_url(), future=True)


Session = sessionmaker(autocommit=False, autoflush=False, future=True)
