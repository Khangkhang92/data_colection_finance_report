from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    UniqueConstraint,
    Date,
)
from sqlalchemy.orm import relationship
from .base import CommonModel


class MarketMention(CommonModel):
    __tablename__ = "market_mentions"
    id = Column(Integer, primary_key=True, autoincrement=True) 
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )
    day = Column(Integer)
    day_color = Column(String)
    week = Column(Integer) 
    week_color = Column(String)
    month = Column(Integer)   
    month_color = Column(String)
    date = Column(Date)
    symbol = relationship("Symbol", back_populates="market_mentions")

    __table_args__ = (
        UniqueConstraint("symbol_ticker", "date", name="uix_symbol_date_market_metion"),
    )