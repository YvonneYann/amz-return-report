# 父体退货分析自动化系统 PRD（Python 计算模块）

> 面向对象：数据/平台工程、后端、AI 平台/算法同学（负责实现与运维 Python 计算模块）
>
> 目标：将当前已敲定的「退货分析报告终版框架」产品化，形成一套可复用、可批量跑的自动化分析流水线，由 Python 模块负责所有量化计算和结构化数据输出；后续这些结果将接入 Google 的 AI App，利用其 BI 看板可视化和 LLM 业务解读能力，为业务方生成一体化的退货分析报告（该部分不在本 PRD 实现范围内）。

---

## 1. 背景 & 立项动机

### 1.1 业务背景

目前针对 Amazon 父 ASIN 的退货分析，整体流程是：

1. 人工从后台导数（ASIN 维度的销量/退货报表）；
2. 人工整理并做退货率计算、子 ASIN 结构分析；
3. 将退货留言/差评导出、打标签或人工阅读，做原因拆解；
4. 分析师/产品/运营写 Word/PPT 报告，给团队或管理层过数。

存在的问题：

- **强依赖人肉拉数 + 手动计算**，分析一次一个父体要投入较多时间；
- **结构无法完全统一**，不同人写的报告结构和指口不一致，不利于横向对比；
- 退货原因拆解中涉及大量 groupby / 聚合，重复性高且易出错；
- 很难快速对多个父体做批量退货体检。

### 1.2 项目目标

构建一套「父体级退货分析报告自动化系统」，实现：

1. **一键生成退货分析「底层数据结果」**：输入父 ASIN + 时间范围，即可自动算出父体及子 ASIN 的完整退货指标集（含整体退货率、结构占比、问题 ASIN 标记、核心原因等），供后续自动化报告消费，用于内部复盘。
2. **结构高度标准化**：所有父体的报告在结构、章节、表格维度完全统一，只通过参数/数据差异来体现差别，方便横向对比。
3. **角色分工清晰**：
   - 本项目聚焦于上游 Python 计算模块，负责：全部量化计算、聚合和排序，输出标准化 JSON；
   - 下游由 Google 的 AI App 消费这些 JSON 结果，生成可视化图表和面向业务的文字解读（不在本 PRD 范围内，仅作为规划方向）。
4. **可扩展至其它父体/品类**：框架对父 ASIN/站点/品类透明，只要输入数据结构满足约定即可复用，便于后续批量体检更多父体或推广到其他类目。

（后续规划：Python 量化结果将统一接入 Google 的 AI App，由其结合 BI 看板可视化和 LLM 业务解读，生成对业务同学友好的可视化退货分析报告；该部分不在本 PRD 实现范围内，仅作为本项目的下游应用场景。）

---

## 2. 本期范围 & 迭代方向

### 2.1 本期范围

- 站点：Amazon（支持多站点）；
- 分析对象：单个父 ASIN（后续可以通过批量任务覆盖更多父体）；
- 时间范围：支持自定义起止日期，聚焦这段时间内的整体表现，不拆分月度/周度趋势；
- 分析框架：
  1. **先看整体盘子**：在指定站点 + 时间段内，算清楚这个父体的总销量、总退货量和整体退货率，给出当前退货健康度的“体检结果”。
  2. **再看子体结构**：拆到每个子 ASIN，看谁贡献了主要销量、谁贡献了主要退货，并按照统一规则给子 ASIN 贴上「主战场款」「高退货问题款」和「高退货小体量观察对象」等标签，快速锁定需要优先关注的款式。
  3. **最后看退货原因**：只针对上述重点问题款，结合退货留言标签，找出主要退货原因，评估样本是否够多、结论是否可信，用二八原则聚焦能解释大部分问题的少数几个原因。
- 报告内容结构：
  - 0. 分析背景 & 目标（模板自动填充）：说明看的是哪个站点、哪个父体、哪段时间、数据来自哪里，本次分析想回答哪些关键问题。

  - 1. 父体总览：
    - 父体健康度：给出这段时间内父体的总销量、总退货量、整体退货率，以及父体健康度的“体检结果”（正常/偏高）；
    - 子 ASIN 结构：识别撑起销量和退货的主要子 ASIN，并标出主战场款、高退货问题款和高退货小体量观察对象，帮助业务快速看清“谁在卖货、谁在退货、谁是优先要管的款”。

  - 2. 问题 ASIN 退货原因拆解：聚焦主战场款和高退货问题款，看清它们各自的核心退货原因，同时标注每个结论对应的样本条数和留言率，区分“可以安心拿来做结构化判断的结论”和“仅供参考的用户声音画像”

