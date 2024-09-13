with t1 as (
select
    m.symbol_ticker,
	date,
	case
		when s.exchange = 'UPCOM' then m.average
		else m.close
	end as price
from
	market m
join symbol s on
	m.symbol_ticker = s.ticker
),
t2 as (
select
    symbol_ticker,
	
	case
		when lag(price) over (partition by symbol_ticker order by date) is not null then
                ((price - lag(price) over (partition by symbol_ticker order by date)) / 
                 lag(price) over (partition by symbol_ticker order by date) * 100)
		else
                null
	end as percent_change,
	date
from
	t1
)

select * from t2 order by symbol_ticker asc, date desc




-- ------------------------------------funtion------------------------------------
-- Create the function
CREATE OR REPLACE FUNCTION upsert_history_data_processing()
RETURNS void AS $$
BEGIN
    -- Perform the upsert operation
    INSERT INTO history_data_processing (symbol_ticker, date, percent_change)
    SELECT symbol_ticker, date, percent_change
    FROM (
        -- Your existing query here
        with t1 as (
            select
                m.symbol_ticker,
                date,
                case
                    when s.exchange = 'UPCOM' then m.average
                    else m.close
                end as price
            from
                market m
            join symbol s on
                m.symbol_ticker = s.ticker
        ),
        t2 as (
            select
                symbol_ticker,
                case
                    when lag(price) over (partition by symbol_ticker order by date) is not null then
                        ((price - lag(price) over (partition by symbol_ticker order by date)) / 
                         lag(price) over (partition by symbol_ticker order by date) * 100)
                    else
                        null
                end as percent_change,
                date
            from
                t1
        )
        select * from t2
    ) AS source
    ON CONFLICT (date, symbol_ticker)
    DO UPDATE SET
        percent_change = EXCLUDED.percent_change;
END;
$$ LANGUAGE plpgsql;

-- Execute the function
SELECT upsert_history_data_processing();

