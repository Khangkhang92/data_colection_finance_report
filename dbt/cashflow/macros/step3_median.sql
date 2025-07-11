{% macro step3_median() %}
{{ return(run_query("
WITH windowed_data AS (
  SELECT 
    date,
    symbol_ticker,
    percent_change,
    -- Tạo mảng chứa các giá trị percent_change > 0 trong 20 ngày trước
    array_agg(CASE WHEN percent_change > 0 THEN percent_change ELSE NULL END) 
      OVER (
        PARTITION BY symbol_ticker 
        ORDER BY date ASC 
        ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
      ) AS positive_changes,
    -- Tạo mảng chứa các giá trị percent_change < 0 trong 20 ngày trước
    array_agg(CASE WHEN percent_change < 0 THEN percent_change ELSE NULL END) 
      OVER (
        PARTITION BY symbol_ticker 
        ORDER BY date ASC 
        ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
      ) AS negative_changes,
    row_number() OVER (PARTITION BY symbol_ticker ORDER BY date ASC) AS row_num
  FROM history_data_processing
),
result as (SELECT 
  date,
  symbol_ticker,
  -- Trung vị của các giá trị > 0 trong 20 ngày trước
  CASE 
    WHEN row_num > 20 THEN 
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY val) 
       FROM unnest(positive_changes) AS val 
       WHERE val IS NOT NULL)
    ELSE NULL 
  END AS median_bull_20,
  -- Trung vị của các giá trị < 0 trong 20 ngày trước
  CASE 
    WHEN row_num > 20 THEN 
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY val) 
       FROM unnest(negative_changes) AS val 
       WHERE val IS NOT NULL)
    ELSE NULL 
  END AS median_bear_20
FROM windowed_data 
ORDER BY symbol_ticker ASC, date desc )


INSERT INTO history_data_processing (symbol_ticker, median_bull_20, median_bear_20, date)
SELECT
    symbol_ticker,
    median_bull_20,
    median_bear_20,
    date
FROM result 
ON CONFLICT (symbol_ticker, date)
DO UPDATE
SET
    median_bull_20 = EXCLUDED.median_bull_20,
    median_bear_20 = EXCLUDED.median_bear_20;")) }}
{% endmacro %}   