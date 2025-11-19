# 父体退货分析自动化系统 PRD（Python + LLM）

> 面向对象：数据/平台工程、后端、AI 平台、分析同学
>
> 目标：将当前已敲定的「退货分析报告终版框架」产品化，形成一套可复用、可批量跑的自动化分析流水线，由 Python 负责所有量化计算，由 LLM 在严格模板约束下负责结构化报告生成。

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

1. **一键生成退货分析报告**：输入父 ASIN + 时间范围，即可自动产出完整报告（Markdown/HTML/Text），可直接用于内部复盘。
2. **结构高度标准化**：所有父体的报告在结构、章节、表格维度完全统一，只通过参数/数据差异来体现差别，方便横向对比。
3. **角色分工清晰**：
   - Python 模块负责：**全部量化计算、聚合和排序**，输出结构化 JSON；
   - LLM 模块负责：在**固定报告模板 + 句式约束**下，填入数据并输出结构化文案总结，不再自行做数值运算。
4. **可扩展至其它父体/品类**：框架对父 ASIN/站点/品类透明，只要输入数据结构满足约定即可复用。

---

## 2. 范围 & 不在本期范围

### 2.1 本期范围（Phase 1）

- 站点：Amazon（不限站点，先从 US 起步）；
- 粒度：单个父 ASIN（可支持后续批量）；
- 时间粒度：支持指定起止日期（按日聚合或按月聚合均可，但本期报告本身不做时间趋势分析）；
- 分析逻辑：先看盘子，用父体 & 子 ASIN 的销量、退货量、退货率，搞清楚“整体退多少、主要是谁在退”；然后再看原因，基于二级退货标签做二八拆解，量化每个原因大概吃掉多少退货率；最后把Top 原因挂到具体子 ASIN 上，为后续产品 / 运营动作提供清晰靶点。
- 分析内容：
  - 0\. 分析背景 & 目标（模板自动填充）：明确本次分析的对象、时间范围、数据口径以及报告要回答的关键问题，为后续所有结论统一上下文和假设前提。

  - 1\. 现状 & 结构（父体健康度 + 子ASIN结构）：量化当前父体整体退货水平，并识别主要贡献销量和退货的核心子 ASIN，帮助快速锁定退货盘子的主战场和高风险款。

  - 2\. 父体层面原因拆解（二级退货标签二八分析 + 原因→子ASIN映射）：基于二级退货标签识别解释大部分退货的 Top 原因，量化各原因对整体退货率的贡献，并将其落到具体子 ASIN 组合，为后续产品 / 运营优化提供优先级依据。

### 2.2 不在本期范围（未来迭代）

- 不做**退货趋势**分析（按月/周的曲线）；
- 不做**干预前后效果对比**（例如页面优化前后、产品迭代前后）；
- 不做**自动生成行动计划/Backlog**，仅在报告中做定性描述；
- 暂不考虑多父体横向对比报告，先按单父体维度稳定产出。

---

## 3. 数据输入 & 口径约定

### 3.1 数据源一：销量 & 退货数据（必需）

**来源示例**：

- 内部对 Amazon 后台导出的退货/销量报表进行清洗后的表格

**要求字段（至少）：**

- `parent_asin`：父 ASIN
- `asin`：子 ASIN
- `date` 或 `month`：日期或月份
- `units_sold`：销量（件数）
- `units_returned`：退货量（件数）

**关键口径：**

- 退货率：`return_rate = units_returned / units_sold`
- 父体整体销量 = 所有子 ASIN 在时间范围内销量之和
- 父体整体退货量 = 所有子 ASIN 在时间范围内退货之和

### 3.2 数据源二：退货原因标签数据（必需）

#### 3.2.1 标签维表

文件示例：`return_dim_tag_xxx.json`

字段示例：

- `tag_code`：如 `FIT_COMPAT`, `NO_MATCH`, `VALUE_WEAK` 等
- `tag_name_cn`：二级标签中文名，如“尺寸/兼容性不符”“无合适标签”等
- （可选）`category_code` / `category_name`：一级标签信息

#### 3.2.2 打标事实表

文件示例：`return_fact_details_xxx.json`

字段示例：

