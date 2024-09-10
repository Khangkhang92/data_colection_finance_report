from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

from .base import CommonModel

class IntradayMarketStatistic(CommonModel):
    __tablename__ = 'intraday_market_statistics'

    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    total_trade = Column(Float)
    total_value = Column(Float)
    total_volume = Column(Float)
    index_current = Column(Float)
    buy_foreign_quantity = Column(Float)
    sell_foreign_quantity = Column(Float)
    buy_foreign_value = Column(Float)
    sell_foreign_value = Column(Float)
    advances = Column(Integer)
    declines = Column(Integer)
    unchange = Column(Integer)
    total_volume_pt = Column(Float)
    total_value_pt = Column(Float)
    total_active_buy_volume = Column(Float)
    total_active_sell_volume = Column(Float)
    total_positive_value = Column(Float)
    total_negative_value = Column(Float)
    total_neutral_value = Column(Float)
    cumulative_ad = Column(Float)
    transaction_speed = Column(Float)
    transaction_speed_deal = Column(Float)
    transaction_value_speed = Column(Float)
    transaction_value_speed_deal = Column(Float)
    transaction_acceleration = Column(Float)
    transaction_acceleration_deal = Column(Float)
    transaction_value_acceleration = Column(Float)
    transaction_value_acceleration_deal = Column(Float)
    buy_count = Column(Float)
    sell_count = Column(Float)
    buy_quantity = Column(Float)
    sell_quantity = Column(Float)
    total_ad = Column(Float)
    pt_only = Column(Float)
    total_over_avg_volume_speed_10d = Column(Float)
    total_under_avg_volume_speed_10d = Column(Float)
    total_equal_avg_volume_speed_10d = Column(Float)

    def __repr__(self):
        return f"<IntradayMarketStatistic(id={self.id}, exchange='{self.exchange}', date='{self.date}')>"