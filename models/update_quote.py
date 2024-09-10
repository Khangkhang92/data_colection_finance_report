from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
    DateTime,
)
from sqlalchemy.orm import relationship
from .base import CommonModel
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
import pytz


class UpdateQuote(CommonModel):
    __tablename__ = "update_quote"

    id = Column(Integer, primary_key=True)
    _date = Column('date', DateTime, nullable=False)

    @hybrid_property
    def date(self):
        return self._date.replace(tzinfo=pytz.UTC).astimezone(pytz.FixedOffset(420))

    @date.setter
    def date(self, value):
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if value.tzinfo is None:
            value = pytz.UTC.localize(value)
        self._date = value.astimezone(pytz.UTC)


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
    total_volume = Column(Float)
    volume = Column(Float)
    total_value = Column(Float)
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
    buy_foreign_value = Column(Float)
    sell_foreign_value = Column(Float)
    buy_foreign_quantity = Column(Float)
    current_foreign_room = Column(Float)
    total_active_buy_volume = Column(Float)
    total_active_sell_volume = Column(Float)
    price_percent_change = Column(Float)
    price_change = Column(Float)


    symbol = relationship("Symbol", back_populates="update_quote")

    def __repr__(self):
        return f"<UpdateQuote(symbol='{self.symbol}', date='{self.date}')>"
