from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from .base import CommonModel


class UpdateMarket(CommonModel):
    __tablename__ = "update_market"

    id = Column(Integer, primary_key=True)
    exchange = Column(String, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String)
    total_value = Column(Float)
    total_volume = Column(Float)
    index_current = Column(Float)
    index_basic = Column(Float)
    pt_volume = Column(Float)
    pt_value = Column(Float)
    buy_foreign_quantity = Column(Float)
    sell_foreign_quantity = Column(Float)
    buy_foreign_value = Column(Float)
    sell_foreign_value = Column(Float)
    advances = Column(Integer)
    declines = Column(Integer)
    unchange = Column(Integer)
    advances_value = Column(Float)
    declines_value = Column(Float)
    unchange_value = Column(Float)
    current_foreign_room = Column(Float)

    def __repr__(self):
        return f"<UpdateMarket(exchange='{self.exchange}', date='{self.date}')>"
