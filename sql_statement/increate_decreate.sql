with t1 as (
select
	date,
	close,
	lag(close) over (
	order by date) as prev_close,
	case
		when lag(close) over (
		order by date) is not null then
                ((close - lag(close) over (
		order by date)) / lag(close) over (
		order by date) * 100)
		else
                null
	end as percent_change
from
	market
where
	symbol_ticker = 'VCI'
),
t2 as (
select
	date,
	close,
	percent_change,
	case
		when percent_change > 0 then 1
		when percent_change < 0 then -1
		else 0
	end as change
from
	t1
),
Transitions as (
select
	date,
	change,
	lag(change) over (
	order by date) as prev_change
from
	t2
),
GroupedChanges as (
select
	date,
	change,
	case
		when change = prev_change then 0
		else 1
	end as is_change
from
	Transitions
),
FinalGroups as (
select
	date,
	change,
	SUM(is_change) over (
	order by date rows between unbounded preceding and current row) as group_id
from
	GroupedChanges
),
SummedChanges as (
select
	date,
	change,
	--        group_id,
	SUM(change) over (partition by group_id
order by
	date rows between unbounded preceding and current row) as position
from
	FinalGroups
)

select
	date,
	change,
	position,
	MAX(position) over (
order by
	date rows between 20 preceding and current row) as max_ping,
	MIN(position) over (
order by
	date rows between 20 preceding and current row) as min_ping
from
	SummedChanges
order by
	date desc;
