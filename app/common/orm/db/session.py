from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from common.orm.db.core import Session, get_engine
from loguru import logger
from sqlalchemy.orm import Session as OrmSession


@contextmanager
def session_scope() -> Generator[OrmSession, None, None]:
    engine = get_engine()
    Session.configure(bind=engine)
    session = Session()
    try:
        logger.debug("DB session opened")
        yield session
        session.commit()
        logger.debug("DB session committed")
    except Exception:
        session.rollback()
        logger.exception("DB session rolled back")
        raise
    finally:
        session.close()
        Session.configure(bind=None)
        logger.debug("DB session closed")


def get_session() -> Generator[OrmSession, None, None]:
    with session_scope() as session:
        yield session
