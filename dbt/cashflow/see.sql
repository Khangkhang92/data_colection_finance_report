SELECT
    nt.date,
    nt.industry,
    nt.daily_rank,
    nt.market_change as industry_index_change,
    nl.positive_percentage,
    nl.negative_percentage,
    nl.zero_percentage,
    nth.day_percent_change,
    nth.avg_day_percent_change AS avg_percent_change,
    nth.rank_day_change,
    nth.rank_avg_day_change AS rank_avg_change,
    nth.phanbo_dongtien
FROM nganh_thay_doi nt
JOIN nganh_lan_toa nl 
    ON nl.industry = nt.industry AND nl.date = nt.date
JOIN nganh_thanh_khoan nth 
    ON nth.industry = nt.industry AND nth.date = nt.date
where  nt.date = '2025-07-10'

-- dbt run // run model to creater meterialview
-- dbt run-operation run_all // run  models
