WITH t1 AS (
    SELECT *
    FROM finance_report fr
    WHERE fr.symbol_ticker = 'HAH'
      AND type = 1
      AND name = 'TÀI SẢN'
),
filtered_data AS (
    SELECT
        fr.symbol_ticker,
        fr.name,
        value,
        quarter,
        year
    FROM
        finance_report fr
    JOIN data d ON fr.id = d.report_id
    WHERE
        fr.parent_id = (
            SELECT id FROM t1
        )
        and quarter = 0
)
SELECT
    year,
    quarter,
    MAX(CASE WHEN name = 'A. Tài sản lưu động và đầu tư ngắn hạn' THEN value END) AS "Tài sản ngắn hạn",
    MAX(CASE WHEN name = 'B. Tài sản cố định và đầu tư dài hạn' THEN value END) AS "Tài sản dài hạn"
FROM
    filtered_data
GROUP BY
    year,
    quarter
ORDER BY
    year,
    quarter;
