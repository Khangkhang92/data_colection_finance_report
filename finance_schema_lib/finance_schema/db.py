from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from finance_schema.config import get_database_url


def get_engine():
    return create_engine(
        get_database_url(),
        pool_pre_ping=True,
        poolclass=NullPool,
    )


Session = sessionmaker(autocommit=False, autoflush=False)


@contextmanager
def scoped_session():
    engine = get_engine()
    Session.configure(bind=engine)
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Session.configure(bind=None)
