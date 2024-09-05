CREATE OR REPLACE FUNCTION generate_dynamic_sql_raw(input_names TEXT, symbol_ticker TEXT, mode TEXT)
RETURNS TEXT AS $$
DECLARE
    sql_raw TEXT;
    case_statements TEXT;
    name TEXT;
    quarter_condition TEXT;
    formatted_names TEXT[];
BEGIN
    -- Determine the condition for quarter based on the mode
    IF mode = 'year' THEN
        quarter_condition := 'd.quarter = 0';
    ELSIF mode = 'quarter' THEN
        quarter_condition := 'd.quarter != 0';
    ELSE
        RAISE EXCEPTION 'Invalid mode. Use ''year'' or ''quarter''.';
    END IF;

    -- Convert tuple-like input to an array
    formatted_names := regexp_split_to_array(
        regexp_replace(input_names, '[()]+', '', 'g'), -- Remove parentheses
        '\s*,\s*' -- Split by commas and optional whitespace
    );

    -- Initialize the base sql_raw
    sql_raw := 'SELECT d.quarter, d.year';

    -- Generate CASE statements for each input name
    FOREACH name IN ARRAY formatted_names
    LOOP
        case_statements := format(
            'MAX(CASE WHEN fr.name = %L THEN d.value ELSE 0 END) AS "%s"',
            name, name
        );
        sql_raw := sql_raw || ', ' || case_statements;
    END LOOP;

    -- Complete the sql_raw
    sql_raw := sql_raw || ' FROM finance_report fr ' ||
             'JOIN data d ON fr.id = d.report_id ' ||
             'WHERE fr.symbol_ticker = ' || quote_literal(symbol_ticker) || ' ' ||
             'AND fr.type = 1 ' ||
             'AND ' || quarter_condition || ' ' ||
             'AND fr.name IN (' || 
             array_to_string(formatted_names, ', ') || 
             ') ' ||
             'GROUP BY d.quarter, d.year ' ||
             'ORDER BY d.quarter, d.year;';

    RETURN sql_raw;
END;
$$ LANGUAGE plpgsql;