### 2.2 迭代方向

- 时间趋势：本期只回答“这段时间整体退得怎么样”，不绘制按月/按周的退货曲线，也不做季节性分析；
- 具体动作效果：不区分“调整前/调整后”，只看当前选定时间段的整体表现；
- 跨父体 / 跨站点对比：本期报告以“单个父体在单个站点”的深度体检为主，不输出多父体、多站点的对比榜单；
- 自动生成行动计划：系统会指出“重点问题款”和“主要退货原因”，但不会自动生成运营项目或改版方案，具体怎么落地仍由业务团队结合资源和策略决策；
- 搭建或调整标签体系：本期默认使用既有的退货标签和打标结果，不负责设计或优化标签体系；
- 子 ASIN 原因拆解：原因分析只针对主战场款和高退货问题款，其他长尾子 ASIN 仅在结构部分展示退货表现，不单独做原因拆解。

---


## 3. 视图 / 表结构

### 3.1 销量 & 退货数据

- **view\_return\_snapshot**

  - 内容：数据表按国家、父ASIN、子ASIN和日期维度聚合存储每日销售与退货数据，为退货率计算提供核心基础数据支撑。
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
		"units_sold" : 8,
		"units_returned" : 8
	},
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-02",
		"units_sold" : 19,
		"units_returned" : 8
	}
 ]
}
```

### 3.2 退货打标 & 标签数据

#### 3.2.1 标签维表

- **return\_dim\_tag**

  - 内容：存放标签维度信息，为事实表提供标签定义、边界以及版本/生效期等维度信息，保证分析口径一致性。
  - 主键：`tag_code`

输出示例：

```json
{
"return_dim_tag": [
	{
		"tag_code" : "FIT_COMPAT",
		"tag_name_cn" : "尺寸\/兼容性不符",
		"category_code" : "CAT_STRUCT_FIT",
		"category_name_cn" : "产品结构\/适配体验",
		"level" : 2,
		"definition" : "与目标位置\/设备（如水槽、台面、柜体等）尺寸不匹配，导致无法放入、无法跨放，或间隙过大严重影响使用。",
		"boundary_note" : "尺寸能放下且主要问题为某特定场景下出现倾斜\/回流水等→“沥水\/排水问题”或“整体稳定性差\/易晃动”；仅为轻微缝隙、基本不影响使用→可不打本标签；由页面规格错误引起的认知偏差将由页面描述评估单独处理，本标签不区分该类客观误差。",
		"is_active" : 1,
		"version" : 2,
		"effective_from" : "2025-11-01",
		"effective_to" : null,
		"created_at" : "2025-11-17 04:55:33",
		"updated_at" : "2025-11-17 04:55:33"
	}
 ]
}
```

#### 3.2.2 打标事实表

- **view\_return\_fact\_details**

  - 内容：存储每个国家、父ASIN、子ASIN、评论日期、评论ID、标签代码的详细退货原因信息，为退货原因分析提供基础数据。
  - 主键：`country`、`fasin`、`asin`、`review_date`、`review_id`、`tag_code`

输出示例：

```json
{
"view_return_fact_details": [
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"review_date" : "2025-09-21 00:00:00",
		"review_id" : "R3GDDPAC4WALFE",
		"tag_code" : "INSTALL_COMPLEX",
		"review_source" : 2,
		"review_en" : "Not what I expected. Needed to be put together. Flimsy",
		"review_cn" : "不符合预期。需要组装。不结实",
		"sentiment" : -1,
		"tag_name_cn" : "安装\/组装复杂（耗时高）",
		"evidence" : "Needed to be put together",
		"created_at" : "2025-11-17 06:45:47",
		"updated_at" : "2025-11-17 06:45:47"
	}
 ]
}
```

---


## 4. Python 计算模块

> 目标：对给定**国家（站点） + 父 ASIN + 时间范围**，完成所有与退货分析报告相关的数值计算与聚合，统一输出标准化 JSON 供下游模块使用。所有聚合在父体或子 ASIN 粒度上，均需显式带上 `country` 维度（例如：`group by country + parent_asin` 或 `group by country + parent_asin + asin`）。

---

### 4.1 父体整体指标计算

> 目标：在指定国家/站点与时间范围内，计算单个父 ASIN 的整体销量、退货量与退货率，作为退货分析报告的盘子基准，并为后续模块提供 `return_rate_parent` 等基准指标。

#### 输入

- 上游来源：view\_return\_snapshot
- 输入参数：
  - `country`：站点/国家（如 `US`，`JP`）。
  - `fasin`：父 ASIN。
  - `start_date`：起始日期（含）。
  - `end_date`：结束日期（含）。
- 输入 JSON 结构示例：

```json
{
"view_return_snapshot": [
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-04",
		"units_sold" : 8,
		"units_returned" : 8
	},
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-02",
		"units_sold" : 19,
		"units_returned" : 8
	}
 ]
}
```

#### 逻辑

1. 筛选条件：
   - `country = 输入.country`；
   - `fasin = 输入.fasin`；
   - `start_date ≤ snapshot_date ≤ end_date`。
2. 聚合维度：
   - `group by country, fasin`。
3. 指标计算：
   - `total_units_sold_parent = sum(units_sold)`；
   - `total_units_returned_parent = sum(units_returned)`；
   - `return_rate_parent = total_units_returned_parent / total_units_sold_parent`。

#### 输出

- 输出给：下游 子 ASIN 结构计算，需用 `return_rate_parent`；
- 输出 JSON 结构示例：

```json
{
  "parent_summary": {
    "country": "US",
    "fasin": "B0BGHGXYJX",
    "start_date": "2025-01-01",
    "end_date": "2025-11-12",
    "units_sold": 20088,
    "units_returned": 2272,
    "return_rate": 0.113
  }
}
```

---

### 4.2 子 ASIN 结构计算

> 目标：在指定国家/站点与时间范围内，基于父体 `parent_summary`，计算各子 ASIN 的销量、退货量、退货率及其在父体中的贡献占比（谁撑起销量、谁撑起退货），并按统一规则识别 A/B 类问题 ASIN 及高退货小体量观察名单，为后续原因分析提供输入。

#### 输入

- 上游来源：
  - 4.1 输出的 `parent_summary`；
  - view\_return\_snapshot
- 输入参数：
  - `country`：站点/国家（如 `US`，`JP`）。
  - `fasin`：父 ASIN。
  - `start_date`：起始日期（含）。
  - `end_date`：结束日期（含）。
- 输入 JSON 结构示例：

```json
{
  "parent_summary": {
    "country": "US",
    "fasin": "B0BGHGXYJX",
    "start_date": "2025-08-01",
    "end_date": "2025-10-31",
    "units_sold": 5057,
    "units_returned": 618,
    "return_rate": 0.122
  },
  "view_return_snapshot": [
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-04",
		"units_sold" : 8,
		"units_returned" : 8
	},
	{
		"country" : "US",
		"fasin" : "B0BGHGXYJX",
		"asin" : "B0BGHH2L23",
		"snapshot_date" : "2025-11-02",
		"units_sold" : 19,
		"units_returned" : 8
	}
 ]
}
```

#### 逻辑

1. 筛选条件：
   - `country = 输入.country`；
   - `fasin = 输入.fasin`；
   - `start_date ≤ snapshot_date ≤ end_date`。
2. 聚合维度：
   - `group by country, fasin, asin`。
3. 指标计算：
   - `units_sold_asin = sum(units_sold)`；
   - `units_returned_asin = sum(units_returned)`；
   - `return_rate_asin = units_returned_asin / units_sold_asin`；
   - 从 `parent_summary` 获取：
     - `total_units_sold_parent = parent_summary.units_sold`；
     - `total_units_returned_parent = parent_summary.units_returned`；
     - `R_parent = parent_summary.return_rate`；
   - 结构占比：
     - `sales_share = units_sold_asin / total_units_sold_parent`；
     - `returns_share = units_returned_asin / total_units_returned_parent`。
4. A/B 类问题 ASIN 识别规则：

   - 设：
     - `R_parent = parent_summary.return_rate`（父体整体退货率）；
     - `R_warn = 0.10`（类目退货警戒线，默认值）；
     - `R_high_B = max(R_parent, R_warn) + 0.02`（高退货阈值，默认值）。

   - **类 A：主战场 ASIN（Main Battlefield）**  
     满足以下任一条件即为类 A：
     - `sales_share ≥ 0.10`（销量贡献占比阈值，默认值）
     - 或 `returns_share ≥ 0.10`（退货贡献占比阈值，默认值）

     > 说明：类 A 不要求退货率高于父体，重点强调其对整体销量/退货盘子的贡献度，是**无论健康与否都需要重点关注的主战场款**。

   - **类 B：高退货问题 ASIN（High Return Problem）**  
     同时满足以下全部条件即为类 B：

     1. 退货率显著高于父体/警戒线：  
        `return_rate_asin ≥ R_high_B`。

     2. 退货量有一定体量：  
        `units_returned_asin ≥ 10`（过滤卖 3 退 2 这类极端偶然情况，默认值）。

     3. 对盘子有一定权重（排除体量很小的小透明）：  
        `sales_share > 0.05` **或** `returns_share > 0.05`（结构占比阈值，默认值）。  
        仅当 `sales_share ≤ 0.05` 且 `returns_share ≤ 0.05` 时，视作“小体量可暂不优先治理”的款式。

   - 对于满足 B 类退货率阈值和退货量阈值，但 `sales_share ≤ 0.05` 且 `returns_share ≤ 0.05` 的 ASIN：
     - 标记为 `high_return_watchlist = true`（高退货小体量观察名单）；
     - 不纳入正式 A/B 问题 ASIN 主清单。

5. 子 ASIN 结构表：
   - 在完成上述指标计算与 A/B 类问题 ASIN 识别后，将所有子 ASIN 的聚合结果（含 `problem_class`、`high_return_watchlist` 等标记字段）合并为一张结构表；
   - 为了便于业务同学阅读理解，在结构表展示层增加中文标签字段：
     - `problem_class` 作为内部分类编码，取值仅为 `"A"`、`"B"` 或 `null`，用于数据库查询与下游程序逻辑；
     - `problem_class_label_cn` 作为展示字段：
       - 当 `problem_class = "A"` 时，显示为 `"主战场款"`；
       - 当 `problem_class = "B"` 时，显示为 `"高退货问题款"`；
       - 当 `problem_class = null` 时，显示为空字符串或 `"—"`；
     - 报告中的表使用 `problem_class_label_cn` 这一中文字段作为列头展示，而不是直接展示 A/B 编码。
   - 按 `returns_share` 降序排序（退货占比越高的 ASIN 越靠前），可配置是否仅展示 Top N（默认 N=10），用于突出对整体退货影响最大的款式；
   - 该表为“结构视图 + 问题 ASIN 清单”的功能，无需额外维护独立的问题 ASIN 清单表。

#### 输出

- 输出给：下游 4.3 问题 ASIN 核心原因计算，需要 `problem_class` 与问题 ASIN清单；
- 输出 JSON 结构示例：

```json
{
  "asin_structure": [
    {
      "country": "US",
      "fasin": "B0BGHGXYJX",
      "asin": "B0BGHH2L23",
      "start_date": "2025-08-01",
      "end_date": "2025-10-31",
      "units_sold": 11302,
      "units_returned": 1140,
      "return_rate": 0.101,
      "sales_share": 0.563,
      "returns_share": 0.502,
      "problem_class": "A",
      "problem_class_label_cn": "主战场款",
      "high_return_watchlist": false
    }
  ]
}
```

---

### 4.3 问题 ASIN 核心原因计算

> 目标：基于 4.2 中识别出的 A/B 类问题 ASIN 清单，在指定国家/站点与时间范围内，分别为每个问题 ASIN 找到其退货的核心原因（二级标签维度），并输出标准化 JSON，遵循二八原则或 Top1 原则聚焦主要问题。

#### 输入

- 上游来源：
  - 4.2 输出的 `asin_structure`（包含 `problem_class`、`high_return_watchlist` 等）；
  - view\_return\_fact\_details
- 输入参数：
  - `country`：站点/国家（如 `US`，`JP`）。
  - `fasin`：父 ASIN。
  - `start_date`：起始日期（含）。
  - `end_date`：结束日期（含）。
- 输入 JSON 结构示例：

```json
{
  "asin_structure": [
    {
      "country": "US",
      "fasin": "B0BGHGXYJX",
      "asin": "B0BGHH2L23",
      "start_date": "2025-08-01",
      "end_date": "2025-10-31",
      "units_sold": 11302,
      "units_returned": 1140,
      "return_rate": 0.101,
      "sales_share": 0.563,
      "returns_share": 0.502,
      "problem_class": "A",
      "problem_class_label_cn": "主战场款",
      "high_return_watchlist": false
    }
  ],
  "view_return_fact_details": [
    {
      "country": "US",
      "fasin": "B0BGHGXYJX",
      "asin": "B0BGHH2L23",
      "review_id": "R3GDDPAC4WALFE",
      "review_source": 2,
      "review_date": "2025-09-21 00:00:00",
      "tag_code": "INSTALL_COMPLEX",
      "review_en": "Not what I expected. Needed to be put together. Flimsy",
      "review_cn": "不符合预期。需要组装。不结实",
      "sentiment": -1,
      "tag_name_cn": "安装\/组装复杂（耗时高）",
      "evidence": "Needed to be put together",
      "created_at": "2025-11-17 06:45:47",
      "updated_at": "2025-11-17 06:45:47"
    }
  ]
}
```

#### 逻辑

1. 构建问题 ASIN 清单：
   - 从 `asin_structure` 中筛选所有 `problem_class = "A"` 或 `"B"` 的记录，形成 `problem_asin_list`；

2. 在打标事实表 `view_return_fact_details` 中筛选：
   - `country = 输入.country`；
   - `fasin = 输入.fasin`；
   - `review_source = 0`（仅退货留言）；
   - `start_date ≤ review_date ≤ end_date`；
   - `asin ∈ problem_asin_list`。

3. 对于 `problem_asin_list` 中的每一个 ASIN（按 `country + fasin + asin` 粒度）：

   1. 统计该 ASIN 的退货文本样本总数：
      - `N_events_asin = count(distinct review_id where asin = X)`。

   2. 在该 ASIN 内按 `tag_code` 聚合：
      - `event_count_tag_asin = count(distinct review_id where asin = X and tag_code = Y)`；
      - `event_coverage_tag_asin = event_count_tag_asin / N_events_asin`。

   3. 样本置信度评估：
      - 为每个问题 ASIN 计算文本样本相关指标：
        - `text_sample_count = N_events_asin`（该 ASIN 在当前站点 + 时间范围内的退货留言事件数）；
        - 从 `asin_structure` 中获取该 ASIN 在同一站点 + 时间范围内的退货量：`units_returned_asin`；
        - `text_coverage = text_sample_count / units_returned_asin`（留言率，若分母为 0 则置为 0）。
      - 基于 `text_sample_count` 与 `text_coverage` 打标样本置信度等级：
        - 高置信（`high`）：`text_sample_count ≥ 30` 且 `text_coverage ≥ 0.10`；
        - 中置信（`medium`）：`15 ≤ text_sample_count < 30` 且 `text_coverage ≥ 0.05`；
        - 低置信（`low`）：其他情况。
      - 额外生成布尔字段 `can_deep_dive_reasons`：
        - 当置信度为 `high` 或 `medium` 时标记为 `true`，表示可以在报告中对该 ASIN 做结构化原因拆解；
        - 当置信度为 `low` 时标记为 `false`，报告中仅做“问题画像/典型用户声音”展示，不做严肃占比结论。

   4. 排序与核心原因选取：
      - 对于 `can_deep_dive_reasons = true` 的 ASIN：
        - 按 `event_count_tag_asin` 降序；
        - 默认规则：从排序第一的标签开始，按 `event_coverage_tag_asin` 累加，直到累计覆盖率 ≥ `COVERAGE_THRESHOLD`（0.8，默认值），中途至少保留 1 个标签，最多保留 3 个标签；
        - 实际系统中通过配置项控制，便于不同品类/业务方对“核心原因”的口径调整。
      - 对于 `can_deep_dive_reasons = false` 的 ASIN：
        - 可以仅按 `event_count_tag_asin` 输出 Top1 标签作为“主诉问题”参考，不强制进行覆盖率累计与多标签核心原因集合选择。

#### 输出

- 输出 JSON 结构示例：

```json
{
  "problem_asin_reasons": [
    {
      "country": "US",
      "fasin": "B0BGHGXYJX",
      "asin": "B0BGHH2L23",
      "start_date": "2025-08-01",
      "end_date": "2025-10-31",
      "problem_class": "A",
      "problem_class_label_cn": "主战场款",
      "total_events": 40,
      "units_returned": 160,
      "text_coverage": 0.25,
      "reason_confidence_level": "high",
      "can_deep_dive_reasons": true,
      "core_reasons": [
        {
          "tag_code": "FIT_COMPAT",
          "tag_name_cn": "尺寸/兼容性不符",
          "event_count": 13,
          "event_coverage": 0.325,
          "is_primary": true
        },
        {
          "tag_code": "VALUE_WEAK",
          "tag_name_cn": "性价比差/不值这个价",
          "event_count": 8,
          "event_coverage": 0.200,
          "is_primary": false
        }
      ],
      "coverage_threshold": 0.8,
      "coverage_reached": 0.525
    }
  ]
}
```

> 说明：
> - `country` 与 `fasin` 始终保留，确保可在多站点、多父体场景下进行追溯与过滤；
> - `core_reasons` 为每个问题 ASIN 选出的 1~N 个核心二级原因标签；
> - `coverage_threshold` 为系统配置的目标覆盖率（默认值 0.8）；
> - `coverage_reached` 为核心原因集合在该 ASIN 文本样本中的实际累计覆盖率；
> - `text_coverage`、`reason_confidence_level` 与 `can_deep_dive_reasons` 用于样本置信度评估，指导报告中对不同 ASIN 采用“结构化原因拆解”或“定性画像”两种不同呈现深度。

---


（完）