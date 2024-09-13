WITH date_series AS (
  SELECT DISTINCT date
  FROM history_data_processing 
  ORDER BY date
),
bull_streaks AS (
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
  FROM history_data_processing where  symbol_ticker = 'HAH' order by  date desc limit 21
),

numbered_streaks AS (
  SELECT 
    *,
    SUM(streak_start) OVER (PARTITION BY symbol_ticker ORDER BY date) AS streak_group
  FROM bull_streaks
)

select * from numbered_streaks   order by  date desc




WITH OrderedData AS (
    SELECT
        date,
        value,
        ROW_NUMBER() OVER (ORDER BY date) AS row_num
    FROM data_table
)


SELECT
        *
FROM OrderedData d1
LEFT JOIN OrderedData d2
ON d2.date BETWEEN d1.date - INTERVAL '3 days' AND d1.date - INTERVAL '1 day'
GROUP BY d1.date, d1.value


WindowSums AS (
    SELECT
        d1.date,
        d1.value,
        SUM(d2.value) AS sum_previous_3_days
    FROM OrderedData d1
    LEFT JOIN OrderedData d2
    ON d2.date BETWEEN d1.date - INTERVAL '3 days' AND d1.date - INTERVAL '1 day'
    GROUP BY d1.date, d1.value
)
SELECT
    date,
    value,
    sum_previous_3_days
FROM WindowSums
ORDER BY date;




WITH OrderedData AS (
    SELECT
        date,
        value,
        ROW_NUMBER() OVER (ORDER BY date) AS row_num
    FROM data_table
),
WindowSums AS (
    SELECT
        date,
        value,
        CASE
            WHEN COUNT(*) OVER (
                ORDER BY date
                ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
            ) = 3 THEN
                SUM(value) OVER (
                    ORDER BY date
                    ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
                )
            ELSE NULL
        END AS sum_previous_3_days
    FROM OrderedData
)
SELECT
    date,
    value,
    sum_previous_3_days
FROM WindowSums
ORDER BY date;

--https://www.timescale.com/learn/postgresql-window-functions -- learn more about window functions