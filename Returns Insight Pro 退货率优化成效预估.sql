-- AMZ 退货分析 --
-- DE 退货订单 - 购买日期 --
-- Returns Insight Pro 退货率优化成效预估 --
select order_data.*,return_data.return_date,return_data.units_returned from 

-- orders --
(select b.country,c.parent_asin fasin,a.asin,DATE(purchase_date) purchase_date,order_id,
sum(quantity) units_sold
from HYY_DW_MYSQL.hyy.jj_all_orders a
left join hyy_mysql.basic_account b on a.market_id = b.gg_marketid
left join hyy.view_asin_mid_new_info c on a.asin = c.asin and b.country = c.marketplace_id
where DATE(purchase_date) <= CURDATE() -INTERVAL 2 DAY
group by b.country,c.parent_asin,a.asin,DATE(purchase_date),order_id) order_data

-- returns --
left join 
(select order_id,asin,DATE(purchase_date) purchase_date,DATE(return_date) return_date,sum(quantity) units_returned
from HYY_DW_MYSQL.hyy.jj_return_orders
group by order_id,asin,DATE(purchase_date),DATE(return_date)) return_data
on return_data.order_id = order_data.order_id 
and return_data.asin = order_data.asin 
and return_data.purchase_date = order_data.purchase_date;