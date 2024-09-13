from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    Date,
    Boolean,
)
from sqlalchemy.orm import relationship
from .base import CommonModel


class MajorHolder(CommonModel):
    __tablename__ = "major_holder"

    id = Column(Integer, primary_key=True)
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )
    name = Column(String(255))
    position = Column(String(255))
    shares = Column(Float)
    ownership = Column(Float)
    is_organization = Column(Boolean)
    is_foreigner = Column(Boolean)
    is_foundation = Column(Boolean)
    is_listing = Column(Boolean)
    listing_symbol = Column(String(10))
    reported = Column(Date)

    symbol = relationship("Symbol", back_populates="major_holders")

    def __repr__(self):
        return f"<MajorHolder(symbol='{self.symbol}', name='{self.name}')>"
