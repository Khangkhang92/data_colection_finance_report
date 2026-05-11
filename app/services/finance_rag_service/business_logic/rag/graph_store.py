from __future__ import annotations

from common.config.finance_rag import Settings


class GraphContextProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_context(self, question: str, limit: int = 5) -> list[str]:
        # Optional dependency runtime guard.
        try:
            from neo4j import GraphDatabase
        except Exception:
            return []

        query = """
        MATCH (n)
        WHERE any(k IN keys(n) WHERE toString(n[k]) CONTAINS $question)
        RETURN n
        LIMIT $limit
        """

        snippets: list[str] = []
        driver = GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
        )
        try:
            with driver.session() as session:
                rows = session.run(query, question=question, limit=limit)
                for row in rows:
                    node = row.get("n")
                    if node is not None:
                        snippets.append(str(dict(node)))
        finally:
            driver.close()
        return snippets

