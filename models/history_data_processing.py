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

class HistoryDataProcessing(CommonModel):
    __tablename__ = "history_data_processing"

    id = Column(Integer, primary_key=True)
    symbol_ticker = Column(
        String(length=15), ForeignKey("symbol.ticker"), nullable=False
    )
    percent_change = Column(Float)
    max_bull_20  = Column(Integer) # --> số phiên tăng liên tục 20 phiên trước 
    max_bear_20 = Column(Integer) # --> số phiên giảm liên tục 20 phiên trước 
    max_bull_50 = Column(Integer) # --> số phiên tăng liên tục 50 phiên trước   
    max_bear_50 = Column(Integer) # --> số phiên giảm liên tục 50 phiên trước 
    current_position = Column(Integer) # --> vị trí của phiên hiện tại trong dãy số phiên tăng/giảm liên tục 

    median_bull_20  = Column(Float) # --> trung vị (%) của các phiên tăng  trong 20 phiên trước 
    median_bear_20 = Column(Float) # --> trung vị (%) của các phiên giảm  trong 20 phiên trước 
    median_bull_50 = Column(Float) # --> trung vị (%) của các phiên tăng  trong 50 phiên trước 
    median_bear_50 = Column(Float) # --> trung vị (%) của các phiên giảm  trong 50 phiên trước 

    range_demand_support_20 = Column(Float) # --> tỉ lệ % biên độ giao động giữa cao nhất & thấp nhất của  20 phiên trước 
    range_demand_support_50 = Column(Float) # --> tỉ lệ % biên độ giao động giữa cao nhất & thấp nhất của  50 phiên trước 
    range_current_support_20 = Column(Float) # --> tỉ lệ % của phiên cao nhất 20 phiên so với phiên hiện tại   
    range_current_support_50 = Column(Float) # --> tỷ lệ % của phiên cao nhất 50 phiên so với phiên hiện tại    
    range_demand_current_20 = Column(Float) # --> tỷ lệ % của phiên thấp nhất 20 phiên so với phiên hiện tại   
    range_demand_current_50 = Column(Float) #  --> tỷ lệ % của phiên thấp nhất 50 phiên so với phiên hiện tại
    range_current_lastweek_5 = Column(Float) #  --> tỷ lệ % của phiên hiện tại so với phiên tuần trước 
    range_current_lastmonth_20 = Column(Float) #  --> tỷ lệ % của phiên hiện tại so với phiên tháng trước 
    
    date = Column(Date)
    
 
    symbol = relationship("Symbol", back_populates="history_data_processings")

    def __repr__(self):
        return f"<UpdateQuote(symbol='{self.symbol}', date='{self.date}')>"
    

    __table_args__ = (
       UniqueConstraint('symbol_ticker', 'date', name='uq_history_data_processing_symbol_date'),
   )


#=(MAX($I181:$AB181)-MIN($I181:$AB181))/MIN($I181:$AB181)  --> tỉ lệ phần trắm biên độ giao động giữa cao nhất và thấp nhất của  20 phiên trước 

#=($AC181-MIN($I181:$AB181))/MIN($I181:$AB181) --> tỷ lệ phần trăm của phiên hiện tại so với phiên thấp nhất    

#=(MAX($I181:$AB181)-$AC181)/$AC181  --> tỷ lệ phần trăm của phiên cao nhất so với phiên hiện tại   
#=(AC181-X181)/X181 --> tỷ lệ phần trăm của phiên hiện tại so với phiên tuần trước 