- `review_id`：标识一条退货留言或评论文本（事实上的“事件 ID”）
- `review_source`：来源类型（约定：`0=退货留言`，`2=差评` 等）
- `parent_asin`：父 ASIN
- `asin`：子 ASIN（可能存在缺失）
- `review_date`：留言日期
- `tag_code`：标签编码，一条 `review_id` 可对应多条 `tag_code`

**原因分析口径：**

- 只使用 `review_source = 0` 的记录（纯退货留言）作为原因分析样本；
- 对每个 `review_id` 视为一条“退货事件”，可命中多个二级标签；
- 不强求样本覆盖所有退货订单，但要求**样本量足够用于判断原因结构**（建议 N≥50 条）。

### 3.3 全局分析口径

- 父体分析对象：`parent_asin` + `start_date` \~ `end_date` 共同确定一个分析盘子；
- 退货率为数量口径，不含金额；
- 原因拆解为样本口径，通过“事件覆盖率 × 整体退货率”估算各原因对退货率的贡献；
- 所有“占比”和“贡献”均以百分比形式展示（保留 1 位或 2 位小数，具体由产品定义）。

---

## 4. 功能需求概览

系统内部逻辑分为两大模块：

1. **Python 计算模块**（Data Engine）：

   - 接收原始数据 & 配置参数
   - 完成全部数值计算、聚合及排序
   - 输出结构化 JSON 结果

2. **LLM 报告生成模块**（Report Engine）：

   - 接收 Python 输出的 JSON + 固定 Markdown 模板
   - 仅在指定占位符位置生成总结性文字
   - 不做任何新的数值计算

下面按模块逐一定义。

---

## 5. Python 计算模块（F1）

> 目标：对给定父 ASIN + 时间范围，生成所有表格和指标所需的结构化数据。

### 5.1 F1-1 父体整体指标计算

**输入：**

- `parent_asin`
- `start_date`
- `end_date`

**逻辑：**

1. 从销量表筛选：`parent_asin`、日期在范围内；
2. 按父体聚合：
   - `total_units_sold_parent`
   - `total_units_returned_parent`
   - `return_rate_parent = total_units_returned_parent / total_units_sold_parent`

**输出 JSON 结构示例：**

```json
{
  "parent_summary": {
    "parent_asin": "B0BGHGXYJX",
    "start_date": "2025-01-01",
    "end_date": "2025-11-12",
    "units_sold": 20088,
    "units_returned": 2272,
    "return_rate": 0.113
  }
}
```

---

### 5.2 F1-2 子 ASIN 结构计算（表 1-2）

\*\*目标：\*\*输出“谁撑起销量，谁撑起退货”的结构表。

**逻辑：**

1. 在销量表中过滤 `parent_asin` & 日期范围；
2. 按 `asin` 聚合：
   - `units_sold_asin`
   - `units_returned_asin`
   - `return_rate_asin = units_returned_asin / units_sold_asin`
3. 使用父体汇总值计算：
   - `sales_share = units_sold_asin / total_units_sold_parent`
   - `returns_share = units_returned_asin / total_units_returned_parent`
4. 按 `units_returned_asin` 降序排序，取 Top N（默认 N=10，可配置）。

**输出 JSON 示例：**

```json
{
  "asin_structure": [
    {
      "asin": "B0BGHH2L23",
      "units_sold": 11302,
      "units_returned": 1140,
      "return_rate": 0.101,
      "sales_share": 0.563,
      "returns_share": 0.502
    },
    {
      "asin": "B0D4QLYM4C",
      "units_sold": 3771,
      "units_returned": 408,
      "return_rate": 0.108,
      "sales_share": 0.188,
      "returns_share": 0.180
    }
  ]
}
```

---

### 5.3 F1-3 父体二级标签分布（表 2-1）

\*\*目标：\*\*找出二级原因标签的二八结构（Top 原因）。

**逻辑：**

1. 从打标事实表中筛选：
   - `parent_asin` 匹配
   - `review_source = 0`
   - `review_date` 在时间范围内
2. 统计父体退货事件数：
   - `N_events = count(distinct review_id)`
