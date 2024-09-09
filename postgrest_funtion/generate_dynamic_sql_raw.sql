CREATE OR REPLACE FUNCTION generate_dynamic_sql_raw(symbol TEXT, category_name TEXT, mode TEXT)
RETURNS TEXT AS $$
DECLARE
    quarter_condition TEXT;
    time_column TEXT;
    raw_sql TEXT;
    case_statements TEXT := '';
    input_name TEXT;
    input_names TEXT[];
    sanitized_category_name TEXT;
BEGIN
    -- Sanitize category_name by replacing double quotes with single quotes
    sanitized_category_name := replace(category_name, '"', '''');

    -- Collect input_names based on symbol and sanitized_category_name
    SELECT array_agg(fr.name) INTO input_names
    FROM finance_report fr
    JOIN finance_report fr2 ON fr.parent_id = fr2.id
    WHERE fr.symbol_ticker = symbol AND fr2.name = sanitized_category_name;

    -- Check if input_names is NULL or empty
    IF input_names IS NULL OR array_length(input_names, 1) = 0 THEN
        RAISE EXCEPTION 'No matching finance reports found for symbol % and category %', symbol, sanitized_category_name;
    END IF;

    -- Determine the condition for quarter based on the mode
    IF mode = 'year' THEN
        quarter_condition := 'd.quarter = 0';
        time_column := 'd.year::TEXT AS "Time"';
    ELSIF mode = 'quarter' THEN
        quarter_condition := 'd.quarter != 0';
        time_column := 'CASE WHEN d.quarter = 0 THEN d.year::TEXT ELSE ''Q'' || d.quarter::TEXT || '' '' || d.year::TEXT END AS "Time"';
    ELSE
        RAISE EXCEPTION 'Invalid mode. Use ''year'' or ''quarter''.';
    END IF;

    -- Generate the initial part of the raw_sql
    raw_sql := format('SELECT d.quarter, d.year, %s', time_column);

    -- Generate case statements for each name in input_names
    FOREACH input_name IN ARRAY input_names
    LOOP
        case_statements := case_statements || format(
            ', MAX(CASE WHEN fr.name = %L THEN d.value ELSE 0 END) AS "%s"',
            input_name, input_name
        );
    END LOOP;

    -- Append the case statements to the raw_sql
    raw_sql := raw_sql || case_statements;

    -- Complete the raw_sql
    raw_sql := raw_sql || ' FROM finance_report fr ' ||
             'JOIN data d ON fr.id = d.report_id ' ||
             'WHERE fr.symbol_ticker = ' || quote_literal(symbol) || ' ' ||
             'AND fr.type = 1 ' ||
             'AND ' || quarter_condition || ' ' ||
             'AND fr.name IN (' || 
             array_to_string(array(SELECT quote_literal(unnest(input_names))), ', ') || 
             ') ' ||
             'GROUP BY d.quarter, d.year ' ||
             'ORDER BY d.year, d.quarter;';

    RETURN raw_sql;
END;
$$ LANGUAGE plpgsql;


---------------------------optimize version----------------------------------------------------------

CREATE OR REPLACE FUNCTION generate_dynamic_sql_raw(symbol TEXT, category_name TEXT, mode TEXT)
RETURNS TEXT AS $$
DECLARE
    quarter_condition TEXT;
    time_column TEXT;
    raw_sql TEXT;
    input_names TEXT[];
    sanitized_category_name TEXT;
BEGIN
    -- Sanitize category_name by replacing double quotes with single quotes
    sanitized_category_name := replace(category_name, '""', '''');

    -- Collect input_names based on symbol and sanitized_category_name
    SELECT array_agg(fr.name) INTO input_names
    FROM finance_report fr
    JOIN finance_report fr2 ON fr.parent_id = fr2.id
    WHERE fr.symbol_ticker = symbol AND fr2.name = sanitized_category_name;

    -- Check if input_names is NULL or empty
    IF input_names IS NULL OR array_length(input_names, 1) = 0 THEN
        RAISE EXCEPTION 'No matching finance reports found for symbol % and category %', symbol, sanitized_category_name;
    END IF;

    -- Determine the condition for quarter and time column based on the mode
    IF mode = 'year' THEN
        quarter_condition := 'd.quarter = 0';
        time_column := 'd.year::TEXT AS "Time"';
    ELSIF mode = 'quarter' THEN
        quarter_condition := 'd.quarter != 0';
        time_column := 'CASE WHEN d.quarter = 0 THEN d.year::TEXT ELSE ''Q'' || d.quarter::TEXT || '' '' || d.year::TEXT END AS "Time"';
    ELSE
        RAISE EXCEPTION 'Invalid mode. Use ''year'' or ''quarter''.';
    END IF;

    -- Generate the complete raw_sql using a single format call
    raw_sql := format(
        'SELECT d.quarter, d.year, %s, %s ' ||
        'FROM finance_report fr ' ||
        'JOIN data d ON fr.id = d.report_id ' ||
        'WHERE fr.symbol_ticker = %L ' ||
        -- 'AND fr.type = 1 ' ||
        'AND %s ' ||
        'AND fr.name = ANY(%L) ' ||
        'GROUP BY d.quarter, d.year ' ||
        'ORDER BY d.year, d.quarter;',
        time_column,
        (SELECT string_agg(format('MAX(CASE WHEN fr.name = %L THEN d.value ELSE 0 END) AS "%1$s"', name), ', ')
         FROM unnest(input_names) AS name),
        symbol,
        quarter_condition,
        input_names
    );

    RETURN raw_sql;
END;
$$ LANGUAGE plpgsql;


-------------------------example----------------------

-- SELECT generate_dynamic_sql_raw(
--     'HAH',
--     'Name1',
--     'year'
-- );

-- SELECT generate_dynamic_sql_raw(
--     'HAH',
--     'Name1',
--     'quarter'
-- );



---------------------------------create view----------------------------------------------------------
CREATE OR REPLACE FUNCTION create_dynamic_view(symbol TEXT, category_name TEXT, mode TEXT)
RETURNS VOID AS $$
DECLARE
    view_name TEXT := 'dynamic_view';
    dynamic_sql TEXT;
BEGIN
    -- Drop the view if it exists
    EXECUTE format('DROP VIEW IF EXISTS %I', view_name);

    -- Generate the dynamic SQL
    dynamic_sql := generate_dynamic_sql_raw(symbol, category_name, mode);
    
    -- Create the view
    EXECUTE format('CREATE VIEW %I AS %s', view_name, dynamic_sql);
END;
$$ LANGUAGE plpgsql;

-- Example usage:
-- SELECT create_dynamic_view(ARRAY['Name1', 'Name2', 'Name3'], 'HAH', 'year');
-- SELECT create_dynamic_view(ARRAY['Name1', 'Name2', 'Name3'], 'HAH', 'quarter');
