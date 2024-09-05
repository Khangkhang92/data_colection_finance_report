with t1 as (
select
	date,
	case
		when s.exchange = 'UPCOM' then m.average
		else m.close
	end as price
from
	market m
join symbol s on
	m.symbol_ticker = s.ticker
where
	m.symbol_ticker = 'VGI'
),
t2 as (
select
	date,
	price,
	lag(price) over (
order by
	date) as prev_price,
	case
		when lag(price) over (
	order by
		date) is not null then
                ((price - lag(price) over (
	order by
		date)) / lag(price) over (
	order by
		date) * 100)
		else
                null
	end as percent_change
from
	t1
),
t3 as (
select
	date,
	price,
	percent_change,
	case
		when percent_change > 0 then 1
		when percent_change < 0 then -1
		else 0
	end as change
from
	t2
),
Transitions as (
select
	date,
	price,
	percent_change,
	change,
	lag(change) over (
order by
	date) as prev_change
from
	t3
),
GroupedChanges as (
select
	date,
	price,
	percent_change,
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
	price,
	percent_change,
	change,
	SUM(is_change) over (
order by
	date rows between unbounded preceding and current row) as group_id
from
	GroupedChanges
),
SummedChanges as (
select
	date,
	price,
	percent_change,
	change,
	--        group_id,
	SUM(change) over (partition by group_id
order by
	date rows between unbounded preceding and current row) as ps
from
	FinalGroups
)

select
	date,
	price,
	percent_change,
	ps,
	MAX(ps) over (
order by
	date rows between 20 preceding and 1 preceding ) as max_increase ,
	MIN(ps) over (
order by
	date rows between 20 preceding and 1 preceding ) as max_drop
from
	SummedChanges
order by
	date desc;
