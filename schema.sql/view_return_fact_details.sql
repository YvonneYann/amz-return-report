-- AMZ 退货分析 --
-- CREATE OR REPLACE VIEW hyy.view_return_fact_details as 
with raw as
(select country_name country,fasin,asin,STR_TO_DATE(review_date,'%Y-%m-%d') review_date,
review_id,2 review_source,content review_en
from HYY_DW_MYSQL.hyy.jj_review
where star <= 3

union all 
select distinct b.country,c.parent_asin fasin,a.asin,return_date review_date,
order_id review_id,0 review_source,concat(reason,": ",customer_comments) review_en
from HYY_DW_MYSQL.hyy.jj_return_orders a
left join basic_account b on a.market_id = b.gg_marketid
left join hyy.view_asin_mid_new_info c on a.asin = c.asin and b.country = c.marketplace_id
where customer_comments <> '')

select country,fasin,asin,review_date,fact.* 
from hyy.return_fact_details fact
left join raw on raw.review_id = fact.review_id
where review_date >= CURDATE() -interval 180 day;
-- and country = 'US' and fasin = 'B0BGHGXYJX'
-- order by review_date desc;