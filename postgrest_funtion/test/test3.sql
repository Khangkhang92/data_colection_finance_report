--  this one is the main working
WITH bull_streaks AS (
  SELECT 
    symbol_ticker,
    date,
    percent_change > 0 AS is_bull,
    percent_change > 0 AND LAG(percent_change) OVER (PARTITION BY symbol_ticker ORDER BY date) <= 0 AS streak_start
  FROM history_data_processing 
  WHERE symbol_ticker = 'HAH' 
  ORDER BY date DESC 
  LIMIT 21
),
numbered_streaks AS (
  SELECT 
    *,
    SUM(streak_start::int) OVER (PARTITION BY symbol_ticker ORDER BY date) AS streak_group
  FROM bull_streaks
),
streak_sums AS (
  SELECT
    *,
    CASE
      WHEN is_bull THEN SUM(is_bull::int) OVER (PARTITION BY streak_group ORDER BY date)
      ELSE NULL
    END AS sum_is_bull_each_group
  FROM numbered_streaks
)
SELECT
  symbol_ticker,
  date,
  is_bull,
  sum_is_bull_each_group,
  CASE
    WHEN COUNT(*) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND CURRENT ROW) = 21 
    THEN MAX(sum_is_bull_each_group) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)
  END AS max	
FROM streak_sums
ORDER BY date;

-- this one is feed data for the main one
WITH WindowSums AS (
    SELECT
        date,
        symbol_ticker,
        percent_change,
        CASE
            WHEN COUNT(*) OVER (
                PARTITION BY symbol_ticker
                ORDER BY date
                ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
            ) = 20 THEN
                SUM(percent_change) OVER (
                    PARTITION BY symbol_ticker
                    ORDER BY date
                    ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING
                )
            ELSE NULL
        END AS sum_previous_20_days
    FROM history_data_processing
)
SELECT
    date,
    symbol_ticker,
    percent_change,
    sum_previous_20_days
FROM WindowSums