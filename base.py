from common.db import ScopedSession
from sqlalchemy import select
from functools import lru_cache
from models import Symbol


class Base:
    @lru_cache(maxsize=1)
    def get_all_symbols(self):
        with ScopedSession() as session:
            return session.execute(select(Symbol.ticker)).scalars().all()       

