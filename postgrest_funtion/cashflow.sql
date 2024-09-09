WITH cashflow_data AS (
    SELECT
        fr.symbol_ticker,
        fr.name,
        d.value,
        d.quarter,
        d.year
    FROM
        finance_report fr
    JOIN data d ON fr.id = d.report_id
    WHERE
        fr.name IN (
            'Tiền và tương đương tiền đầu kỳ',
            'Tiền và tương đương tiền cuối kỳ',
            'Lưu chuyển tiền thuần từ hoạt động kinh doanh',
            'Lưu chuyển tiền thuần từ hoạt động đầu tư',
            'Lưu chuyển tiền thuần từ hoạt động tài chính',
            'Lưu chuyển tiền từ hoạt động tài chính',
            'Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ',
            'Lưu chuyển tiền thuần trong kỳ',
            'IV. Tăng/giảm tiền thuần trong kỳ'
        )
        AND d.quarter = 0
        AND fr.symbol_ticker = UPPER('MSH')
)
SELECT
    MAX(CASE WHEN name = 'Lưu chuyển tiền thuần từ hoạt động kinh doanh' THEN value END) AS "Dòng tiền từ kinh doanh",
    MAX(CASE WHEN name = 'Lưu chuyển tiền thuần từ hoạt động đầu tư' THEN value END) AS "Dòng tiền từ đầu tư",
    MAX(CASE WHEN name IN ('Lưu chuyển tiền thuần từ hoạt động tài chính', 'Lưu chuyển tiền từ hoạt động tài chính') THEN value END) AS "Dòng tiền từ tài chính",
    MAX(CASE WHEN name IN ('Lưu chuyển tiền thuần trong kỳ', 'IV. Tăng/giảm tiền thuần trong kỳ') THEN value END) AS "Dòng tiền thuần trong kỳ",
    MAX(CASE WHEN name IN ('Tiền và tương đương tiền đầu kỳ', 'V. Tiền và các khoản tương đương tiền đầu kỳ') THEN value END) AS "Tiền đầu kỳ",
    MAX(CASE WHEN name IN ('Tiền và tương đương tiền cuối kỳ', 'VI. Tiền và các khoản tương đương tiền cuối kỳ') THEN value END) AS "Tiền cuối kỳ",
    MAX(CASE WHEN name = 'Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ' THEN value END) AS "Ảnh hưởng bởi tỷ giá",
    
    year,
    quarter
FROM
    cashflow_data
GROUP BY
    year,
    quarter
ORDER BY
    year,
    quarter;




    

-----------------------------------------------------------funtion----------------------------------------------------------




CREATE OR REPLACE FUNCTION get_cashflow(symbol TEXT, mode TEXT)
RETURNS TABLE (
    "Dòng tiền từ kinh doanh" NUMERIC,
    "Dòng tiền từ đầu tư" NUMERIC,
    "Dòng tiền từ tài chính" NUMERIC,
    "Dòng tiền thuần trong kỳ" NUMERIC,
    "Tiền đầu kỳ" NUMERIC,
    "Tiền cuối kỳ" NUMERIC,
    "Ảnh hưởng bởi tỷ giá" NUMERIC,
    "Time" TEXT
) AS $$
DECLARE
    quarter_condition TEXT;
    time_column TEXT;
BEGIN
    IF mode = 'year' THEN
        quarter_condition := 'quarter = 0';
        time_column := 'year::TEXT';
    ELSIF mode = 'quarter' THEN
        quarter_condition := 'quarter != 0';
        time_column := 'CASE WHEN quarter = 0 THEN year::TEXT ELSE ''Q'' || quarter::TEXT || '' '' || year::TEXT END';
    ELSE
        RAISE EXCEPTION 'Invalid mode. Use ''year'' or ''quarter''.';
    END IF;

    RETURN QUERY EXECUTE format('
    WITH cashflow_data AS (
        SELECT
            fr.symbol_ticker,
            fr.name,
            d.value,
            d.quarter,
            d.year
        FROM
            finance_report fr
        JOIN data d ON fr.id = d.report_id
        WHERE
            fr.name IN (
                ''Tiền và tương đương tiền đầu kỳ'',
                ''Tiền và tương đương tiền cuối kỳ'',
                ''Lưu chuyển tiền thuần từ hoạt động kinh doanh'',
                ''Lưu chuyển tiền thuần từ hoạt động đầu tư'',
                ''Lưu chuyển tiền thuần từ hoạt động tài chính'',
                ''Lưu chuyển tiền từ hoạt động tài chính'',
                ''Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ'',
                ''Lưu chuyển tiền thuần trong kỳ'',
                ''IV. Tăng/giảm tiền thuần trong kỳ''
            )
            AND %s
            AND fr.symbol_ticker = UPPER($1)
    )
    SELECT
        MAX(CASE WHEN name = ''Lưu chuyển tiền thuần từ hoạt động kinh doanh'' THEN value END)::NUMERIC AS "Dòng tiền từ kinh doanh",
        MAX(CASE WHEN name = ''Lưu chuyển tiền thuần từ hoạt động đầu tư'' THEN value END)::NUMERIC AS "Dòng tiền từ đầu tư",
        MAX(CASE WHEN name IN (''Lưu chuyển tiền thuần từ hoạt động tài chính'', ''Lưu chuyển tiền từ hoạt động tài chính'') THEN value END)::NUMERIC AS "Dòng tiền từ tài chính",
        MAX(CASE WHEN name IN (''Lưu chuyển tiền thuần trong kỳ'', ''IV. Tăng/giảm tiền thuần trong kỳ'') THEN value END)::NUMERIC AS "Dòng tiền thuần trong kỳ",
        MAX(CASE WHEN name IN (''Tiền và tương đương tiền đầu kỳ'', ''V. Tiền và các khoản tương đương tiền đầu kỳ'') THEN value END)::NUMERIC AS "Tiền đầu kỳ",
        MAX(CASE WHEN name IN (''Tiền và tương đương tiền cuối kỳ'', ''VI. Tiền và các khoản tương đương tiền cuối kỳ'') THEN value END)::NUMERIC AS "Tiền cuối kỳ",
        MAX(CASE WHEN name = ''Ảnh hưởng của thay đổi tỷ giá hối đoái quy đổi ngoại tệ'' THEN value END)::NUMERIC AS "Ảnh hưởng bởi tỷ giá",
        %s AS "Time"
    FROM
        cashflow_data
    GROUP BY
        year, quarter
    ORDER BY
        year, quarter;
    ', quarter_condition, time_column) USING symbol;
END;
$$ LANGUAGE plpgsql;