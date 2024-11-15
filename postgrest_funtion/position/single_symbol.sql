WITH PriceData AS (
    SELECT
        hp.date,
        CASE 
            WHEN s.exchange = 'UPCOM' THEN hp.price_average
            ELSE hp.price_close
        END AS price,
        LAG(
            CASE 
                WHEN s.exchange = 'UPCOM' THEN hp.price_average
                ELSE hp.price_close
            END
        ) OVER (ORDER BY hp.date) AS previous_price
    FROM
        history_price hp
    JOIN symbol s ON s.ticker = hp.symbol_ticker
    WHERE
        hp.symbol_ticker = 'VCI'
),
PriceChanges AS (
    SELECT
        date,
        price,
        previous_price,
        -- Calculate percentage change
        CASE 
            WHEN previous_price IS NOT NULL THEN
                (price - previous_price) / previous_price * 100
            ELSE NULL
        END AS percent_change
    FROM
        PriceData
),
ChangeSigns AS (
    SELECT
        date,
        price,
        previous_price,
        percent_change,
        -- Assign 1 for positive changes and -1 for negative changes
        CASE
            WHEN percent_change > 0 THEN 1
            WHEN percent_change < 0 THEN -1
            ELSE 0 -- In case of no valid percent change (shouldn't happen with valid data)
        END AS change_sign
    FROM
        PriceChanges
),
ChangeGroups AS (
    SELECT
        date,
        price,
        previous_price,
        percent_change,
        change_sign,
        -- Create a flag to indicate the start of a new group
        CASE
            WHEN change_sign != LAG(change_sign) OVER (ORDER BY date) THEN 1
            ELSE 0
        END AS new_group_flag
        
    FROM
        ChangeSigns
),

GroupedChanges AS (
    SELECT
        date,
         price,
	    previous_price,
	    percent_change,
        change_sign,
        -- Group consecutive days with the same change_sign
        SUM(new_group_flag) OVER (ORDER BY date) AS group_id
    FROM
        ChangeGroups
),
CumulativeSums AS (
    SELECT
        date,
         price,
	    previous_price,
	    percent_change,
        change_sign,
        group_id,
        -- Cumulative sum of change_sign within each group, starting from the first date in the group
        SUM(change_sign) OVER (PARTITION BY group_id ORDER BY date) AS cumulative_sum
    FROM
        GroupedChanges
)
SELECT
    date,
     price,
    previous_price,
    percent_change,
--    group_id,
    cumulative_sum
FROM
    CumulativeSums
ORDER BY
    date DESC;



    


