CREATE OR REPLACE FUNCTION get_dept_ratio_by_symbol(symbol VARCHAR,quarter_mode BOOLEAN)
RETURNS TABLE (
    symbol_ticker VARCHAR,
    "Nợ dài hạn" BIGINT,
    "Nợ ngắn hạn" BIGINT,
    quarter INT,
    year INT,
    timeline TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fr.symbol_ticker,
        MAX(CASE WHEN fr.name = 'II. Nợ dài hạn' THEN d.value ELSE NULL END) AS "Nợ dài hạn",
        MAX(CASE WHEN fr.name = 'I. Nợ ngắn hạn' THEN d.value ELSE NULL END) AS "Nợ ngắn hạn",
        d.quarter,
        d.year,
        CASE
            WHEN quarter_mode = TRUE THEN CONCAT('Q', d.quarter, ' ', d.year)
            ELSE CONCAT(d.year)
        END AS timeline
    FROM
        finance_report fr
    JOIN
        data d ON fr.id = d.report_id
    WHERE
        fr.symbol_ticker = symbol
        AND fr.name IN ('I. Nợ ngắn hạn', 'II. Nợ dài hạn')
        AND (
            (quarter_mode = FALSE AND d.quarter = 0)
            OR (quarter_mode = TRUE AND d.quarter != 0)
        )
    GROUP BY
        fr.symbol_ticker,
        d.quarter,
        d.year
    ORDER BY
        d.year ASC,
        d.quarter ASC;
END;
$$ LANGUAGE plpgsql;


select * from get_dept_ratio_by_symbol('KDH',TRUE);
