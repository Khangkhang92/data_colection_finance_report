from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from .base import CommonModel


class Symbol(CommonModel):
    __tablename__ = "symbol"
    ticker = Column(String(length=15), primary_key=True, nullable=False)
    exchange = Column(String(length=20), nullable=False)
    company_name = Column(String)
    industry = Column(String)
    sector = Column(String)
    short_industry = Column(String)
    cap_ratio = Column(Integer)

    reports = relationship("Report", back_populates="symbol")
    markets = relationship("Market", back_populates="symbol")
    update_quote = relationship(
        "UpdateQuote", back_populates="symbol", uselist=False
    )  # one to one
    major_holders = relationship("MajorHolder", back_populates="symbol")

    daily_markets = relationship("DailyMarket", back_populates="symbol")
    history_data_processings = relationship(
        "HistoryDataProcessing", back_populates="symbol"
    )
    tagged_symbols = relationship("TaggedSymbol", back_populates="symbol")

    score = relationship("Score", back_populates="symbol")
    market_mentions = relationship("MarketMention", back_populates="symbol")