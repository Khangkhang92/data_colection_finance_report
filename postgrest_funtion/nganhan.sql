WITH t1 AS (
    SELECT *
    FROM finance_report fr
    WHERE fr.symbol_ticker = 'HAH'
      AND type = 1
      AND name = 'A. Tài sản lưu động và đầu tư ngắn hạn'
),
t2 AS (
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
    MAX(CASE WHEN name = 'I. Tiền và các khoản tương đương tiền' THEN value END) AS "Tiền & các khoản tương đương tiền",
    MAX(CASE WHEN name = 'II. Các khoản đầu tư tài chính ngắn hạn' THEN value END) AS "Các khoản đầu tư tài chính ngắn hạn",
    MAX(CASE WHEN name = 'III. Các khoản phải thu ngắn hạn' THEN value END) AS "Các khoản phải thu ngắn hạn",
    MAX(CASE WHEN name = 'IV. Tổng hàng tồn kho' THEN value END) AS "Tổng hàng tồn kho",
    MAX(CASE WHEN name = 'V. Tài sản ngắn hạn khác' THEN value END) AS "Tài sản ngắn hạn khác",
    year,
    quarter
FROM
    t2
GROUP BY
    year,
    quarter
ORDER BY
    year,
    quarter;
