from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import CommonModel


class UpdateQuote(CommonModel):
    __tablename__ = "update_quote"

    id = Column(Integer, primary_key=True)

    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )
    price_current = Column(Float)
    price_last = Column(Float)
    price_high = Column(Float)
    price_low = Column(Float)
    price_open = Column(Float)
    price_close = Column(Float)
    price_average = Column(Float)
    price_change = Column(Float)
    price_percent_change = Column(Float)
    volume = Column(Float)
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
    buy_count = Column(Float)
    sell_count = Column(Float)
    buy_quantity = Column(Float)
    sell_quantity = Column(Float)
    price_bid1 = Column(Float)
    quantity_bid1 = Column(Float)
    price_bid2 = Column(Float)
    quantity_bid2 = Column(Float)
    price_bid3 = Column(Float)
    quantity_bid3 = Column(Float)
    price_ask1 = Column(Float)
    quantity_ask1 = Column(Float)
    price_ask2 = Column(Float)
    quantity_ask2 = Column(Float)
    price_ask3 = Column(Float)
    quantity_ask3 = Column(Float)
    datetime = Column(DateTime(timezone=True))

    symbol = relationship("Symbol", back_populates="update_quote")

    def __repr__(self):
        return f"<UpdateQuote(symbol='{self.symbol}', date='{self.date}')>"

    __table_args__ = (
        UniqueConstraint("symbol_ticker", "date", name="uq_update_quote_symbol_date2"),
    )


class SessionQuote(CommonModel):
    __tablename__ = "session_quote"

    id = Column(Integer, primary_key=True)

    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )
    side = Column(String(3))
    match_price = Column(Float)
    volume = Column(Float)
    total_volume = Column(Float)
    datetime = Column(DateTime(timezone=True))

    symbol = relationship("Symbol", back_populates="session_quote")

    __table_args__ = (
        UniqueConstraint(
            "symbol_ticker", "datetime", name="uq_update_quote_symbol_datetime"
        ),
    )
