{% macro step1_position() %}
{{ return(run_query("
WITH PriceData AS (
    SELECT
        hp.date,
        hp.symbol_ticker,
        -- Determine the price (average or close) once based on the exchange type
        CASE 
            WHEN s.exchange = 'UPCOM' THEN hp.price_average
            ELSE hp.price_close
        END AS price,
        -- Use LAG to get the previous price in the same step
        LAG(
            CASE 
                WHEN s.exchange = 'UPCOM' THEN hp.price_average
                ELSE hp.price_close
            END
        ) OVER (PARTITION by symbol_ticker ORDER BY  date) AS previous_price,
        ROW_NUMBER() OVER (PARTITION BY hp.symbol_ticker ORDER BY hp.date DESC) AS rn
        
    FROM
        history_price hp
    JOIN symbol s ON s.ticker = hp.symbol_ticker
    order by symbol_ticker asc , date desc  
),
PriceChanges AS (
    SELECT
        date,
        symbol_ticker,
        price,
        previous_price,
        -- Calculate percentage change only once
        CASE 
            WHEN previous_price IS NOT NULL THEN
                (price - previous_price) / previous_price 
            ELSE NULL
        END AS percent_change
    FROM
        PriceData
    WHERE
    rn <= 25  -- Filter for the top 10 records per symbol    
        
     order by symbol_ticker asc , date desc    
),
ChangeSigns AS (
    SELECT
        date,
        symbol_ticker,
        price,
        previous_price,
        percent_change,
        -- Calculate the change sign directly here
        CASE
            WHEN percent_change > 0 THEN 1
            WHEN percent_change < 0 THEN -1
            ELSE 0
        END AS change_sign
    FROM
        PriceChanges
    order by symbol_ticker asc , date desc    
),
ChangeGroups AS (
    SELECT
        date,
        symbol_ticker,
        price,
        previous_price,
        percent_change,
        change_sign,
        -- Mark the start of a new group based on change_sign change
        CASE
            WHEN change_sign != LAG(change_sign) OVER (ORDER BY symbol_ticker asc , date) THEN 1
            ELSE 0
        END AS new_group_flag
    FROM
        ChangeSigns
    order by symbol_ticker asc , date desc    
),
GroupedChanges AS (
    SELECT
        date,
        symbol_ticker,
        price,
        previous_price,
        percent_change,
        change_sign,
        -- Group consecutive days with the same change_sign
        SUM(new_group_flag) OVER (ORDER BY symbol_ticker asc , date) AS group_id
    FROM
        ChangeGroups
    order by symbol_ticker asc , date desc      
),
CumulativeSums AS (
    SELECT
        date,
        symbol_ticker,
        price,
        previous_price,
        percent_change,
        change_sign,
        group_id,
        -- Calculate the cumulative sum within each group directly
        SUM(change_sign) OVER (PARTITION BY group_id ORDER BY symbol_ticker asc , date) AS cumulative_sum
    FROM
        GroupedChanges
    order by symbol_ticker asc , date desc      
),
result as  (SELECT
    date,
    symbol_ticker,
    price,
    previous_price,
    percent_change,
    cumulative_sum
from CumulativeSums
order by symbol_ticker asc , date desc      
)


INSERT INTO history_data_processing (symbol_ticker, percent_change, current_position, date)
SELECT
    symbol_ticker,
    percent_change,
    cumulative_sum AS current_position,
    date
FROM result
ON CONFLICT (symbol_ticker, date)
DO UPDATE
SET
    percent_change = EXCLUDED.percent_change,
    current_position = EXCLUDED.current_position;")) }}

{% endmacro %}    