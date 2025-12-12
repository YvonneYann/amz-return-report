基于您上传的《退货分析报告_status.pdf》的逻辑结构，这“三层输出法”实际上是对报告中不同颗粒度信息的结构化映射。

以下是这三层的具体定义及其在 PDF 报告中的对应来源：

### 1. Narrative (叙事层) —— 业务全景与战略解读
**定义：**
这是对数据进行定性判断的“指挥层”。它不只罗列数字，而是负责“翻译”数字背后的业务含义（如：状态是安全还是危险？策略是进攻还是防守？）。
* **核心功能：** 设定报告的基调（Tone）和紧迫感（Urgency）。
* [cite_start]**PDF 对应内容：** 对应报告中的 **“业务解读”** 板块 [cite: 13]。
    * [cite_start]例如报告中判断当前状态为“高于红线10%” [cite: 14]。
    * [cite_start]提出的战略方向是由“放量”转向“精细化优化” [cite: 15]。
    * [cite_start]明确了优先任务是“压降整体退货率” [cite: 16]。

### 2. Statistics (统计层) —— 数据概览与分层锁定
**定义：**
这是提供客观证据的“验证层”。它通过聚合数据（销量、退货量、退货率）来支撑叙事层的结论，并负责将大盘数据拆解为不同类别的 ASIN 矩阵（Class A/B/Watchlist），以便锁定问题范围。
* **核心功能：** 建立数学围栏，防止结论主观化，并进行问题分级。
* [cite_start]**PDF 对应内容：** 对应报告中的 **数据概览** 和 **“锁定问题子体”** 板块 [cite: 17]。
    * [cite_start]父体数据：销量 1,537，退货 233，退货率 15.2% [cite: 6, 11, 12]。
    * [cite_start]**Class A (主战场款):** 销量占比 85.5% 的 B0CSMK924R [cite: 18, 24, 25]。
    * [cite_start]**Class B (高退货问题款):** 销量占比 12.4% 的 B0DHRRP7V1 [cite: 27, 30, 32]。
    * [cite_start]**Watchlist (观察名单):** 销量虽小但退货率达 26.3% 的 B0D737GFTW [cite: 46, 49]。

### 3. Entities (实体层) —— 深度归因、诊断与行动
**定义：**
这是解决具体问题的“执行层”。它深入到具体的 SKU/ASIN 级别，结合 VOC（用户之声）挖掘根本原因（Root Cause），并针对 Listing 的具体模块（标题、五点）提出可落地的行动方案（Action Plan）。
* **核心功能：** 颗粒度极细的诊断，区分不同变体的具体痛点（如：有的尺寸不对，有的质量差），并给出改写建议。
* [cite_start]**PDF 对应内容：** 对应报告中的 **“拆解退货原因”** [cite: 52] [cite_start]和 **“AI 智能归因诊断”** 板块 [cite: 67]。
    * [cite_start]**归因 (Why):** 明确指出 B0CSMK924R 的主因是“尺寸/兼容性不符” [cite: 58][cite_start]，B0DHRRP7V1 存在“做工/形状”问题 [cite: 111]。
    * [cite_start]**证据 (Evidence):** 引用用户原话，如 "This did not fit in my sink even though I had measured my sink" [cite: 63]。
    * [cite_start]**诊断 (Diagnosis):** 分析标题关键尺寸滞后 [cite: 75][cite_start]，五点描述中兼容性警告被埋没 [cite: 80]。
    * [cite_start]**行动 (Action):** 给出具体的标题优化草稿 [cite: 87] [cite_start]和五点描述重写建议 [cite: 92]。