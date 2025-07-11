{{ config(
    materialized='materialized_view',
    alias='nganh_thanh_khoan',
    post_hook=[
        "CREATE INDEX IF NOT EXISTS idx_nganhthanhkhoan_date ON {{ this }}(date)",
        "CREATE INDEX IF NOT EXISTS idx_nganhthanhkhoan_industry ON {{ this }}(industry)",
        "CREATE INDEX IF NOT EXISTS idx_nganhthanhkhoan_rank_day ON {{ this }}(rank_day_change)"
    ]
) }}

WITH volume_by_industry AS (
    SELECT 
        t.industry,
        hp.date,
        SUM(hp.total_value) AS total_value
    FROM {{ source('public', 'history_price') }} hp
    JOIN {{ source('public', 'temp') }} t 
        ON hp.symbol_ticker = t.ticker
    GROUP BY t.industry, hp.date
),

base_with_lag AS (
    SELECT 
        *,
        AVG(total_value) OVER (
            PARTITION BY industry 
            ORDER BY date 
            ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
        ) AS avg_20_prev_volume,
        LAG(total_value) OVER (
            PARTITION BY industry 
            ORDER BY date
        ) AS previous_volume
    FROM volume_by_industry
),

base_with_change AS (
    SELECT 
        *,
        (total_value - previous_volume) * 100.0 / NULLIF(previous_volume, 0) AS day_percent_change,
        (total_value - avg_20_prev_volume) * 100.0 / NULLIF(avg_20_prev_volume, 0) AS avg_day_percent_change
    FROM base_with_lag
),

nganh AS (
    SELECT 
        *,
        RANK() OVER (PARTITION BY date ORDER BY day_percent_change DESC) AS rank_day_change,
        RANK() OVER (PARTITION BY date ORDER BY avg_day_percent_change DESC) AS rank_avg_day_change
    FROM base_with_change
),

vni AS (
    SELECT 
        date,
        total_value AS vni_value
    FROM {{ source('public', 'history_price') }}
    WHERE symbol_ticker = 'VNINDEX'
)

SELECT  
    n.*,
    ROUND(n.total_value * 100.0 / NULLIF(vni.vni_value, 0), 2) AS phanbo_dongtien
FROM nganh n 
JOIN vni ON n.date = vni.date
ORDER BY n.date DESC, rank_day_change




-- CREATE MATERIALIZED VIEW nganh_thanhkhoan AS
-- WITH volume_by_industry AS (
--     SELECT 
--         t.industry,
--         hp.date,
--         SUM(hp.total_value) AS total_value
--     FROM history_price hp
--     JOIN temp t ON hp.symbol_ticker = t.ticker
--     GROUP BY t.industry, hp.date
-- ),
-- base_with_lag AS (
--     SELECT 
--         *,
--         AVG(total_value) OVER (
--             PARTITION BY industry 
--             ORDER BY date 
--             ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
--         ) AS avg_20_prev_volume,
--         LAG(total_value) OVER (
--             PARTITION BY industry 
--             ORDER BY date 
--         ) AS previous_volume
--     FROM volume_by_industry
-- ),
-- base_with_change AS (
--     SELECT 
--         *,
--         (total_value - previous_volume) * 100.0 / NULLIF(previous_volume, 0) AS day_percent_change,
--         (total_value - avg_20_prev_volume) * 100.0 / NULLIF(avg_20_prev_volume, 0) AS avg_day_percent_change
--     FROM base_with_lag
-- ),
-- nganh AS (
--     SELECT 
--         *,
--         RANK() OVER (PARTITION BY date ORDER BY day_percent_change DESC) AS rank_day_change,
--         RANK() OVER (PARTITION BY date ORDER BY avg_day_percent_change DESC) AS rank_avg_day_change
--     FROM base_with_change
-- ),
-- vni AS (
--     SELECT 
--         total_value AS vni_value,
--         date
--     FROM history_price
--     WHERE symbol_ticker = 'VNINDEX'
-- )
-- SELECT  
--     n.*,
--     ROUND((n.total_value * 100.0 / NULLIF(vni_value, 0)), 2) AS phanbo_dongtien
-- FROM nganh n 
-- JOIN vni ON vni.date = n.date
-- ORDER BY n.date DESC, rank_day_change;