3. 对每个 `tag_code`：
   - `event_count_tag = count(distinct review_id where tag_code = X)`
   - `event_coverage_tag = event_count_tag / N_events`
   - `return_rate_contribution = return_rate_parent * event_coverage_tag`
4. 左连接标签维表获取 `tag_name_cn`；
5. 按 `event_count_tag` 降序排序，取 Top K（默认 K=5，可配置）。

**输出 JSON 示例：**

```json
{
  "tag_summary": {
    "total_events": 137,
    "tags": [
      {
        "tag_code": "FIT_COMPAT",
        "tag_name_cn": "尺寸/兼容性不符",
        "event_count": 63,
        "event_coverage": 0.46,
        "return_rate_contribution": 0.052
      },
      {
        "tag_code": "NO_MATCH",
        "tag_name_cn": "无合适标签",
        "event_count": 50,
        "event_coverage": 0.365,
        "return_rate_contribution": 0.041
      }
    ]
  }
}
```

---

### 5.4 F1-4 二级原因 → 子 ASIN 映射

\*\*目标：\*\*对每个 Top 二级原因，找出对应的“问题子 ASIN”。

**逻辑（针对每个 Top 标签 ************************************************tag\_code************************************************）：**

1. 在打标事实表中筛选当前 `tag_code`，得到子集 S（包含 review\_id 与 asin）；
2. 对 S 按 `asin` 聚合：
   - `label_events_asin = count(distinct review_id)`
3. 将 `asin` 与销量表 join：
   - 取出 `units_sold_asin`、`units_returned_asin`、`return_rate_asin`
4. 计算：
   - `share_in_tag = label_events_asin / total_events_for_tag`
   - （可选）`share_in_asin_issues = label_events_asin / all_events_for_asin`（该 ASIN 所有标签事件中该标签占比）
5. 按 `label_events_asin` 降序排序，取 Top M（默认 M=5）。

**输出 JSON 示例：**

```json
{
  "tag_asin_mapping": {
    "FIT_COMPAT": {
      "tag_code": "FIT_COMPAT",
      "tag_name_cn": "尺寸/兼容性不符",
      "total_events": 63,
      "asins": [
        {
          "asin": "B0BGHH2L23",
          "units_sold": 11302,
          "units_returned": 1140,
          "return_rate": 0.101,
          "label_events": 22,
          "share_in_tag": 0.301,
          "share_in_asin_issues": 0.319
        },
        {
          "asin": "B0D4QLYM4C",
          "units_sold": 3771,
          "units_returned": 408,
          "return_rate": 0.108,
          "label_events": 20,
          "share_in_tag": 0.274,
          "share_in_asin_issues": 0.488
        }
      ]
    },
    "NO_MATCH": {
      "tag_code": "NO_MATCH",
      "tag_name_cn": "无合适标签",
      "total_events": 50,
      "asins": [
        {
          "asin": "B0BGHH2L23",
          "units_sold": 11302,
          "units_returned": 1140,
          "return_rate": 0.101,
          "label_events": 26,
          "share_in_tag": 0.51,
          "share_in_asin_issues": 0.377
        }
      ]
    }
  }
}
```

---

## 6. LLM 报告生成模块（F2）

> 核心要求：**结构模板固定 + 文本占位符受控**，LLM 只在少数位置输出总结性文字，不做数值计算。

### 6.1 报告结构模板（Markdown）

LLM 必须遵守以下固定结构。代码侧通过模板字符串 + 占位符拼接后，交给 LLM 填写。

> 提示：以下 `{{...}}` 为占位符，由代码或 LLM 替换。

