# 订单归因视角 PRD

## 3. 视图 / 表结构

### 3.1 销量 & 退货数据

#### 3.1.1 销量数据

- **view\_return\_snapshot**

  - 内容：数据表按国家、父ASIN、子ASIN和日期维度聚合存储每日销售数据，为退货率计算提供核心基础数据支撑。
  - 主键：`country`、`fasin`、`asin`、`snapshot_date`

输出示例：

```json
{
"view_return_snapshot": [
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-04",
		"units_sold" : 8
	},
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-02",
		"units_sold" : 19
	}
 ]
}
```

#### 3.1.2 退货数据

- **view\_return\_orders\_snapshot**

  - 内容：数据表按国家、父ASIN、子ASIN、日期和订单维度聚合存储每日退货数据，为退货率计算提供核心基础数据支撑。
  - 主键：`country`、`fasin`、`asin`、`purchase_date`、`review_id`

输出示例：

```json
{
"view_return_orders_snapshot": [
{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"purchase_date" : "2025-08-02 09:36:31",
		"review_id" : "113-3071682-6176201",
		"quantity" : 1
	},
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"purchase_date" : "2025-08-01 14:12:20",
		"review_id" : "111-3072640-0190643",
		"quantity" : 1
	}
 ]
}
```

### 3.2 退货打标 & 标签数据

#### 3.2.1 打标事实表

- **view\_return\_fact\_details**

  - 内容：存储每个国家、父ASIN、子ASIN、购买日期、评论ID、标签代码的详细退货原因信息，为退货原因分析提供基础数据。
  - 主键：`country`、`fasin`、`asin`、`purchase_date`、`review_id`、`tag_code`

输出示例：

```json
{
"view_return_fact_details": [
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0D4QLYM4C",
		"purchase_date" : "2025-12-03 16:40:30",
		"review_id" : "111-5573349-1202651",
		"tag_code" : "FIT_COMPAT",
		"review_source" : 1,
		"review_en" : "The width dimension on 9” doesn't take into account the thumb screws that add another half inch making it just a hair too wide to fit",
		"review_cn" : "9英寸的宽度尺寸没有考虑到拇指螺丝增加了半英寸，导致刚好稍微宽了一点，无法安装",
		"sentiment" : -1,
		"tag_name_cn" : "尺寸\/兼容性不符",
		"evidence" : "just a hair too wide to fit",
		"created_at" : "2025-12-09 02:40:22",
		"updated_at" : "2025-12-09 02:40:22"
	}
 ]
}
```


## 4. Python 计算模块

### 4.1 与退货视角的差异补充（仅列差异）

- 时间窗口：按 `adjust_date` 左右的 before/after 购买窗口（默认 90 天），订单判定基于 purchase_date；参数见 `config/order_attribution_run_params.json`。
- 退货滞后：对订单退货事件按 purchase_date → review_date 间隔做过滤（默认 `return_lag_days = 35`），区别于退货视角的 review_date 窗口校验。
- 输入表侧重点：
  - `view_return_orders_snapshot` 作为退货事实源（purchase_date 粒度）；
  - `view_return_fact_details` 在 Python 侧按 purchase_date + return_lag 过滤，再写出 before/after 两套结果；
  - `view_bi_amz_asin_product_snapshot` 拉全 before/after 覆盖范围，Python 端为两个窗口各自挑选最优快照。
- 输出形态：所有重加工表增加 `window_label`、`start_date`、`end_date`，输出为成对的 `*_before.json` 与 `*_after.json`。
- 参数/配置：
  - `config.py` 支持 `environment_path` 与 `threshold_overrides`，可独立于退货视角设置阈值；
  - CLI 增加 `--adjust-date`、before/after 窗口覆盖、`--return-lag-days`、`--thresholds-json`、`--env-file`，不使用退货视角的 biz_date 逻辑。
- Pipeline 行为：从 Doris 抽取时直接覆盖 `template/order_attribution/input` 缓存，输出到 `template/order_attribution/output`，不依赖已有本地数据。

### 4.2 问题 ASIN 商品信息版本筛选（problem_asin_listing）

> 说明：`view_bi_amz_asin_product_snapshot` 的版本筛选不在 Doris 视图内处理，而在 Python 侧按调整日选择最贴近的 before/after 快照。

- 拉取范围：一次性从 Doris 拉取覆盖 before/after 两段窗口的日期范围（end 至少取 max(after_end, today)），再在 Python 侧筛选。
- 规则（按 ASIN 独立筛选 1 个版本）：
  - before：选择 `snapshot_date <= adjust_date` 且最接近 `adjust_date` 的快照；若无调整日前快照，则该 ASIN 在 before 为空。
  - after：优先选 `snapshot_date >= adjust_date` 且落在 after 窗口内、距离 `adjust_date` 最近的快照；若窗口内无，则取 `snapshot_date >= adjust_date` 的最新快照；若仍无，则取该 ASIN 最新快照。
- 输出形态：文件名 `problem_asin_listing_before/after.json`，顶级表名 `problem_asin_listing_before/after`，每行记录含 `window_label`、`start_date`、`end_date` 便于对比。
- 责任边界：Doris 仅供数据源，版本选择完全由 Python 脚本完成。
