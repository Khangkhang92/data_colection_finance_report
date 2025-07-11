{{ config(materialized='materialized_view') }}

WITH adjusted_market_caps AS (
    SELECT
        s.ticker,
        t.type,
        CASE
            WHEN s.exchange = 'UPCOM' THEN hp.price_average * t.hs * m.free_shares
            ELSE hp.price_close * t.hs * m.free_shares
        END AS adj_market_cap,
        hp.date
    FROM
        {{ source('public', 'history_price') }} hp
    JOIN {{ source('public', 'market') }} m 
        ON m.symbol_ticker = hp.symbol_ticker
    JOIN {{ source('public', 'symbol') }} s 
        ON s.ticker = hp.symbol_ticker
    JOIN {{ source('public', 'temp') }} t 
        ON t.ticker = hp.symbol_ticker
    WHERE
        hp.date > '2025-04-09'
),

daily_totals AS (
    SELECT
        type,
        date,
        SUM(adj_market_cap) AS total_market_cap
    FROM
        adjusted_market_caps
    GROUP BY
        type,
        date
),

type_analysis AS (
    SELECT
        dt.type,
        dt.date,
        dt.total_market_cap,
        LAG(dt.total_market_cap, 1) OVER (PARTITION BY dt.type ORDER BY dt.date) AS prev_day_market_cap,
        FIRST_VALUE(dt.total_market_cap) OVER (
            PARTITION BY dt.type
            ORDER BY dt.date ASC
        ) AS base_cap,
        (dt.total_market_cap - LAG(dt.total_market_cap, 1) OVER (PARTITION BY dt.type ORDER BY dt.date)) / 
        NULLIF(LAG(dt.total_market_cap, 1) OVER (PARTITION BY dt.type ORDER BY dt.date), 0) * 100 AS market_change
    FROM
        daily_totals dt
),

vni_analysis AS (
    SELECT
        hp.symbol_ticker,
        hp.date,
        hp.price_close,
        LAG(hp.price_close, 1) OVER (ORDER BY hp.date) AS prev_vni,
        FIRST_VALUE(hp.price_close) OVER (
            PARTITION BY hp.symbol_ticker
            ORDER BY hp.date ASC
        ) AS base_price,
        (hp.price_close - LAG(hp.price_close, 1) OVER (ORDER BY hp.date)) / 
        NULLIF(LAG(hp.price_close, 1) OVER (ORDER BY hp.date), 0) * 100 AS vni_change
    FROM
        {{ source('public', 'history_price') }} hp
    WHERE
        hp.symbol_ticker = 'VNINDEX'
        AND hp.date > '2025-04-09'
),

merged_data AS (
    SELECT
        type,
        market_change,
        date,
        total_market_cap,
        prev_day_market_cap,
        base_cap
    FROM
        type_analysis
    WHERE
        date IS NOT NULL
    
    UNION ALL
    
    SELECT
        symbol_ticker AS type,
        vni_change AS market_change,
        date,
        NULL AS total_market_cap,
        prev_vni AS prev_day_market_cap,
        base_price AS base_cap
    FROM
        vni_analysis
    WHERE
        date IS NOT NULL
)

SELECT
    date,
    type,
    market_change,
    RANK() OVER (PARTITION BY date ORDER BY market_change DESC) AS daily_rank,
    total_market_cap,
    prev_day_market_cap,
    base_cap,
    CASE 
        WHEN base_cap IS NOT NULL AND base_cap <> 0 THEN total_market_cap / base_cap 
        ELSE NULL 
    END AS index_vs_base
FROM
    merged_data
ORDER BY
    date DESC,
    daily_rank






-- CREATE MATERIALIZED VIEW vonhoa_thaydoi AS
-- WITH adjusted_market_caps AS (
--     SELECT
--         s.ticker,
--         t.type,
--         CASE
--             WHEN s.exchange = 'UPCOM' THEN hp.price_average * t.hs * m.free_shares
--             ELSE hp.price_close * t.hs * m.free_shares
--         END AS adj_market_cap,
--         hp.date
--     FROM
--         history_price hp
--     JOIN market m ON
--         m.symbol_ticker = hp.symbol_ticker
--     JOIN symbol s ON
--         s.ticker = hp.symbol_ticker
--     JOIN temp t ON
--         t.ticker = hp.symbol_ticker
--     WHERE
--         hp.date > '2025-04-09'
-- ),

-- daily_totals AS (
--     SELECT
--         type,
--         date,
--         SUM(adj_market_cap) AS total_market_cap
--     FROM
--         adjusted_market_caps
--     GROUP BY
--         type,
--         date
-- ),

-- type_analysis AS (
--     SELECT
--         dt.type,
--         dt.date,
--         dt.total_market_cap,
--         LAG(dt.total_market_cap, 1) OVER (PARTITION BY dt.type ORDER BY dt.date) AS prev_day_market_cap,
--         FIRST_VALUE(dt.total_market_cap) OVER (
--             PARTITION BY dt.type
--             ORDER BY dt.date ASC
--         ) AS base_cap,
--         (dt.total_market_cap - LAG(dt.total_market_cap, 1) OVER (PARTITION BY dt.type ORDER BY dt.date)) / 
--         LAG(dt.total_market_cap, 1) OVER (PARTITION BY dt.type ORDER BY dt.date) * 100 AS market_change
--     FROM
--         daily_totals dt
-- ),

-- vni_analysis AS (
--     SELECT
--         hp.symbol_ticker,
--         hp.date,
--         hp.price_close,
--         LAG(hp.price_close, 1) OVER (ORDER BY hp.date) AS prev_vni,
--         FIRST_VALUE(hp.price_close) OVER (
--             PARTITION BY hp.symbol_ticker
--             ORDER BY hp.date ASC
--         ) AS base_price,
--         (hp.price_close - LAG(hp.price_close, 1) OVER (ORDER BY hp.date)) / 
--         LAG(hp.price_close, 1) OVER (ORDER BY hp.date) * 100 AS vni_change
--     FROM
--         history_price hp
--     WHERE
--         hp.symbol_ticker = 'VNINDEX'
--         AND hp.date > '2025-04-09'
-- ),

-- merged_data AS (
--     SELECT
--         type,
--         market_change,
--         date,
--         total_market_cap,
--         prev_day_market_cap,
--         base_cap
--     FROM
--         type_analysis
--     WHERE
--         date IS NOT NULL
    
--     UNION ALL
    
--     SELECT
--         symbol_ticker AS type,
--         vni_change AS market_change,
--         date,
--         NULL AS total_market_cap,
--         prev_vni AS prev_day_market_cap,
--         base_price AS base_cap
--     FROM
--         vni_analysis
--     WHERE
--         date IS NOT NULL
-- )

-- SELECT
--     date,
--     type,
--     market_change,
--     RANK() OVER (PARTITION BY date ORDER BY market_change DESC) AS daily_rank,
--     total_market_cap,
--     prev_day_market_cap,
--     base_cap,
--     (total_market_cap / base_cap) AS index_vs_base
-- FROM
--     merged_data
-- ORDER BY
--     date DESC,
--     daily_rank
-- WITH DATA;

-- -- Create indexes for better performance
-- CREATE INDEX idx_market_analysis_date ON vonhoa_thaydoi(date);
-- CREATE INDEX idx_market_analysis_type ON vonhoa_thaydoi(type);
-- CREATE INDEX idx_market_analysis_rank ON vonhoa_thaydoi(daily_rank);