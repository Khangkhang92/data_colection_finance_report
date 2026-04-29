from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from .base import CommonModel


class IntradayQuote(CommonModel):
    __tablename__ = "intraday_quotes"

    id = Column(Integer, primary_key=True)
    quote_id = Column(Integer, nullable=False)
    symbol = Column(String(10), nullable=False)
    date = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    total_volume = Column(Float, nullable=False)
    side = Column(String(1))

    def __repr__(self):
        return f"<IntradayQuote(quote_id={self.quote_id}, symbol='{self.symbol}', date='{self.date}', price={self.price}, volume={self.volume}, total_volume={self.total_volume}, side='{self.side}')>"
