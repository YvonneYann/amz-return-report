-- AMZ 退货分析 --
-- CREATE OR REPLACE VIEW hyy.view_return_snapshot as 
select country_name country,variation_asin fasin,asin,STR_TO_DATE(workdate,'%Y-%m-%d') snapshot_date,
units_ordered units_sold,returns units_returned
from HYY_DW_MYSQL.hyy.jj_sales_performance
where STR_TO_DATE(workdate,'%Y-%m-%d') >= CURDATE() -interval 365 day;
-- and country_name = 'US' and variation_asin = 'B0BGHGXYJX'
-- order by units_returned desc;