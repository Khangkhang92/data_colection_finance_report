from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
    Date,
)
from sqlalchemy.orm import relationship
from .base import CommonModel


class Market(CommonModel):
    __tablename__ = "market"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Added primary key
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )  # Corrected FK
    date = Column(Date)

    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    close = Column(Float)

    average = Column(Float)

    price_previous_close = Column(Float)
    price_basic = Column(Float)
    total_volume = Column(Float)
    deal_volume = Column(Float)
    volume = Column(Float)
    putthrough_volume = Column(Float)
    total_trade = Column(Float)
    total_value = Column(Float)
    putthrough_value = Column(Float)
    buy_foreign_quantity = Column(Float)
    buy_foreign_value = Column(Float)
    sell_foreign_quantity = Column(Float)
    sell_foreign_value = Column(Float)
    buy_count = Column(Float)
    buy_quantity = Column(Float)
    sell_count = Column(Float)
    sell_quantity = Column(Float)
    buy_avg = Column(Float)
    sell_avg = Column(Float)
    adj_ratio = Column(Float)
    adj_close = Column(Float)
    adj_open = Column(Float)
    adj_high = Column(Float)
    adj_low = Column(Float)
    current_foreign_room = Column(Float)
    shares = Column(Float)
    shares_out_standing = Column(Float)
    market_cap = Column(Float)
    market_capitalization = Column(Float)
    free_shares = Column(Float)

    symbol = relationship("Symbol", back_populates="markets")

    __table_args__ = (
        UniqueConstraint("symbol_ticker", "date", name="uix_symbol_date"),
    )
