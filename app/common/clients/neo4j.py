from __future__ import annotations

from typing import Any

from loguru import logger
from neo4j import Driver, GraphDatabase


class Neo4jClient:
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j") -> None:
        self._uri = uri
        self._database = database
        self._driver: Driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self) -> None:
        self._driver.close()

    def health_check(self) -> bool:
        try:
            with self._driver.session(database=self._database) as session:
                value = session.run("RETURN 1 AS ok").single()
                return bool(value and value.get("ok") == 1)
        except Exception:
            logger.exception("Neo4j health check failed uri={uri}", uri=self._uri)
            return False

    def execute_write(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            result = session.execute_write(lambda tx: tx.run(query, params or {}))
            return [dict(record) for record in result]

    def execute_read(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._driver.session(database=self._database) as session:
            result = session.execute_read(lambda tx: tx.run(query, params or {}))
            return [dict(record) for record in result]


def connect_neo4j(uri: str, username: str, password: str, database: str = "neo4j") -> Neo4jClient:
    return Neo4jClient(uri=uri, username=username, password=password, database=database)
