with t1 as (
select
	*
from
	finance_report fr
where
	
    fr.symbol_ticker = UPPER('MSH')
and type = 3
and lever in (3)
)
  select
	fr2.symbol_ticker,
	fr2.name,
	d.value,
	d.quarter,
	d.year
from
	finance_report fr2
join data d on
	fr2.id = d.report_id
where
	d.quarter = 0
	and fr2.parent_id in (select id from finance_report where finance_report.name = 'II. Lưu chuyển tiền từ hoạt động đầu tư')
	and d.year = 2023
    and	fr2.symbol_ticker = UPPER('MSH')


-- ----------------------------------------------------------



select
	d.quarter,
	d.year,
	d.year::text as "Time",
	MAX(case when fr.name = '1. Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác' then d.value else 0 end) as "1. Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác",
	MAX(case when fr.name = '2. Tiền thu từ thanh lý, nhượng bán TSCĐ và các tài sản dài hạn khác' then d.value else 0 end) as "2. Tiền thu từ thanh lý, nhượng bán TSCĐ và các tài sản dài hạn khác",
	MAX(case when fr.name = '3. Tiền chi cho vay, mua các công cụ nợ của đơn vị khác' then d.value else 0 end) as "3. Tiền chi cho vay, mua các công cụ nợ của đơn vị khác",
	MAX(case when fr.name = '4. Tiền thu hồi cho vay, bán lại các công cụ nợ của các đơn vị khác' then d.value else 0 end) as "4. Tiền thu hồi cho vay, bán lại các công cụ nợ của các đơn vị khác",
	MAX(case when fr.name = '5. Đầu tư góp vốn vào công ty liên doanh liên kết' then d.value else 0 end) as "5. Đầu tư góp vốn vào công ty liên doanh liên kết",
	MAX(case when fr.name = '6. Chi đầu tư ngắn hạn' then d.value else 0 end) as "6. Chi đầu tư ngắn hạn",
	MAX(case when fr.name = '7. Tiền chi đầu tư góp vốn vào đơn vị khác' then d.value else 0 end) as "7. Tiền chi đầu tư góp vốn vào đơn vị khác",
	MAX(case when fr.name = '8. Tiền thu hồi đầu tư góp vốn vào đơn vị khác' then d.value else 0 end) as "8. Tiền thu hồi đầu tư góp vốn vào đơn vị khác",
	MAX(case when fr.name = '9. Lãi tiền gửi đã thu' then d.value else 0 end) as "9. Lãi tiền gửi đã thu",
	MAX(case when fr.name = '10. Tiền thu lãi cho vay, cổ tức và lợi nhuận được chia' then d.value else 0 end) as "10. Tiền thu lãi cho vay, cổ tức và lợi nhuận được chia",
	MAX(case when fr.name = '11. Tiền chi mua lại phần vốn góp của các cổ đông thiểu số' then d.value else 0 end) as "11. Tiền chi mua lại phần vốn góp của các cổ đông thiểu số",
	MAX(case when fr.name = 'Lưu chuyển tiền thuần từ hoạt động đầu tư' then d.value else 0 end) as "Lưu chuyển tiền thuần từ hoạt động đầu tư"
from
	finance_report fr
join data d on
	fr.id = d.report_id
where
	fr.symbol_ticker = 'MSH'
	and d.quarter = 0
	and fr.name = any('{"1. Tiền chi để mua sắm, xây dựng TSCĐ và các tài sản dài hạn khác","2. Tiền thu từ thanh lý, nhượng bán TSCĐ và các tài sản dài hạn khác","3. Tiền chi cho vay, mua các công cụ nợ của đơn vị khác","4. Tiền thu hồi cho vay, bán lại các công cụ nợ của các đơn vị khác","5. Đầu tư góp vốn vào công ty liên doanh liên kết","6. Chi đầu tư ngắn hạn","7. Tiền chi đầu tư góp vốn vào đơn vị khác","8. Tiền thu hồi đầu tư góp vốn vào đơn vị khác","9. Lãi tiền gửi đã thu","10. Tiền thu lãi cho vay, cổ tức và lợi nhuận được chia","11. Tiền chi mua lại phần vốn góp của các cổ đông thiểu số","Lưu chuyển tiền thuần từ hoạt động đầu tư"}')
group by
	d.quarter,
	d.year
order by
	d.year,
	d.quarter;


    