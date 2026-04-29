from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from finance_api.utils.dates import parse_date
from finance_schema.models import MajorHolder, Subsidiaries


class CompanyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def replace_holders(self, symbol: str, rows: list[dict]) -> int:
        self.session.execute(delete(MajorHolder).where(MajorHolder.symbol_ticker == symbol))
        objects = [MajorHolder(**self._holder_values(symbol, row)) for row in rows]
        self.session.add_all(objects)
        return len(objects)

    def replace_subsidiaries(self, symbol: str, rows: list[dict]) -> int:
        self.session.execute(delete(Subsidiaries).where(Subsidiaries.symbol_ticker == symbol))
        objects = [Subsidiaries(**self._subsidiary_values(symbol, row)) for row in rows]
        self.session.add_all(objects)
        return len(objects)

    def _holder_values(self, symbol: str, row: dict) -> dict:
        return {
            "symbol_ticker": symbol,
            "name": row.get("name") or row.get("Name"),
            "position": row.get("position") or row.get("Position"),
            "shares": row.get("shares") or row.get("Shares"),
            "ownership": row.get("ownership") or row.get("Ownership"),
            "is_organization": row.get("isOrganization", row.get("is_organization")),
            "is_foreigner": row.get("isForeigner", row.get("is_foreigner")),
            "is_foundation": row.get("isFounder", row.get("is_foundation")),
            "is_listing": row.get("isListing", row.get("is_listing")),
            "listing_symbol": row.get("listingSymbol") or row.get("listing_symbol"),
            "reported": parse_date(row.get("reported") or row.get("Reported")),
        }

    def _subsidiary_values(self, symbol: str, row: dict) -> dict:
        return {
            "symbol_ticker": symbol,
            "sub_symbol": row.get("symbol") or row.get("sub_symbol"),
            "exchange": row.get("exchange"),
            "company_name": row.get("companyName") or row.get("company_name"),
            "short_name": row.get("shortName") or row.get("short_name"),
            "international_name": row.get("internationalName") or row.get("international_name"),
            "company_profile": row.get("companyProfile") or row.get("company_profile"),
            "type": row.get("type"),
            "ownership": row.get("ownership"),
            "shares": row.get("shares"),
            "is_listed": row.get("isListed", row.get("is_listed")),
            "charter_capital": row.get("charterCapital") or row.get("charter_capital"),
        }