```markdown
# 退货分析报告（{{SITE}}，父 ASIN：{{PARENT_ASIN}}）

## 0. 分析背景 & 目标

### 0.1 分析范围
- 站点：{{SITE}}
- 父 ASIN：{{PARENT_ASIN}}
- 子体范围：{{CHILD_SCOPE}}
- 时间范围：{{DATE_RANGE}}

### 0.2 数据说明
- 销量 & 退货数据来源：{{DATA_SOURCE_SALES}}
- 退货标签数据来源：{{DATA_SOURCE_TAG}}
- 原因分析样本口径：仅使用 review_source = 0 的退货留言；每条退货可命中多个二级标签。

### 0.3 分析目标
1. 看清在 {{DATE_RANGE}} 内父体 {{PARENT_ASIN}} 的整体退货水平，以及主要贡献退货的子 ASIN 结构。
2. 基于二级退货标签，找出解释退货盘子的 Top 原因，并用二八原则聚焦 20% 的原因覆盖 80% 的问题。
3. 量化各关键原因对整体退货率的大致贡献，并标记出需优先关注的「原因 × 子 ASIN」组合，为产品 / 运营优化提供依据。

---

## 1. 现状 & 结构

### 1.1 父体整体退货健康度

表 1-1 父体整体表现：

| 指标       | 数值        |
|------------|-------------|
| 累计销量   | {{PARENT_UNITS_SOLD}} |
| 累计退货量 | {{PARENT_UNITS_RETURNED}} |
| 整体退货率 | {{PARENT_RETURN_RATE_PCT}} |

{{SUMMARY_1_1}}

### 1.2 子 ASIN 结构：谁撑起销量，谁撑起退货

表 1-2 子 ASIN 结构（按退货量排序）：

{{ASIN_TABLE}}

{{SUMMARY_1_2}}

---

## 2. 父体层面原因拆解

### 2.1 父体二级原因标签分布（Top 标签）

表 2-1 父体二级原因标签分布：

{{TAG_TABLE}}

{{SUMMARY_2_1}}

### 2.2 Top 原因 → 问题子 ASIN 映射

#### 2.2.1 {{TOP1_TAG_NAME}} 对应的主要子 ASIN

表 2-2 {{TOP1_TAG_NAME}} 对应主要子 ASIN：

{{TOP1_TAG_ASIN_TABLE}}

{{SUMMARY_2_2_1}}

#### 2.2.2 {{TOP2_TAG_NAME}} 对应的主要子 ASIN

表 2-3 {{TOP2_TAG_NAME}} 对应主要子 ASIN：

{{TOP2_TAG_ASIN_TABLE}}

{{SUMMARY_2_2_2}}

...（按实际 Top 标签数量扩展小节）

---
```

> 工程要求：
>
> - 所有标题、表头、固定文案由代码直接写死，不允许 LLM 更改；
> - LLM 只负责填充：`SUMMARY_1_1` / `SUMMARY_1_2` / `SUMMARY_2_1` / `SUMMARY_2_2_x` ；
> - 表格数据（ASIN\_TABLE / TAG\_TABLE / TAG\_ASIN\_TABLE）可以由代码生成 Markdown，也可以由 LLM 按 JSON 渲染，但表头字段名必须固定。

### 6.2 LLM 输入格式

**LLM 的输入包含三个部分：**

1. **系统提示（System Prompt）**：明确角色和约束，例如：

   - 你是退货分析报告生成器；
   - 必须遵守给定的 Markdown 模板结构；
   - 不得修改任何标题和表头；
   - 只在指定占位符处输出总结文字。

2. **用户提示（User Prompt）**，包含：

   - Python 输出的 JSON 数据：`parent_summary` / `asin_structure` / `tag_summary` / `tag_asin_mapping`
   - 报告模板字符串（包含占位符）
   - 每个 `SUMMARY_xxx` 的句式约束说明

3. **模型输出**：完整的 Markdown 文本，模板结构不变，占位符被内容替换。

### 6.3 对总结占位符的句式约束

为保证不同父体间报告风格和结构的一致性，对各 `SUMMARY_xxx` 制定**统一的句式模板**：

#### 6.3.1 `SUMMARY_1_1`（父体整体小结）

- 句数：1–2 句；
- 必须包含：累计销量、累计退货量、整体退货率；
- 推荐句式示例：

> 在 {{DATE\_RANGE}} 期间，父体 {{PARENT\_ASIN}} 在 {{SITE}} 的累计销量为 **{{PARENT\_UNITS\_SOLD}} 件**，累计退货量 **{{PARENT\_UNITS\_RETURNED}} 件**，整体退货率约为 **{{PARENT\_RETURN\_RATE\_PCT}}**。
>
> 整体来看，该退货率处于【偏高/中等/偏低】水平，为后续的原因拆解提供了盘子基准。

