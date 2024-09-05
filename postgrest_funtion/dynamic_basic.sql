CREATE OR REPLACE FUNCTION generate_dynamic_query(input_names TEXT[])
RETURNS TEXT AS $$
DECLARE
    query TEXT;
    case_statements TEXT;
    name TEXT;
BEGIN
    -- Initialize the base query
    query := 'SELECT d.quarter, d.year';

    -- Generate CASE statements for each input name
    FOREACH name IN ARRAY input_names
    LOOP
        case_statements := format(
            'MAX(CASE WHEN fr.name = %L THEN d.value ELSE 0 END) AS "%s"',
            name, name
        );
        query := query || ', ' || case_statements;
    END LOOP;

    -- Complete the query
    query := query || ' FROM finance_report fr ' ||
             'JOIN data d ON fr.id = d.report_id ' ||
             'WHERE fr.symbol_ticker = ''HAH'' ' ||
             'AND fr.type = 1 ' ||
             'AND d.quarter = 0 ' ||
             'AND fr.name IN (' || 
             array_to_string(array(SELECT format('''%s''', unnest(input_names))), ', ') || 
             ') ' ||
             'GROUP BY d.quarter, d.year ' ||
             'ORDER BY d.quarter, d.year;';

    RETURN query;
END;
$$ LANGUAGE plpgsql;
