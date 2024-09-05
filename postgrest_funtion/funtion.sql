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
    WITH t1 AS (
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
    t2 AS (
        SELECT
            t1.output_date,
            t1.price,
            LAG(t1.price) OVER (ORDER BY t1.output_date) AS prev_price,
            CASE
                WHEN LAG(t1.price) OVER (ORDER BY t1.output_date) IS NOT NULL THEN
                    ((t1.price - LAG(t1.price) OVER (ORDER BY t1.output_date)) / LAG(t1.price) OVER (ORDER BY t1.output_date) * 100)::NUMERIC
                ELSE
                    NULL
            END AS percent_change
        FROM t1
    ),
    t3 AS (
        SELECT
            t2.output_date,
            t2.price,
            t2.percent_change,
            CASE
                WHEN t2.percent_change > 0 THEN 1
                WHEN t2.percent_change < 0 THEN -1
                ELSE 0
            END AS change
        FROM t2
    ),
    Transitions AS (
        SELECT
            t3.output_date,
            t3.price,
            t3.percent_change,
            t3.change,
            LAG(t3.change) OVER (ORDER BY t3.output_date) AS prev_change
        FROM t3
    ),
    GroupedChanges AS (
        SELECT
            Transitions.output_date,
            Transitions.price,
            Transitions.percent_change,
            Transitions.change,
            CASE
                WHEN Transitions.change = Transitions.prev_change THEN 0
                ELSE 1
            END AS is_change
        FROM Transitions
    ),
    FinalGroups AS (
        SELECT
            GroupedChanges.output_date,
            GroupedChanges.price,
            GroupedChanges.percent_change,
            GroupedChanges.change,
            SUM(GroupedChanges.is_change) OVER (ORDER BY GroupedChanges.output_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS group_id
        FROM GroupedChanges
    ),
    SummedChanges AS (
        SELECT
            FinalGroups.output_date,
            FinalGroups.price,
            FinalGroups.percent_change,
            FinalGroups.change,
            SUM(FinalGroups.change) OVER (PARTITION BY FinalGroups.group_id ORDER BY FinalGroups.output_date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ps
        FROM FinalGroups
    )
    SELECT
        SummedChanges.output_date AS date,
        SummedChanges.price::NUMERIC,
        SummedChanges.percent_change::NUMERIC,
        SummedChanges.ps::NUMERIC,
        MAX(SummedChanges.ps) OVER (ORDER BY SummedChanges.output_date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)::NUMERIC AS max_increase,
        MIN(SummedChanges.ps) OVER (ORDER BY SummedChanges.output_date ROWS BETWEEN 20 PRECEDING AND 1 PRECEDING)::NUMERIC AS max_drop
    FROM SummedChanges
    ORDER BY SummedChanges.output_date DESC;
END;
$$ LANGUAGE plpgsql;
