from __future__ import annotations

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from finance_api.utils.dates import parse_datetime
from finance_schema.models import CommodityContract, CoveredWarrantInfo, DerivativeContract, Symbol


class ExtendedInstrumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert_symbol(self, row: dict) -> None:
        stmt = insert(Symbol).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["ticker"],
            set_={key: row.get(key) for key in row if key != "ticker"},
        )
        self.session.execute(stmt)

    def upsert_derivative_contract(self, row: dict) -> None:
        stmt = insert(DerivativeContract).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_ticker"],
            set_={key: row.get(key) for key in row if key != "symbol_ticker"},
        )
        self.session.execute(stmt)

    def upsert_warrant_info(self, raw: dict) -> None:
        symbol = raw.get("symbol")
        if not symbol:
            return
        row = {
            "symbol_ticker": str(symbol).upper(),
            "real_name": raw.get("realName"),
            "fire_ant_name": raw.get("fireAntName"),
            "issuer": raw.get("issuer"),
            "issuer_symbol": raw.get("issuerSymbol"),
            "original_issued_price": raw.get("originalIssuedPrice"),
            "last_issued_price": raw.get("lastIssuedPrice"),
            "option_choice": raw.get("optionChoice"),
            "option_type": raw.get("optionType"),
            "right": raw.get("right"),
            "original_exercise_price": raw.get("originalExercisePrice"),
            "exercise_price": raw.get("exercisePrice"),
            "paid_price": raw.get("paidPrice"),
            "original_exercise_ratio": raw.get("originalExerciseRatio"),
            "exercise_ratio": raw.get("exerciseRatio"),
            "basic_securities_symbol": raw.get("basicSecuritiesSymbol"),
            "listed_shares": raw.get("listedShares"),
            "outstanding_shares": raw.get("outStandingShares"),
            "issued_day": parse_datetime(raw.get("issuedDay")),
            "last_issued_day": parse_datetime(raw.get("lastIssuedDay")),
            "listed_day": parse_datetime(raw.get("listedDay")),
            "first_trading_day": parse_datetime(raw.get("firstTradingDay")),
            "due_date": parse_datetime(raw.get("duedDate")),
            "last_trading_day": parse_datetime(raw.get("lastTradingDay")),
            "duration": raw.get("duration"),
            "mode_of_exercise_of_rights": raw.get("modeOfExerciseOfRights"),
            "isin_code": raw.get("isinCode"),
            "value_of_payment_security_assets": raw.get("valueOfPaymentSecurityAssets"),
            "last_value_of_payment_security_assets": raw.get(
                "lastValueOfPaymentSecurityAssets"
            ),
            "value_of_payment_security_assets_percent": raw.get(
                "valueOfPaymentSecurityAssetsProcent"
            ),
            "last_value_of_payment_security_assets_percent": raw.get(
                "lastValueOfPaymentSecurityAssetsProcent"
            ),
            "market_capitalization": raw.get("marketCapitalization"),
            "warrant_price": raw.get("warrantPrice"),
            "basic_securities_price": raw.get("basicSecuritiesPrice"),
            "break_even_price": raw.get("breakEvenPrice"),
            "cw_status": raw.get("cwStatus"),
            "listing_status": raw.get("listingStatus"),
            "source_last_updated": parse_datetime(raw.get("lastUpdated")),
            "source_symbol_id": raw.get("symbolID"),
        }
        stmt = insert(CoveredWarrantInfo).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol_ticker"],
            set_={key: row.get(key) for key in row if key != "symbol_ticker"},
        )
        self.session.execute(stmt)

    def upsert_commodity_contract(self, raw: dict) -> None:
        contract_code = raw.get("contractCode") or raw.get("symbol")
        if not contract_code:
            return
        row = {
            "contract_code": str(contract_code).upper(),
            "symbol_ticker": raw.get("symbol"),
            "contract_name": raw.get("contractName") or raw.get("name"),
            "commodity_code": raw.get("commodityCode") or raw.get("commoditySymbol"),
            "sub_type": raw.get("subType"),
            "status": raw.get("status"),
            "first_trading_date": parse_datetime(raw.get("firstTradingDate")),
            "last_trading_date": parse_datetime(raw.get("lastTradingDate")),
            "expiration_date": parse_datetime(raw.get("expirationDate")),
            "multiplier": raw.get("multiplier"),
            "exchange": raw.get("exchange"),
            "contract_unit": raw.get("contractUnit"),
            "currency": raw.get("currency"),
        }
        stmt = insert(CommodityContract).values(**row)
        stmt = stmt.on_conflict_do_update(
            index_elements=["contract_code"],
            set_={key: row.get(key) for key in row if key != "contract_code"},
        )
        self.session.execute(stmt)
