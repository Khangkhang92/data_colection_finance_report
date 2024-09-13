--https://www.timescale.com/learn/postgresql-window-functions


CREATE OR REPLACE FUNCTION calculate_price_changes(p_symbol_ticker TEXT)
RETURNS TABLE (
    output_date DATE,
    price NUMERIC,
    percent_change NUMERIC,
    ps NUMERIC,
    max_increase NUMERIC,
    max_drop NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH price_data AS (
        SELECT
            m.date AS output_date,
            CASE
                WHEN s.exchange = 'UPCOM' THEN m.average::NUMERIC
                ELSE m.close::NUMERIC
            END AS price
        FROM market m
        JOIN symbol s ON m.symbol_ticker = s.ticker
        WHERE m.symbol_ticker = p_symbol_ticker
    ),
    changes AS (
        SELECT
            output_date,
            price,
            (price - LAG(price) OVER (ORDER BY output_date)) / NULLIF(LAG(price) OVER (ORDER BY output_date), 0) * 100 AS percent_change,
            SIGN(price - LAG(price) OVER (ORDER BY output_date)) AS change
        FROM price_data
    ),
    grouped_changes AS (
        SELECT
            output_date,
            price,
            percent_change,
            SUM(CASE WHEN change != LAG(change) OVER (ORDER BY output_date) OR LAG(change) OVER (ORDER BY output_date) IS NULL THEN 1 ELSE 0 END) OVER (ORDER BY output_date) AS group_id
        FROM changes
    ),
    summed_changes AS (
        SELECT
            output_date,
            price,
            percent_change,
            SUM(change) OVER (PARTITION BY group_id ORDER BY output_date) AS ps
        FROM grouped_changes
    )
    SELECT
        output_date,
        price,
        COALESCE(percent_change, 0)::NUMERIC,
        ps::NUMERIC,
        COALESCE(MAX(ps) OVER (ORDER BY output_date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING), 0)::NUMERIC AS max_increase,
        COALESCE(MIN(ps) OVER (ORDER BY output_date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING), 0)::NUMERIC AS max_drop
    FROM summed_changes
    ORDER BY output_date DESC;
END;
$$ LANGUAGE plpgsql;
