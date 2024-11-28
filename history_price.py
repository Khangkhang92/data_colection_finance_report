from getdata.base import Base
from loguru import logger
import os
from common.db import ScopedSession
from sqlalchemy.dialects.postgresql import insert
from models import HistoryPrice
from datetime import datetime, timedelta


base_call_api = Base(os.getenv("SUBSIDIARIES"))
all_symbols = base_call_api.get_all_symbols()

end_date = datetime.today()
start_date = datetime.today() - timedelta(days=250)
limit = 250
print(end_date)
def tranfer_data(history_data):
    return {
        "symbol_ticker": history_data.get("symbol"),
        "price_high" : history_data.get("priceHigh"),
        "price_low" : history_data.get("priceLow"),
        "price_open" : history_data.get("priceOpen"),
        "price_average" : history_data.get("priceAverage"),
        "price_close" : history_data.get("priceClose"),
        "price_basic" : history_data.get("priceBasic"),
        "total_volume" : history_data.get("totalVolume"),
        "deal_volume" : history_data.get("dealVolume"),
        "putthrough_volume" : history_data.get("putthroughVolume"),
        "total_value" : history_data.get("totalValue"),
        "putthrough_value" : history_data.get("putthroughValue"),
        "buy_foreign_quantity" : history_data.get("buyForeignQuantity"),
        "buy_foreign_value" : history_data.get("buyForeignValue"),
        "sell_foreign_quantity" : history_data.get("sellForeignQuantity"),
        "sell_foreign_value" : history_data.get("sellForeignValue"),
        "buy_count" : history_data.get("buyCount"),
        "buy_quantity" : history_data.get("buyQuantity"),
        "sell_count" : history_data.get("sellCount"),
        "sell_quantity" : history_data.get("sellQuantity"),
        "adj_ratio" : history_data.get("adjRatio"),
        "current_foreign_room" : history_data.get("currentForeignRoom"),
        "prop_trading_net_deal_value" : history_data.get("propTradingNetDealValue"),
        "prop_trading_net_pt_value" : history_data.get("propTradingNetPTValue"),
        "prop_trading_net_value" : history_data.get("propTradingNetValue"),
        "date" : datetime.fromisoformat(history_data.get("date")).date()
    }


def upsert_history_datas_quotes(history_price):

    if not history_price:
        logger.warning("No data to upsert.")
        return

    with ScopedSession() as session:
        for history_data in history_price:
            data = tranfer_data(history_data)
            stmt = (
                insert(HistoryPrice)
                .values(**data)
                .on_conflict_do_update(
                    index_elements=[
                        "symbol_ticker",
                        "date",
                    ],  # Unique constraint columns
                    set_={
                            "price_high" : data.get("price_high"),
                            "price_low" : data.get("price_low"),
                            "price_open" : data.get("price_open"),
                            "price_average" : data.get("price_average"),
                            "price_close" : data.get("price_close"),
                            "price_basic" : data.get("price_basic"),
                            "total_volume" : data.get("total_volume"),
                            "deal_volume" : data.get("deal_volume"),
                            "putthrough_volume" : data.get("putthrough_volume"),
                            "total_value" : data.get("total_value"),
                            "putthrough_value" : data.get("putthrough_value"),
                            "buy_foreign_quantity" : data.get("buy_foreign_quantity"),
                            "buy_foreign_value" : data.get("buy_foreign_value"),
                            "sell_foreign_quantity" : data.get("sell_foreign_quantity"),
                            "sell_foreign_value" : data.get("sell_foreign_value"),
                            "buy_count" : data.get("buy_count"),
                            "buy_quantity" : data.get("buy_quantity"),
                            "sell_count" : data.get("sell_count"),
                            "sell_quantity" : data.get("sell_quantity"),
                            "adj_ratio" : data.get("adj_ratio"),
                            "current_foreign_room" : data.get("current_foreign_room"),
                            "prop_trading_net_deal_value" : data.get("prop_trading_net_deal_value"),
                            "prop_trading_net_pt_value" : data.get("prop_trading_net_pt_value"),
                            "prop_trading_net_value" : data.get("prop_trading_net_value"),
                    },
                )
            )
            try:
                session.execute(stmt)
            except Exception as e:
                logger.error(e)
        session.commit()
        logger.success(f"history_datas of {symbol}")



base_url = base_call_api.base_url
for symbol in all_symbols:
    base_call_api.base_url = f"{base_url}/{symbol}/historical-quotes"
    history_price = base_call_api.fetch_posts({"startDate": start_date,
                                                     "endDate" : end_date,
                                                     "limit" : limit,
                                                     })
    logger.info(f"get data for {symbol} ok")
    upsert_history_datas_quotes(history_price)
    logger.success(f"history_datas of {symbol}")
