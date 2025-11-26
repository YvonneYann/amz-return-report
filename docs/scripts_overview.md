# pipeline 模块脚本说明

## 目录结构
```
pipeline/
├── __init__.py
├── __main__.py
├── asin_structure.py
├── cli.py
├── config.py
├── doris_client.py
├── parent_summary.py
├── problem_reasons.py
└── utils.py
```

## 模块职责
- `parent_summary.py`：对应 PRD 4.1，封装父体维度数据过滤与汇总逻辑（`filter_snapshot_rows`、`build_parent_summary`）。
- `asin_structure.py`：对应 PRD 4.2，负责子 ASIN 粒度聚合、主战场/问题款识别以及榜单截断策略。
- `problem_reasons.py`：对应 PRD 4.3，筛选退货文本样本、评估置信度并输出核心退货原因集合。
- `cli.py`：命令行入口，解析参数、加载数据源、逐步调用 4.1→4.3 子模块并输出 JSON。
- `config.py`：dataclass 配置定义，集中管理阈值及默认参数。
- `doris_client.py`：本地样例/ Doris 数据读取工具，后续也可扩展为入库接口。
- `utils.py`：通用方法（安全除法、日期解析等）。
- `__main__.py` / `__init__.py`：分别用于 `python -m pipeline` 运行及对外暴露公共接口。

## 典型执行顺序
1. 通过 CLI 调用 `python -m pipeline`，解析参数后构造 `ComputationParams`。
2. `doris_client` 读取 `view_return_snapshot`、`view_return_fact_details`、`return_dim_tag` 三份 JSON（可替换为 Doris 查询结果）。
3. CLI 依次调用：
   - `parent_summary.filter_snapshot_rows` + `build_parent_summary`；
   - `asin_structure.build_asin_structure`；
   - `problem_reasons.filter_fact_rows` + `build_problem_reasons`。
4. 将结果写入 JSON 文件或标准输出，供后续 BI/报告模块使用。