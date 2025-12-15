# ETL 代码结构说明（按文件用途 + 调用关系）

当前仅保留 3 条主视角的 pipeline。

## 共享层（etl/shared）
- `calculator.py`：日期解析/格式化、窗口计算、基础数学。
- `config_base.py`：数据库/阈值基类、环境文件解析、阈值覆盖工具，暴露 `BASE_DIR/DEFAULT_ENV_PATH`。
- `utils.py`：单窗 CLI 参数构造、运行时参数解析（加载 params.json + 计算窗口）、写表 `write_table`、补全天范围 `ensure_full_day_range`、`format_window`。
- `doris_client.py`：统一 Doris 客户端；`date_mode="review"` 用于退货视角，`date_mode="purchase"` 用于订单归因类视角，负责 snapshot/fact/orders/tag/BI 的查询与 JSON 缓存。

## 退货发生视角（etl/return_window，默认目录 template/return_window/）
- `config.py`：退货视角的路径/数据库/阈值配置，默认窗口天数 30。
- `cli_utils.py`：构建退货视角 CLI，解析 params.json 并计算单窗 `(start_date, end_date)`。
- `parent_summary.py`：基于 snapshot_date 过滤，计算父 ASIN 汇总（units_sold/returned、return_rate）。
- `asin_structure.py`：基于 snapshot_date 过滤，按 ASIN 聚合销量/退货，计算 A/B 类、高退货监控等标签。
- `problem_reasons.py`：基于 review_date 过滤 fact，按问题 ASIN 提取核心原因、覆盖率、可信度。
- `reason_explanations.py`：根据核心原因筛选 fact 详单，输出解释列表。
- `problem_asin_listing.py`：在 BI snapshot 中匹配问题 ASIN，取最新快照。
- `pipeline.py`：退货视角入口，组装以上步骤，调用 shared DorisClient(`date_mode=review`)，输出 JSON 带 `_return_window` 后缀。

调用链（退货）：`pipeline` → `cli_utils`(解析窗口) → `shared.doris_client`(拉数) → `parent_summary` → `asin_structure` → `problem_reasons` → `reason_explanations` → `problem_asin_listing` → `shared.utils.write_table`

## 订单归因视角（etl/order_attribution，默认目录 template/order_attribution/）
- `config.py`：路径/数据库/阈值配置，默认窗口天数 90，可接收阈值覆盖。
- `cli_utils.py`：解析 before/after 两段购买窗，支持手动覆盖，阈值 JSON 覆盖。
- `parent_summary.py`：按 snapshot_date（销量）+ purchase_date（退货）过滤，计算父 ASIN 汇总，带 `window_label`。
- `asin_structure.py`：按 snapshot_date + purchase_date 过滤，计算 A/B 分类、监控标签，带 `window_label`。
- `problem_reasons.py`：purchase_date 窗口筛 fact，按问题 ASIN 统计核心原因、覆盖率、可信度，带 `window_label`。
- `reason_explanations.py`：按 purchase_date 范围与核心原因筛 fact，输出解释，带窗口信息。
- `problem_asin_listing.py`：按窗口/优先级选择 BI snapshot（最新/窗口内最优），带 `window_label` 与窗口起止。
- `pipeline.py`：订单归因入口，双窗循环运行上述步骤，DorisClient(`date_mode=purchase`)，输出文件名带 `_<label>.json`。

调用链（订单归因）：`pipeline` → `cli_utils`(双窗解析) → `shared.doris_client`(date_mode=purchase) → `parent_summary` → `asin_structure` → `problem_reasons` → `reason_explanations` → `problem_asin_listing` → `shared.utils.write_table`

## 单窗订单归因视角（etl/purchase_window，默认目录 template/purchase_window/）
- `config.py`：路径/数据库/阈值配置，默认窗口天数 30。
- `cli_utils.py`：参数同退货视角（biz_date/start/end），解析单一购买窗。
- `pipeline.py`：单窗购买视角入口，沿用订单归因的计算函数，DorisClient(`date_mode=purchase`)，输出文件名带 `_purchase_window` 后缀。

调用链（单窗归因）：`pipeline` → `cli_utils`(单窗解析) → `shared.doris_client`(date_mode=purchase) → 复用 order_attribution 的 `parent_summary/asin_structure/problem_reasons/reason_explanations/problem_asin_listing` → `shared.utils.write_table`

## 入口命令
- 进入目录：`cd C:\Users\MOREFINE\Desktop\amz-return-report`
- 退货视角：`py -3 -m etl.return_window.pipeline ...`
- 订单归因：`py -3 -m etl.order_attribution.pipeline ...`
- 单窗归因：`py -3 -m etl.purchase_window.pipeline ...`

输出文件名带各自后缀区分视角（`_return_window`、`_purchase_window`，或 `_order_attribution` 的窗口标签）。
