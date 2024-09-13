WITH bull_streaks AS (
  SELECT 
    symbol_ticker,
    date,
    CASE 
      WHEN percent_change > 0 THEN 1
      ELSE 0
    END AS is_bull,
    CASE 
      WHEN percent_change > 0 AND LAG(percent_change) OVER (PARTITION BY symbol_ticker ORDER BY date) <= 0 THEN 1
      ELSE 0
    END AS streak_start
  FROM history_data_processing 
  WHERE symbol_ticker = 'HAH' 
  ORDER BY date DESC 
  LIMIT 21
),
numbered_streaks AS (
  SELECT 
    *,
    SUM(streak_start) OVER (PARTITION BY symbol_ticker ORDER BY date) AS streak_group
  FROM bull_streaks
),
t3 AS (
  SELECT
    *,
 
     CASE
           WHEN is_bull > 0 THEN
                SUM(is_bull) OVER (PARTITION BY streak_group ORDER BY date) 
            ELSE NULL
     END AS sum_is_bull_each_group
  FROM numbered_streaks
)
SELECT
  symbol_ticker,date,is_bull,sum_is_bull_each_group,
  CASE
    WHEN COUNT(*) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING) = 20 
    THEN MAX(sum_is_bull_each_group) OVER (ORDER BY date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)
    ELSE NULL
  END AS max	
FROM t3
ORDER BY date;