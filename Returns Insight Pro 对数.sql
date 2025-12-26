-- Returns-Insight-Pro --
-- check：return status w/ review date --
select NOW() - INTERVAL 90 DAY;

select sum(units_sold),sum(units_returned)
from hyy.view_return_snapshot
where date_format(snapshot_date,'%Y%m%d') between 20250917 and 20251215
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select count(distinct review_id)
from hyy.view_return_fact_details
where date_format(review_date,'%Y%m%d') between 20250917 and 20251215 and review_source < 2
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23'
and tag_code = 'FIT_COMPAT';

select * from hyy.view_return_fact_details
where date_format(review_date,'%Y%m%d') between 20250917 and 20251215
and asin = 'B0BGHH2L23'
and tag_code = 'FIT_COMPAT'
order by length(evidence) desc;



-- check：return status w/ purchase date --
select NOW() - INTERVAL 90 DAY;

select sum(units_sold)
from hyy.view_return_snapshot
where date_format(snapshot_date,'%Y%m%d') between 20250917 and 20251215
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select sum(quantity)
from hyy.view_return_orders_snapshot
where date_format(purchase_date,'%Y%m%d') between 20250917 and 20251215
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select count(distinct review_id)
from hyy.view_return_fact_details
where date_format(purchase_date,'%Y%m%d') between 20250620 and 20251216 and review_source < 2
and asin = 'B092QN244N' 
and tag_code = 'CAPACITY_EFF';

select * from hyy.view_return_fact_details
where date_format(purchase_date,'%Y%m%d') between 20250620 and 20251216
and asin = 'B092QN244N'
and tag_code = 'CAPACITY_EFF'
order by length(evidence) desc;



-- check：return A/B test w/ purchase date --
select STR_TO_DATE('2025-08-20','%Y-%m-%d') - INTERVAL 90 DAY,STR_TO_DATE('2025-08-19','%Y-%m-%d') + INTERVAL 90 DAY;
select NOW() -INTERVAL 30 DAY;

-- before --
select sum(units_sold)
from hyy.view_return_snapshot
where date_format(snapshot_date,'%Y%m%d') between 20250522 and 20250819
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select sum(quantity)
from hyy.view_return_orders_snapshot
where date_format(purchase_date,'%Y%m%d') between 20250522 and 20250819
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select count(distinct review_id)
from hyy.view_return_fact_details
where date_format(purchase_date,'%Y%m%d') between 20250522 and 20250819 and review_source < 2
and asin = 'B0BGHH2L23' 
and tag_code = 'FIT_COMPAT';


-- after --
select sum(units_sold)
from hyy.view_return_snapshot
where date_format(snapshot_date,'%Y%m%d') between 20250820 and 20251117
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select sum(quantity)
from hyy.view_return_orders_snapshot
where date_format(purchase_date,'%Y%m%d')between 20250820 and 20251117
and fasin = 'B0BGHGXYJX' and asin = 'B0BGHH2L23';

select count(distinct review_id)
from hyy.view_return_fact_details
where date_format(purchase_date,'%Y%m%d') between 20250820 and 20251117 and review_source < 2
and asin = 'B0BGHH2L23' 
and tag_code = 'FIT_COMPAT';