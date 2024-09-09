WITH t1 AS (
    SELECT * 
	FROM calculate_price_changes('HAH')
	limit 20
),
ordered_changes AS (
    SELECT
        output_date,
        percent_change,
        CASE WHEN percent_change > 0 THEN percent_change ELSE NULL END AS positive_percent,
        CASE WHEN percent_change < 0 THEN percent_change ELSE NULL END AS negative_percent
    FROM
        t1 
),
median_positive AS (
    SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY positive_percent) AS median
    FROM
        ordered_changes
    WHERE
        positive_percent IS NOT NULL
),
median_negative AS (
    SELECT
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY negative_percent) AS median
    FROM
        ordered_changes
    WHERE
        negative_percent IS NOT NULL
)
SELECT
    (SELECT median FROM median_positive) AS median_positive,
    (SELECT median FROM median_negative) AS median_negative;
