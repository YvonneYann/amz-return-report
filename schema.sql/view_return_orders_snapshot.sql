-- AMZ 退货分析 --
-- CREATE OR REPLACE VIEW hyy.view_return_orders_snapshot as 
select b.country,c.parent_asin fasin,a.asin,return_date review_date,purchase_date,purchase_date +interval 45 day return_deadline,
order_id review_id,quantity
from HYY_DW_MYSQL.hyy.jj_return_orders a
left join basic_account b on a.market_id = b.gg_marketid
left join hyy.view_asin_mid_new_info c on a.asin = c.asin and b.country = c.marketplace_id
where purchase_date >= CURDATE() -interval 180 day;