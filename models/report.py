from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from .base import CommonModel


class Report(CommonModel):
    __tablename__ = "finance_report"
    id = Column(Integer, primary_key=True, autoincrement=True)  # Added primary key
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )  # Corrected FK
    parent_id = Column(Integer, ForeignKey("finance_report.id"))  # Self-referential FK
    type = Column(Integer, nullable=False)
    lever = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    display_name = Column(String, nullable=False)

    symbol = relationship("Symbol", back_populates="reports")
    data_entries = relationship("Data", back_populates="report")
    parent = relationship("Report", remote_side=[id], backref="children")

    __table_args__ = (
        CheckConstraint(type.in_([1, 2, 3]), name="check_report_type"),
        UniqueConstraint("name", "symbol_ticker", name="unique_report_name"),
    )


class Data(CommonModel):
    __tablename__ = "data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey("finance_report.id"), nullable=False)
    value = Column(BigInteger, nullable=False)
    quarter = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    report = relationship("Report", back_populates="data_entries")

    __table_args__ = (
        CheckConstraint(quarter.in_([0, 1, 2, 3, 4]), name="check_quarter"),
        UniqueConstraint(
            "report_id", "quarter", "year", name="unique_report_quarter_year"
        ),
    )
