-- AMZ 退货分析 --
-- CREATE OR REPLACE VIEW hyy.view_bi_amz_asin_product_snapshot as 
select marketplace_id country,parent_asin fasin,asin,sunday snapshot_date,payload  
from hyy.bi_amz_asin_product_snapshot;