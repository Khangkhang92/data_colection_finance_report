from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from itertools import islice
from typing import Any

from common.clients.neo4j import Neo4jClient
from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class GraphSyncStats:
    symbols: int = 0
    posts: int = 0
    post_mentions: int = 0
    holders: int = 0
    subsidiaries: int = 0
    sector_industry: int = 0
    reports: int = 0
    market_mentions: int = 0
    co_mentions: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "symbols": self.symbols,
            "posts": self.posts,
            "post_mentions": self.post_mentions,
            "holders": self.holders,
            "subsidiaries": self.subsidiaries,
            "sector_industry": self.sector_industry,
            "reports": self.reports,
            "market_mentions": self.market_mentions,
            "co_mentions": self.co_mentions,
        }


class GraphSyncService:
    def __init__(self, session: Session, neo4j: Neo4jClient, batch_size: int = 500) -> None:
        self.session = session
        self.neo4j = neo4j
        self.batch_size = batch_size

    def ensure_constraints(self) -> None:
        statements = [
            "CREATE CONSTRAINT symbol_ticker_unique IF NOT EXISTS FOR (s:Symbol) REQUIRE s.ticker IS UNIQUE",
            "CREATE CONSTRAINT post_post_id_unique IF NOT EXISTS FOR (p:Post) REQUIRE p.post_id IS UNIQUE",
            "CREATE INDEX holder_name_index IF NOT EXISTS FOR (h:Holder) ON (h.name)",
            "CREATE INDEX company_symbol_index IF NOT EXISTS FOR (c:Company) ON (c.symbol)",
            "CREATE CONSTRAINT sector_name_unique IF NOT EXISTS FOR (s:Sector) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT industry_name_unique IF NOT EXISTS FOR (i:Industry) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT report_id_unique IF NOT EXISTS FOR (r:Report) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT report_data_id_unique IF NOT EXISTS FOR (rd:ReportData) REQUIRE rd.id IS UNIQUE",
            "CREATE CONSTRAINT date_date_unique IF NOT EXISTS FOR (d:Date) REQUIRE d.date IS UNIQUE",
            "CREATE CONSTRAINT post_group_id_unique IF NOT EXISTS FOR (g:PostGroup) REQUIRE g.id IS UNIQUE",
            "CREATE CONSTRAINT post_source_id_unique IF NOT EXISTS FOR (s:PostSource) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT company_name_symbol_unique IF NOT EXISTS FOR (c:Company) REQUIRE (c.name, c.symbol) IS UNIQUE",
        ]
        for stmt in statements:
            self.neo4j.execute_write(stmt)
        logger.info("Neo4j constraints/indexes ensured")

    def sync_symbols(self) -> int:
        rows = self._fetchall(
            """
            SELECT ticker, exchange, company_name, industry, sector, short_industry, cap_ratio
            FROM symbols
            WHERE ticker IS NOT NULL
            """
        )
        query = """
        UNWIND $rows AS row
        MERGE (s:Symbol {ticker: row.ticker})
        SET s.exchange = row.exchange,
            s.company_name = row.company_name,
            s.industry = row.industry,
            s.sector = row.sector,
            s.short_industry = row.short_industry,
            s.cap_ratio = row.cap_ratio
        """
        return self._write_batches(query, rows, label="symbols")

    def sync_posts(self) -> int:
        post_groups = self._fetchall(
            "SELECT post_group_id AS id, fireant_post_group_id, name FROM post_groups"
        )
        post_sources = self._fetchall(
            "SELECT post_source_id AS id, fireant_post_source_id, name FROM post_sources"
        )
        posts = self._fetchall(
            """
            SELECT post_id, fireant_post_id, title, published_at, post_group_id, post_source_id
            FROM posts
            """
        )

        c_groups = self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (g:PostGroup {id: row.id})
            SET g.name = row.name, g.fireant_post_group_id = row.fireant_post_group_id
            """,
            post_groups,
            label="post_groups",
        )
        c_sources = self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (s:PostSource {id: row.id})
            SET s.name = row.name, s.fireant_post_source_id = row.fireant_post_source_id
            """,
            post_sources,
            label="post_sources",
        )
        c_posts = self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (p:Post {post_id: row.post_id})
            SET p.fireant_post_id = row.fireant_post_id,
                p.title = row.title,
                p.published_at = row.published_at
            WITH p, row
            FOREACH (_ IN CASE WHEN row.post_group_id IS NULL THEN [] ELSE [1] END |
              MERGE (g:PostGroup {id: row.post_group_id})
              MERGE (p)-[:BELONGS_TO_GROUP]->(g)
            )
            FOREACH (_ IN CASE WHEN row.post_source_id IS NULL THEN [] ELSE [1] END |
              MERGE (s:PostSource {id: row.post_source_id})
              MERGE (p)-[:FROM_SOURCE]->(s)
            )
            """,
            posts,
            label="posts",
        )
        return c_groups + c_sources + c_posts

    def sync_post_mentions(self) -> int:
        rows = self._fetchall(
            """
            SELECT ts.post_id, ts.symbol_ticker
            FROM tagged_symbols ts
            JOIN posts p ON p.post_id = ts.post_id
            JOIN symbols s ON s.ticker = ts.symbol_ticker
            """
        )
        query = """
        UNWIND $rows AS row
        MATCH (p:Post {post_id: row.post_id})
        MATCH (s:Symbol {ticker: row.symbol_ticker})
        MERGE (p)-[:MENTIONS]->(s)
        """
        return self._write_batches(query, rows, label="post_mentions")

    def sync_holders(self) -> int:
        rows = self._fetchall(
            """
            SELECT symbol_ticker, name, position, is_organization, is_foreigner, is_foundation,
                   shares, ownership, reported
            FROM major_holders
            WHERE symbol_ticker IS NOT NULL AND name IS NOT NULL
            """
        )
        query = """
        UNWIND $rows AS row
        MERGE (h:Holder {name: row.name})
        SET h.position = row.position,
            h.is_organization = row.is_organization,
            h.is_foreigner = row.is_foreigner,
            h.is_foundation = row.is_foundation
        WITH h, row
        MATCH (s:Symbol {ticker: row.symbol_ticker})
        MERGE (h)-[r:HOLDS]->(s)
        SET r.shares = row.shares,
            r.ownership = row.ownership,
            r.reported = row.reported
        """
        return self._write_batches(query, rows, label="holders")

    def sync_subsidiaries(self) -> int:
        rows = self._fetchall(
            """
            SELECT symbol_ticker, sub_symbol AS symbol, exchange, company_name AS name, type, is_listed,
                   ownership, shares
            FROM subsidiaries
            WHERE symbol_ticker IS NOT NULL AND company_name IS NOT NULL
            """
        )
        query = """
        UNWIND $rows AS row
        MERGE (c:Company {name: row.name, symbol: coalesce(row.symbol, row.name)})
        SET c.exchange = row.exchange,
            c.type = row.type,
            c.is_listed = row.is_listed
        WITH c, row
        MATCH (s:Symbol {ticker: row.symbol_ticker})
        MERGE (s)-[r:HAS_SUBSIDIARY]->(c)
        SET r.ownership = row.ownership,
            r.shares = row.shares
        """
        return self._write_batches(query, rows, label="subsidiaries")

    def sync_sector_industry(self) -> int:
        rows = self._fetchall(
            """
            SELECT ticker, sector, industry
            FROM symbols
            WHERE ticker IS NOT NULL
            """
        )
        query = """
        UNWIND $rows AS row
        MATCH (s:Symbol {ticker: row.ticker})
        FOREACH (_ IN CASE WHEN row.sector IS NULL OR row.sector = '' THEN [] ELSE [1] END |
          MERGE (sec:Sector {name: row.sector})
          MERGE (s)-[:IN_SECTOR]->(sec)
        )
        FOREACH (_ IN CASE WHEN row.industry IS NULL OR row.industry = '' THEN [] ELSE [1] END |
          MERGE (ind:Industry {name: row.industry})
          MERGE (s)-[:IN_INDUSTRY]->(ind)
        )
        """
        return self._write_batches(query, rows, label="sector_industry")

    def sync_reports(self) -> int:
        reports = self._fetchall(
            """
            SELECT id, symbol_ticker, name, display_name, type, lever
            FROM reports
            """
        )
        report_data = self._fetchall(
            """
            SELECT id, report_id, year, quarter, value
            FROM report_data
            """
        )
        c_reports = self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (r:Report {id: row.id})
            SET r.name = row.name,
                r.display_name = row.display_name,
                r.type = row.type,
                r.lever = row.lever
            WITH r, row
            MATCH (s:Symbol {ticker: row.symbol_ticker})
            MERGE (s)-[:HAS_REPORT]->(r)
            """,
            reports,
            label="reports",
        )
        c_report_data = self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (rd:ReportData {id: row.id})
            SET rd.year = row.year,
                rd.quarter = row.quarter,
                rd.value = row.value
            WITH rd, row
            MATCH (r:Report {id: row.report_id})
            MERGE (r)-[:HAS_DATA]->(rd)
            """,
            report_data,
            label="report_data",
        )
        return c_reports + c_report_data

    def sync_market_mentions(self) -> int:
        rows = self._fetchall(
            """
            SELECT symbol_ticker, date, day, week, month, day_color, week_color, month_color
            FROM market_mentions
            WHERE symbol_ticker IS NOT NULL AND date IS NOT NULL
            """
        )
        query = """
        UNWIND $rows AS row
        MERGE (d:Date {date: row.date})
        WITH d, row
        MATCH (s:Symbol {ticker: row.symbol_ticker})
        MERGE (s)-[r:MENTIONED_ON]->(d)
        SET r.day = row.day,
            r.week = row.week,
            r.month = row.month,
            r.day_color = row.day_color,
            r.week_color = row.week_color,
            r.month_color = row.month_color
        """
        return self._write_batches(query, rows, label="market_mentions")

    def sync_co_mentions(self) -> int:
        rows = self._fetchall(
            """
            SELECT
              LEAST(t1.symbol_ticker, t2.symbol_ticker) AS ticker_a,
              GREATEST(t1.symbol_ticker, t2.symbol_ticker) AS ticker_b,
              COUNT(DISTINCT t1.post_id) AS weight
            FROM tagged_symbols t1
            JOIN tagged_symbols t2
              ON t1.post_id = t2.post_id
             AND t1.symbol_ticker < t2.symbol_ticker
            GROUP BY 1, 2
            """
        )
        query = """
        UNWIND $rows AS row
        MATCH (a:Symbol {ticker: row.ticker_a})
        MATCH (b:Symbol {ticker: row.ticker_b})
        MERGE (a)-[r:CO_MENTIONED]->(b)
        SET r.weight = row.weight
        """
        return self._write_batches(query, rows, label="co_mentions")

    def sync_symbol_by_id(self, ticker: str) -> int:
        rows = self._fetchall(
            """
            SELECT ticker, exchange, company_name, industry, sector, short_industry, cap_ratio
            FROM symbols
            WHERE ticker = :ticker
            """,
            {"ticker": ticker},
        )
        if not rows:
            self.neo4j.execute_write("MATCH (s:Symbol {ticker: $ticker}) DETACH DELETE s", {"ticker": ticker})
            return 0
        count = self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (s:Symbol {ticker: row.ticker})
            SET s.exchange = row.exchange,
                s.company_name = row.company_name,
                s.industry = row.industry,
                s.sector = row.sector,
                s.short_industry = row.short_industry,
                s.cap_ratio = row.cap_ratio
            """,
            rows,
            label="symbol_by_id",
        )
        self.sync_sector_industry_by_ticker(ticker)
        return count

    def sync_post_by_id(self, post_id: int) -> int:
        rows = self._fetchall(
            """
            SELECT post_id, fireant_post_id, title, published_at, post_group_id, post_source_id
            FROM posts
            WHERE post_id = :post_id
            """,
            {"post_id": post_id},
        )
        if not rows:
            self.neo4j.execute_write("MATCH (p:Post {post_id: $post_id}) DETACH DELETE p", {"post_id": post_id})
            return 0
        return self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (p:Post {post_id: row.post_id})
            SET p.fireant_post_id = row.fireant_post_id,
                p.title = row.title,
                p.published_at = row.published_at
            WITH p, row
            FOREACH (_ IN CASE WHEN row.post_group_id IS NULL THEN [] ELSE [1] END |
              MERGE (g:PostGroup {id: row.post_group_id})
              MERGE (p)-[:BELONGS_TO_GROUP]->(g)
            )
            FOREACH (_ IN CASE WHEN row.post_source_id IS NULL THEN [] ELSE [1] END |
              MERGE (s:PostSource {id: row.post_source_id})
              MERGE (p)-[:FROM_SOURCE]->(s)
            )
            """,
            rows,
            label="post_by_id",
        )

    def sync_post_mentions_by_post_id(self, post_id: int) -> int:
        self.neo4j.execute_write(
            """
            MATCH (p:Post {post_id: $post_id})-[r:MENTIONS]->(:Symbol)
            DELETE r
            """,
            {"post_id": post_id},
        )
        rows = self._fetchall(
            """
            SELECT ts.post_id, ts.symbol_ticker
            FROM tagged_symbols ts
            WHERE ts.post_id = :post_id
            """,
            {"post_id": post_id},
        )
        count = self._write_batches(
            """
            UNWIND $rows AS row
            MATCH (p:Post {post_id: row.post_id})
            MATCH (s:Symbol {ticker: row.symbol_ticker})
            MERGE (p)-[:MENTIONS]->(s)
            """,
            rows,
            label="post_mentions_by_post_id",
        )
        self._recompute_co_mentions_for_post(post_id)
        return count

    def sync_holder_by_id(self, holder_id: int) -> int:
        rows = self._fetchall(
            """
            SELECT id, symbol_ticker, name, position, is_organization, is_foreigner, is_foundation,
                   shares, ownership, reported
            FROM major_holders
            WHERE id = :holder_id
            """,
            {"holder_id": holder_id},
        )
        if not rows:
            return 0
        return self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (h:Holder {name: row.name})
            SET h.position = row.position,
                h.is_organization = row.is_organization,
                h.is_foreigner = row.is_foreigner,
                h.is_foundation = row.is_foundation
            WITH h, row
            MATCH (s:Symbol {ticker: row.symbol_ticker})
            MERGE (h)-[r:HOLDS]->(s)
            SET r.shares = row.shares, r.ownership = row.ownership, r.reported = row.reported
            """,
            rows,
            label="holder_by_id",
        )

    def sync_subsidiary_by_id(self, subsidiary_id: int) -> int:
        rows = self._fetchall(
            """
            SELECT id, symbol_ticker, sub_symbol AS symbol, exchange, company_name AS name, type, is_listed,
                   ownership, shares
            FROM subsidiaries
            WHERE id = :subsidiary_id
            """,
            {"subsidiary_id": subsidiary_id},
        )
        if not rows:
            return 0
        return self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (c:Company {name: row.name, symbol: coalesce(row.symbol, row.name)})
            SET c.exchange = row.exchange,
                c.type = row.type,
                c.is_listed = row.is_listed
            WITH c, row
            MATCH (s:Symbol {ticker: row.symbol_ticker})
            MERGE (s)-[r:HAS_SUBSIDIARY]->(c)
            SET r.ownership = row.ownership, r.shares = row.shares
            """,
            rows,
            label="subsidiary_by_id",
        )

    def sync_report_by_id(self, report_id: int) -> int:
        rows = self._fetchall(
            """
            SELECT id, symbol_ticker, name, display_name, type, lever
            FROM reports
            WHERE id = :report_id
            """,
            {"report_id": report_id},
        )
        if not rows:
            self.neo4j.execute_write("MATCH (r:Report {id: $id}) DETACH DELETE r", {"id": report_id})
            return 0
        return self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (r:Report {id: row.id})
            SET r.name = row.name, r.display_name = row.display_name, r.type = row.type, r.lever = row.lever
            WITH r, row
            MATCH (s:Symbol {ticker: row.symbol_ticker})
            MERGE (s)-[:HAS_REPORT]->(r)
            """,
            rows,
            label="report_by_id",
        )

    def sync_report_data_by_id(self, report_data_id: int) -> int:
        rows = self._fetchall(
            """
            SELECT id, report_id, year, quarter, value
            FROM report_data
            WHERE id = :report_data_id
            """,
            {"report_data_id": report_data_id},
        )
        if not rows:
            self.neo4j.execute_write("MATCH (rd:ReportData {id: $id}) DETACH DELETE rd", {"id": report_data_id})
            return 0
        return self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (rd:ReportData {id: row.id})
            SET rd.year = row.year, rd.quarter = row.quarter, rd.value = row.value
            WITH rd, row
            MATCH (r:Report {id: row.report_id})
            MERGE (r)-[:HAS_DATA]->(rd)
            """,
            rows,
            label="report_data_by_id",
        )

    def sync_market_mention_by_id(self, market_mention_id: int) -> int:
        rows = self._fetchall(
            """
            SELECT id, symbol_ticker, date, day, week, month, day_color, week_color, month_color
            FROM market_mentions
            WHERE id = :market_mention_id
            """,
            {"market_mention_id": market_mention_id},
        )
        if not rows:
            return 0
        return self._write_batches(
            """
            UNWIND $rows AS row
            MERGE (d:Date {date: row.date})
            WITH d, row
            MATCH (s:Symbol {ticker: row.symbol_ticker})
            MERGE (s)-[r:MENTIONED_ON]->(d)
            SET r.day = row.day, r.week = row.week, r.month = row.month,
                r.day_color = row.day_color, r.week_color = row.week_color, r.month_color = row.month_color
            """,
            rows,
            label="market_mention_by_id",
        )

    def sync_entity_event(self, event: dict[str, Any]) -> int:
        entity_type = event["entity_type"]
        entity_id = event["entity_id"]
        action = event["action"]
        if action == "deleted":
            return self.delete_entity_event(event)
        if entity_type == "symbol":
            return self.sync_symbol_by_id(entity_id)
        if entity_type == "post":
            count = self.sync_post_by_id(int(entity_id))
            count += self.sync_post_mentions_by_post_id(int(entity_id))
            return count
        if entity_type == "tagged_symbol":
            post_id = int((event.get("payload") or {}).get("post_id", entity_id))
            return self.sync_post_mentions_by_post_id(post_id)
        if entity_type == "major_holder":
            return self.sync_holder_by_id(int(entity_id))
        if entity_type == "subsidiary":
            return self.sync_subsidiary_by_id(int(entity_id))
        if entity_type == "report":
            return self.sync_report_by_id(int(entity_id))
        if entity_type == "report_data":
            return self.sync_report_data_by_id(int(entity_id))
        if entity_type == "market_mention":
            return self.sync_market_mention_by_id(int(entity_id))
        return 0

    def delete_entity_event(self, event: dict[str, Any]) -> int:
        entity_type = event["entity_type"]
        entity_id = event["entity_id"]
        if entity_type == "symbol":
            self.neo4j.execute_write("MATCH (s:Symbol {ticker: $id}) DETACH DELETE s", {"id": entity_id})
        elif entity_type == "post":
            self.neo4j.execute_write("MATCH (p:Post {post_id: $id}) DETACH DELETE p", {"id": int(entity_id)})
            payload = event.get("payload") or {}
            post_id = int(payload.get("post_id", entity_id))
            self._recompute_co_mentions_for_post(post_id)
        elif entity_type == "tagged_symbol":
            payload = event.get("payload") or {}
            post_id = int(payload.get("post_id", entity_id))
            self.sync_post_mentions_by_post_id(post_id)
        elif entity_type == "report":
            self.neo4j.execute_write("MATCH (r:Report {id: $id}) DETACH DELETE r", {"id": int(entity_id)})
        elif entity_type == "report_data":
            self.neo4j.execute_write("MATCH (rd:ReportData {id: $id}) DETACH DELETE rd", {"id": int(entity_id)})
        return 1

    def sync_all(self) -> GraphSyncStats:
        self.ensure_constraints()
        stats = GraphSyncStats(
            symbols=self.sync_symbols(),
            posts=self.sync_posts(),
            post_mentions=self.sync_post_mentions(),
            holders=self.sync_holders(),
            subsidiaries=self.sync_subsidiaries(),
            sector_industry=self.sync_sector_industry(),
            reports=self.sync_reports(),
            market_mentions=self.sync_market_mentions(),
            co_mentions=self.sync_co_mentions(),
        )
        logger.info("Neo4j sync_all completed stats={stats}", stats=stats.to_dict())
        return stats

    def _fetchall(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rows = self.session.execute(text(sql), params or {}).fetchall()
        return [self._normalize_row(dict(r._mapping)) for r in rows]

    def sync_sector_industry_by_ticker(self, ticker: str) -> int:
        rows = self._fetchall(
            "SELECT ticker, sector, industry FROM symbols WHERE ticker = :ticker",
            {"ticker": ticker},
        )
        return self._write_batches(
            """
            UNWIND $rows AS row
            MATCH (s:Symbol {ticker: row.ticker})
            FOREACH (_ IN CASE WHEN row.sector IS NULL OR row.sector = '' THEN [] ELSE [1] END |
              MERGE (sec:Sector {name: row.sector})
              MERGE (s)-[:IN_SECTOR]->(sec)
            )
            FOREACH (_ IN CASE WHEN row.industry IS NULL OR row.industry = '' THEN [] ELSE [1] END |
              MERGE (ind:Industry {name: row.industry})
              MERGE (s)-[:IN_INDUSTRY]->(ind)
            )
            """,
            rows,
            label="sector_industry_by_ticker",
        )

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in row.items():
            if isinstance(value, Decimal):
                out[key] = float(value)
            elif isinstance(value, (datetime, date)):
                out[key] = value.isoformat()
            else:
                out[key] = value
        return out

    def _write_batches(self, query: str, rows: list[dict[str, Any]], label: str) -> int:
        if not rows:
            logger.info("Neo4j sync skipped label={label} reason=empty_rows", label=label)
            return 0

        total = 0
        iterator = iter(rows)
        while True:
            batch = list(islice(iterator, self.batch_size))
            if not batch:
                break
            self.neo4j.execute_write(query, {"rows": batch})
            total += len(batch)
            logger.debug("Neo4j batch synced label={label} batch_size={size}", label=label, size=len(batch))

        logger.info("Neo4j sync done label={label} rows={rows}", label=label, rows=total)
        return total

    def _recompute_co_mentions_for_post(self, post_id: int) -> None:
        symbols = self._fetchall(
            "SELECT symbol_ticker FROM tagged_symbols WHERE post_id = :post_id ORDER BY symbol_ticker",
            {"post_id": post_id},
        )
        tickers = [str(r["symbol_ticker"]) for r in symbols if r.get("symbol_ticker")]
        pairs: set[tuple[str, str]] = set()
        for i in range(len(tickers)):
            for j in range(i + 1, len(tickers)):
                a = min(tickers[i], tickers[j])
                b = max(tickers[i], tickers[j])
                pairs.add((a, b))

        for ticker_a, ticker_b in pairs:
            count_rows = self._fetchall(
                """
                SELECT COUNT(DISTINCT t1.post_id) AS weight
                FROM tagged_symbols t1
                JOIN tagged_symbols t2
                  ON t1.post_id = t2.post_id
                 AND t1.symbol_ticker = :ticker_a
                 AND t2.symbol_ticker = :ticker_b
                """,
                {"ticker_a": ticker_a, "ticker_b": ticker_b},
            )
            weight = int(count_rows[0]["weight"]) if count_rows else 0
            if weight <= 0:
                self.neo4j.execute_write(
                    """
                    MATCH (a:Symbol {ticker: $ticker_a})-[r:CO_MENTIONED]->(b:Symbol {ticker: $ticker_b})
                    DELETE r
                    """,
                    {"ticker_a": ticker_a, "ticker_b": ticker_b},
                )
            else:
                self.neo4j.execute_write(
                    """
                    MATCH (a:Symbol {ticker: $ticker_a})
                    MATCH (b:Symbol {ticker: $ticker_b})
                    MERGE (a)-[r:CO_MENTIONED]->(b)
                    SET r.weight = $weight
                    """,
                    {"ticker_a": ticker_a, "ticker_b": ticker_b, "weight": weight},
                )
