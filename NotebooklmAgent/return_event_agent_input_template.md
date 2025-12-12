# [VOC_Returns_Report] Target ASIN: {{fasin}}
# Report Date: {{report_date}}

## 1. Narrative (叙事层 - 业务全景与战略解读)
**现状定调：**
本期父体整体退货率为 **{{parent_return_rate}}**，高于红线值 **{{benchmark_rate}}**，整体处于**{{status_description}}**状态。
**业务解读：**
当前策略应由“放量”转向“精细化运营”。重点在于同时对 **Class A (主战场款)** 进行精细优化以压降整体退货成本，并对 **Class B (高退货问题款)** 进行提能处理以消除隐患。
**战略建议：**
建议在保持品牌 {{brand_name}} 市场占有率的前提下，优先解决 {{main_asin}} 的 Listing 信息架构问题，并重点监测 {{problem_asin}} 的质量/做工反馈。

## 2. Statistics (统计层 - 数据概览与分层锁定)
* **Parent Overview (父体总览):**
    * Total Units: {{total_units}} | Returns: {{total_returns}}
    * **Return Rate:** {{parent_return_rate}} (Status: {{status_level}})
* **ASIN Matrix (子体分层锁定):**
    * **Class A (主战场款):** {{asin_A}} | 销量占比: {{share_A}} | 退货率: {{rate_A}}
        * *特征：* 对整体指标影响最大，需小步优化。
    * **Class B (高退货问题款):** {{asin_B_list}} | 合计销量占比: {{share_B_total}} | 平均退货率: {{rate_B_avg}}
        * *特征：* "高退货、有分量"，是短期内排查和整改的重点对象。
    * **Watchlist (观察名单):** {{asin_C}} | 退货率: {{rate_C}} (高危但销量小)

## 3. Entities (实体层 - 深度归因、诊断与行动)
### [Deep Dive] ASIN: {{deep_dive_asin_1}} (Class A)
* **VOC Analysis (原声分析):**
    * **Top Reason:** `{{reason_1}}` (占比 {{coverage_1}})
    * **User Feedback:** "{{quote_1}}", "{{quote_2}}" (主要痛点：量了也不准、空间占用大)
* **Root Cause Diagnosis (根本原因 - Listing 缺陷):**
    * **Title (标题):** 关键尺寸信息滞后（移动端截断）；"Capacity Expandable" 语意冗余；使用场景（In/Over Sink）界定不清。
    * **Bullet Points (五点):** 兼容性“黑名单”被埋没；缺乏具体测量指导（未区分内径/外径）；营销词堆砌分散注意力。
* **Action Plan (行动建议):**
    * **Title Optimization:** 前置核心尺寸；明确适用场景；删除冗余修饰。
        * *Draft:* "{{optimized_title_draft}}"
    * **Bullet Points Optimization:**
        * Point 1: **{{bp_strategy_1}}** (购买前必读/尺寸检查) - 整合分散的尺寸信息。
        * Point 2: **{{bp_strategy_2}}** (简化营销) - 强调伸缩设计的实际利益点。

### [Deep Dive] ASIN: {{deep_dive_asin_2}} (Class B)
* **VOC Analysis:**
    * **Top Reason:** `{{reason_2}}` (占比 {{coverage_2}})
    * **Specific Risk:** 存在 **{{unique_risk}}** 问题（如：金属锋利、产品变形）。
    * **User Feedback:** "{{quote_risk_1}}", "{{quote_risk_2}}"

### [Deep Dive] ASIN: {{deep_dive_asin_3}} (Class B)
* **VOC Analysis:**
    * **Top Reason:** `{{reason_3}}` (占比 {{coverage_3}})
    * **User Feedback:** "{{quote_3}}" (如：公寓水槽不适配)