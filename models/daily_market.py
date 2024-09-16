from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    Date,
    UniqueConstraint,
    text,
)
from .base import CommonModel
from sqlalchemy.orm import relationship
import datetime


class DailyMarket(CommonModel):
    __tablename__ = "daily_market"

    id = Column(Integer, primary_key=True)
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )
    price_percent_change = Column(Float)
    price_change = Column(Float)
    total_active_buy_volume = Column(Float)
    total_active_sell_volume = Column(Float)
    buy_foreign_quantity = Column(Float)
    buy_foreign_value = Column(Float)
    sell_foreign_quantity = Column(Float)
    sell_foreign_value = Column(Float)
    current_foreign_room = Column(Float)
    total_volume = Column(Float)
    total_value = Column(Float)
    date = Column(Date)

    symbol = relationship("Symbol", back_populates="daily_markets")

    def __repr__(self):
        return f"<UpdateQuote(symbol='{self.symbol}', date='{self.date}')>"

    __table_args__ = (
        UniqueConstraint("symbol_ticker", "date", name="uq_update_quote_symbol_date"),
    )

    @classmethod
    def upsert_daily_market(cls, session):
        current_time = datetime.datetime.now().time()
        if current_time.hour >= 15:
            session.execute(
                text(
                    """
            INSERT INTO daily_market (
                symbol_ticker, price_percent_change, price_change, 
                total_active_buy_volume, total_active_sell_volume,
                buy_foreign_quantity, buy_foreign_value,
                sell_foreign_quantity, sell_foreign_value,
                current_foreign_room, total_volume, total_value, date
            )
            SELECT
                symbol_ticker, price_percent_change, price_change, 
                total_active_buy_volume, total_active_sell_volume,
                buy_foreign_quantity, buy_foreign_value,
                sell_foreign_quantity, sell_foreign_value,
                current_foreign_room, total_volume, total_value, date
            FROM update_quote
            WHERE date = CURRENT_DATE
            ON CONFLICT (symbol_ticker, date) DO UPDATE
            SET
                price_percent_change = EXCLUDED.price_percent_change,
                price_change = EXCLUDED.price_change,
                total_active_buy_volume = EXCLUDED.total_active_buy_volume,
                total_active_sell_volume = EXCLUDED.total_active_sell_volume,
                buy_foreign_quantity = EXCLUDED.buy_foreign_quantity,
                buy_foreign_value = EXCLUDED.buy_foreign_value,
                sell_foreign_quantity = EXCLUDED.sell_foreign_quantity,
                sell_foreign_value = EXCLUDED.sell_foreign_value,
                current_foreign_room = EXCLUDED.current_foreign_room,
                total_volume = EXCLUDED.total_volume,
                total_value = EXCLUDED.total_value
            """
                )
            )
            session.commit()
