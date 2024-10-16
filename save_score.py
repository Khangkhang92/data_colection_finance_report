import redis
from common.db import ScopedSession
from models import Score
from base import Base
import json
from loguru import logger
from sqlalchemy.dialects.postgresql import insert

# Initialize Redis client and database
redis_client = redis.Redis(host="127.0.0.1", port=6379, db=1)
base = Base()
all_symbols = base.get_all_symbols()

batch_size = 1000
scores_to_upsert = []



def from_dict(data):
    return {
        "quarter": data.get("Quarter", 0),
        "year": data.get("Year", 0),
        "company_type": data.get("CompanyType", ""),
        "roas_score": data.get("ROAScore", 0),
        "cfo_score": data.get("CFOScore", 0),
        "delta_roas_score": data.get("DeltaROAScore", 0),
        "accrual_score": data.get("AccrualScore", 0),
        "delta_lever_score": data.get("DeltaLeverScore", 0),
        "delta_liquid_score": data.get("DeltaLiquidScore", 0),
        "eq_offer_score": data.get("EQOfferScore", 0),
        "delta_margin_score": data.get("DeltaMarginScore", 0),
        "delta_turn_score": data.get("DeltaTurnScore", 0),
        "piotroski_f_score": data.get("PiotroskiFScore", 0),
        "manufacturing_z_score": data.get("ManufacturingZScore", 0.0),
        "non_manufacturing_z_score": data.get("NonManufacturingZScore", 0.0),
        "manufacturing_status": data.get("ManufacturingStatus", ""),
        "non_manufacturing_status": data.get("NonManufacturingStatus", ""),
        "manufacturing_sp_rating": data.get("ManufacturingSPRating", ""),
        "non_manufacturing_sp_rating": data.get("NonManufacturingSPRating", ""),
        "manufacturing_moody_rating": data.get("ManufacturingMoodyRating", ""),
        "non_manufacturing_moody_rating": data.get("NonManufacturingMoodyRating", ""),
    }


with ScopedSession() as session:
    for symbol in all_symbols:
        list_key = f"{symbol}:year"
        list_items = redis_client.lrange(list_key, 0, -1)

        for item in list_items:
            financial_values = json.loads(item.decode('utf-8')).get("financialValues", {})
            score_dict = from_dict(financial_values)
            score_dict["symbol_ticker"] = symbol
            scores_to_upsert.append(score_dict)

            if len(scores_to_upsert) >= batch_size:
                # Upsert operation using ON CONFLICT
                for batch_score in scores_to_upsert:
                    stmt = insert(Score).values(score_dict)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[ 'year', 'quarter', 'symbol_ticker'],  # Unique constraint columns
                        set_ = {
                            "roas_score": stmt.excluded.roas_score,
                            "cfo_score": stmt.excluded.cfo_score,
                            "delta_roas_score": stmt.excluded.delta_roas_score,
                            "accrual_score": stmt.excluded.accrual_score,
                            "delta_lever_score": stmt.excluded.delta_lever_score,
                            "delta_liquid_score": stmt.excluded.delta_liquid_score,
                            "eq_offer_score": stmt.excluded.eq_offer_score,
                            "delta_margin_score": stmt.excluded.delta_margin_score,
                            "delta_turn_score": stmt.excluded.delta_turn_score,
                            "piotroski_f_score": stmt.excluded.piotroski_f_score,
                            "manufacturing_z_score": stmt.excluded.manufacturing_z_score,
                            "non_manufacturing_z_score": stmt.excluded.non_manufacturing_z_score,
                            "manufacturing_status": stmt.excluded.manufacturing_status,
                            "non_manufacturing_status": stmt.excluded.non_manufacturing_status,
                            "manufacturing_sp_rating": stmt.excluded.manufacturing_sp_rating,
                            "non_manufacturing_sp_rating": stmt.excluded.non_manufacturing_sp_rating,
                            "manufacturing_moody_rating": stmt.excluded.manufacturing_moody_rating,
                            "non_manufacturing_moody_rating": stmt.excluded.non_manufacturing_moody_rating
                        }
                    )
                    session.execute(stmt)
                session.commit()
                scores_to_upsert = []

    # Handle any remaining scores to upsert
    if scores_to_upsert:
        for batch_score in scores_to_upsert:
            score_dict = from_dict(financial_values)
            score_dict["symbol_ticker"] = symbol
            stmt = insert(Score).values(score_dict)
            stmt = stmt.on_conflict_do_update(
                        index_elements=[ 'year', 'quarter', 'symbol_ticker'],  # Unique constraint columns
                        set_ = {
                            "roas_score": stmt.excluded.roas_score,
                            "cfo_score": stmt.excluded.cfo_score,
                            "delta_roas_score": stmt.excluded.delta_roas_score,
                            "accrual_score": stmt.excluded.accrual_score,
                            "delta_lever_score": stmt.excluded.delta_lever_score,
                            "delta_liquid_score": stmt.excluded.delta_liquid_score,
                            "eq_offer_score": stmt.excluded.eq_offer_score,
                            "delta_margin_score": stmt.excluded.delta_margin_score,
                            "delta_turn_score": stmt.excluded.delta_turn_score,
                            "piotroski_f_score": stmt.excluded.piotroski_f_score,
                            "manufacturing_z_score": stmt.excluded.manufacturing_z_score,
                            "non_manufacturing_z_score": stmt.excluded.non_manufacturing_z_score,
                            "manufacturing_status": stmt.excluded.manufacturing_status,
                            "non_manufacturing_status": stmt.excluded.non_manufacturing_status,
                            "manufacturing_sp_rating": stmt.excluded.manufacturing_sp_rating,
                            "non_manufacturing_sp_rating": stmt.excluded.non_manufacturing_sp_rating,
                            "manufacturing_moody_rating": stmt.excluded.manufacturing_moody_rating,
                            "non_manufacturing_moody_rating": stmt.excluded.non_manufacturing_moody_rating
                        }
                    )
            session.execute(stmt)
        session.commit()
