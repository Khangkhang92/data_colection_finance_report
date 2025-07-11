{{ config(
    materialized='materialized_view',
    alias='nganh_lan_toa'
) }}

SELECT
    t.industry,
    hdp.date,

    -- Raw counts
    COUNT(DISTINCT CASE WHEN hdp.percent_change > 0 THEN hdp.symbol_ticker END) AS positive_count,
    COUNT(DISTINCT CASE WHEN hdp.percent_change < 0 THEN hdp.symbol_ticker END) AS negative_count,
    COUNT(DISTINCT CASE WHEN hdp.percent_change = 0 THEN hdp.symbol_ticker END) AS zero_count,
    COUNT(DISTINCT hdp.symbol_ticker) AS total_count,

    -- Percentage calculations
    ROUND(
        100.0 * 
        COUNT(DISTINCT CASE WHEN hdp.percent_change > 0 THEN hdp.symbol_ticker END) / 
        NULLIF(COUNT(DISTINCT hdp.symbol_ticker), 0), 2) AS positive_percentage,

    ROUND(
        100.0 * 
        COUNT(DISTINCT CASE WHEN hdp.percent_change < 0 THEN hdp.symbol_ticker END) / 
        NULLIF(COUNT(DISTINCT hdp.symbol_ticker), 0), 2) AS negative_percentage,

    ROUND(
        100.0 * 
        COUNT(DISTINCT CASE WHEN hdp.percent_change = 0 THEN hdp.symbol_ticker END) / 
        NULLIF(COUNT(DISTINCT hdp.symbol_ticker), 0), 2) AS zero_percentage

FROM
    {{ source('public', 'history_data_processing') }} hdp
JOIN 
    {{ source('public', 'temp') }} t 
    ON t.ticker = hdp.symbol_ticker
GROUP BY  
    t.industry, hdp.date
ORDER BY 
    hdp.date DESC, t.industry





-- CREATE MATERIALIZED VIEW nganh_lantoa AS
-- SELECT
--     t.industry,
--     hdp.date,
--     -- Raw counts
--     COUNT(DISTINCT CASE WHEN hdp.percent_change > 0 THEN hdp.symbol_ticker END) AS positive_count,
--     COUNT(DISTINCT CASE WHEN hdp.percent_change < 0 THEN hdp.symbol_ticker END) AS negative_count,
--     COUNT(DISTINCT CASE WHEN hdp.percent_change = 0 THEN hdp.symbol_ticker END) AS zero_count,
--     COUNT(DISTINCT hdp.symbol_ticker) AS total_count,
    
--     -- Percentage calculations
--     ROUND(
--         100.0 * 
--         COUNT(DISTINCT CASE WHEN hdp.percent_change > 0 THEN hdp.symbol_ticker END) / 
--         NULLIF(COUNT(DISTINCT hdp.symbol_ticker), 0), 2) AS positive_percentage,
    
--     ROUND(
--         100.0 * 
--         COUNT(DISTINCT CASE WHEN hdp.percent_change < 0 THEN hdp.symbol_ticker END) / 
--         NULLIF(COUNT(DISTINCT hdp.symbol_ticker), 0), 2) AS negative_percentage,
    
--     ROUND(
--         100.0 * 
--         COUNT(DISTINCT CASE WHEN hdp.percent_change = 0 THEN hdp.symbol_ticker END) / 
--         NULLIF(COUNT(DISTINCT hdp.symbol_ticker), 0), 2) AS zero_percentage
    
-- FROM
--     history_data_processing hdp 
-- JOIN 
--     temp t ON t.ticker = hdp.symbol_ticker
-- GROUP BY  
--     t.industry, hdp.date
-- ORDER BY 
--     hdp.date DESC, t.industry
-- WITH DATA;