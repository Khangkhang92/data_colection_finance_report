from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    Date,
    UniqueConstraint,
)
from .base import CommonModel
from sqlalchemy.orm import relationship

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
    
 
    symbol = relationship("Symbol", back_populates="daily_market")

    def __repr__(self):
        return f"<UpdateQuote(symbol='{self.symbol}', date='{self.date}')>"
    

    __table_args__ = (
       UniqueConstraint('symbol_ticker', 'date', name='uq_update_quote_symbol_date'),
   )
