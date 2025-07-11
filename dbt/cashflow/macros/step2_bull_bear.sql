
{% macro step2_bull_bear() %}
{{ return(run_query("
with result as (select 
date,
hdp.symbol_ticker,
--hdp.current_position,
--hdp.percent_change,
case
	 when row_number() over (PARTITION by hdp.symbol_ticker order by hdp.date ASC) > 20
	 then MAX(hdp.current_position)
	 over(
	       PARTITION by hdp.symbol_ticker
	       order by hdp.date asc 
	       rows between 20 preceding  AND 1 preceding
	 )
	 else null
end as max_bull_20,
case
	 when row_number() over (PARTITION by hdp.symbol_ticker order by hdp.date ASC) > 20
	 then MIN(hdp.current_position)
	 over(
	       PARTITION by hdp.symbol_ticker
	       order by hdp.date asc 
	       rows between 20 preceding  AND 1 preceding
	 )
	 else null
end as max_bear_20

from history_data_processing hdp  
order by hdp.symbol_ticker asc,date desc)


INSERT INTO history_data_processing (symbol_ticker, max_bull_20, max_bear_20, date)
SELECT
    symbol_ticker,
    max_bull_20,
    max_bear_20,
    date
FROM result where  max_bear_20 is not Null
ON CONFLICT (symbol_ticker, date)
DO UPDATE
SET
    max_bull_20 = EXCLUDED.max_bull_20,
    max_bear_20 = EXCLUDED.max_bear_20;")) }}


{% endmacro %}   