（偏高/中等/偏低 可由简单规则自动判断，也可由 LLM 根据阈值判断。）

#### 6.3.2 `SUMMARY_1_2`（子 ASIN 结构小结）

- 句数：2–3 句；
- 应提到：
  - Top1 \~ Top2 子 ASIN 对父体销量/退货的贡献；
  - 是否存在退货率明显高于平均的大坑位。
- 推荐句式示例：

> 从子 ASIN 结构看，【{{TOP1\_ASIN}}】和【{{TOP2\_ASIN}}】是当前的主力款，合计贡献了约 **{{TOP12\_SALES\_SHARE}}** 的销量和 **{{TOP12\_RETURNS\_SHARE}}** 的退货量。
>
> 其中，【{{HIGH\_RISK\_ASIN}}】等少数款式退货率明显高于父体平均，后续在放量前需要重点关注其原因结构。

#### 6.3.3 `SUMMARY_2_1`（父体原因二八小结）

- 句数：2–3 句；
- 必须提到：Top1 / Top2 标签的事件覆盖率和退货率贡献；
- 推荐句式示例：

> 在所有已打标的退货事件中，「{{TOP1\_TAG\_NAME}}」和「{{TOP2\_TAG\_NAME}}」是最主要的两个原因，分别覆盖了约 **{{TOP1\_COVERAGE\_PCT}}** 和 **{{TOP2\_COVERAGE\_PCT}}** 的退货事件。
>
> 按整体退货率 {{PARENT\_RETURN\_RATE\_PCT}} 估算，这两类原因合计大约吃掉了 **{{TOP12\_RETURN\_LOSS\_PCT}}** 的退货率，已经解释了大部分退货损失。

#### 6.3.4 `SUMMARY_2_2_x`（某个原因下的问题 ASIN 小结）

- 句数：2–3 句；
- 必须提到：
  - 该原因主要集中在哪 1–2 个子 ASIN 上；
  - 是否存在“高退货率小盘子”的风险款。
- 推荐句式示例：

> 在所有「{{TAG\_NAME}}」相关的退货事件中，【{{MAIN\_ASIN\_1}}】和【{{MAIN\_ASIN\_2}}】贡献了约 **{{MAIN\_ASIN\_SHARE\_PCT}}** 的事件，是这一原因的主要问题来源。
>
> 此外，【{{RISK\_ASIN}}】等小盘 ASIN 虽然销量占比不高，但退货率明显偏高，一旦放量可能放大该原因对父体整体退货率的影响。

### 6.4 LLM 禁止行为

在 PRD 中需明确：

- 不允许：

  - 修改或新增标题级别（如增加 3. 行动建议）；
  - 删除任何已有章节或表头；
  - 自行发明新的数值或对 JSON 数值进行复杂运算；
  - 输出与模板结构不一致的 Markdown（例如增加多余的大标题）。

- 允许：

  - 对总结句式中的逻辑连接词、形容词做轻微调整（例如“整体来看/总体而言”）；
  - 在合理范围内调整句子顺序，使语义通顺。

---

## 7. 非功能需求

- **一致性**：不同父体、不同时间范围的报告，在章节结构、表头、总结句式风格上高度统一；
- **可移植性**：支持后续扩展到其它 Amazon 站点或完全不同品类，只需更换数据输入；
- **可配置性**：
  - 子 ASIN Top N 数量可配置（默认 10）；
  - 二级标签 Top K 数量可配置（默认 3–5）。
- **可追溯性**：报告中的所有数值可追溯到 Python 输出 JSON，不依赖 LLM 自算。

---

## 8. 验收标准

1. 在测试环境中，给定一个真实父 ASIN + 时间范围，系统能自动生成一份完整的 Markdown 报告，结构与本 PRD 模板一致；
2. 报告中的所有数字（包括退货率、占比、Top 排序）均可在 Python 输出 JSON 中找到对应来源；
3. 多次对同一父 ASIN/时间范围重复生成报告，结构完全一致，只在总结性文字中存在轻微同义表达差异；
4. 更换父 ASIN 后，无需修改 LLM 模板和逻辑，即可产出结构相同的新报告。

---

（完）

