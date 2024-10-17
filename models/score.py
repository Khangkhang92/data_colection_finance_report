from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import CommonModel


class Score(CommonModel):
    __tablename__ = "score"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )

    roas_score = Column(Integer)
    cfo_score = Column(Integer)
    delta_roas_score = Column(Integer)
    accrual_score = Column(Integer)
    delta_lever_score = Column(Integer)
    delta_liquid_score = Column(Integer)
    eq_offer_score = Column(Integer)
    delta_margin_score = Column(Integer)
    delta_turn_score = Column(Integer)
    piotroski_f_score = Column(Integer)
    manufacturing_z_score = Column(Float)
    non_manufacturing_z_score = Column(Float)
    manufacturing_status = Column(String)
    non_manufacturing_status = Column(String)
    manufacturing_sp_rating = Column(String)
    non_manufacturing_sp_rating = Column(String)
    manufacturing_moody_rating = Column(String)
    non_manufacturing_moody_rating = Column(String)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    company_type = Column(String, nullable=False)

    symbol = relationship("Symbol", back_populates="score")

    __table_args__ = (
        UniqueConstraint(
            "symbol_ticker", "quarter", "year", name="unique_score_quarter_year"
        ),
    )

    @classmethod
    def from_dict(cls, data):
        return cls(
            quarter=data.get("Quarter", 0),
            year=data.get("Year", 0),
            company_type=data.get("CompanyType", ""),
            roas_score=data.get("ROAScore", 0),
            cfo_score=data.get("CFOScore", 0),
            delta_roas_score=data.get("DeltaROAScore", 0),
            accrual_score=data.get("AccrualScore", 0),
            delta_lever_score=data.get("DeltaLeverScore", 0),
            delta_liquid_score=data.get("DeltaLiquidScore", 0),
            eq_offer_score=data.get("EQOfferScore", 0),
            delta_margin_score=data.get("DeltaMarginScore", 0),
            delta_turn_score=data.get("DeltaTurnScore", 0),
            piotroski_f_score=data.get("PiotroskiFScore", 0),
            manufacturing_z_score=data.get("ManufacturingZScore", 0.0),
            non_manufacturing_z_score=data.get("NonManufacturingZScore", 0.0),
            manufacturing_status=data.get("ManufacturingStatus", ""),
            non_manufacturing_status=data.get("NonManufacturingStatus", ""),
            manufacturing_sp_rating=data.get("ManufacturingSPRating", ""),
            non_manufacturing_sp_rating=data.get("NonManufacturingSPRating", ""),
            manufacturing_moody_rating=data.get("ManufacturingMoodyRating", ""),
            non_manufacturing_moody_rating=data.get("NonManufacturingMoodyRating", ""),
        )
