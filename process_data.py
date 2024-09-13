from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.history_data_processing import HistoryDataProcessing
from common.db import ScopedSession  # Using the existing import
from dotenv import load_dotenv
import os
import copy

# Load environment variables
load_dotenv()



def get_db():
    return ScopedSession()

def get_history_data_by_symbol(db: ScopedSession, symbol_ticker: str):
    try:
        query = select(HistoryDataProcessing).where(HistoryDataProcessing.symbol_ticker == symbol_ticker).order_by(HistoryDataProcessing.date.asc())
        return db.execute(query).scalars().all()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        return None

def main():

    
    with get_db() as db:
        all_data = get_history_data_by_symbol(db, 'HAH')
        

        current_position = 0
        for idx, data in enumerate(all_data):
            # data.max_bull_20 = None
            # data.max_bear_20 = None
            # data.current_position = None


            # Deep copy next 20 items not including current item
            next_20 = copy.deepcopy(all_data[idx-21:idx-1])
            print(idx,idx-21,idx-1)
    


            current_change = data.percent_change
            previous_change = all_data[idx-1].percent_change

            
            if current_change is None or previous_change is None:
                continue

            if current_change > 0:
                current_position = 1 if previous_change < 0 else current_position + 1
            elif current_change < 0:
                current_position = -1 if previous_change > 0 else current_position - 1
            else:
                current_position = 0
          
            # Break the loop if fewer than 20 items remain
            if len(next_20) < 20:
                continue
           

            # Count continuous positive and negative percent changes
            continuous_positive = 0
            continuous_negative = 0
            max_continuous_positive = 0
            max_continuous_negative = 0
           
            for item in next_20:
                if item.percent_change is not None:
                    if item.percent_change > 0:
                        continuous_positive += 1
                        continuous_negative = 0
                        max_continuous_positive = max(max_continuous_positive, continuous_positive)

                    elif item.percent_change < 0:
                        continuous_negative -= 1
                        continuous_positive = 0
                        max_continuous_negative = min(max_continuous_negative, continuous_negative)
                    else:
                        continuous_positive = 0
                        continuous_negative = 0

            if max_continuous_positive > 0:
                data.max_bull_20 = max_continuous_positive
            if max_continuous_negative < 0:
                data.max_bear_20 = max_continuous_negative
            data.current_position = current_position
            del next_20
            
       
        # Batch update the database
        try:
            db.bulk_save_objects(all_data)
            db.commit()
            print(f"Successfully updated {len(all_data)} records.")
        except SQLAlchemyError as e:
            db.rollback()
            print(f"An error occurred while updating the database: {e}")

if __name__ == "__main__":
    main()