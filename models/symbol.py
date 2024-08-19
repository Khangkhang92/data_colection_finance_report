from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from .base import CommonModel


class Symbol(CommonModel):
    __tablename__ = "symbol"
    ticker = Column(String(length=15), primary_key=True, nullable=False)
    exchange = Column(String(length=20), nullable=False)
    company_name = Column(String)
    industry = Column(String)
    sector = Column(String)
    reports = relationship("Report", back_populates="symbol")
