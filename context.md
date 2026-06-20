---
title: "BGP 知识库数据准备技术方案"
document_type: "项目上下文"
purpose: "记录 BGP 知识库的建设目标、范围、架构、数据模型和交付标准，作为项目整理与后续执行的总上下文。"
scope: "项目级规划与约束说明"
status: "现行参考"
last_reviewed: "2026-06-19"
---
下面给你一版**严格限定在“BGP 知识库数据准备”范围内**的技术方案。
不讲 RAG 检索、不讲 Agent 工作流、不结合你的具体项目系统，只做一件事：

> **把 BGP 相关知识先整理成一个结构清楚、可追溯、可维护、可扩展的领域知识库数据底座。**

---

# 一、建设目标

这一阶段的目标不是“问答”，也不是“智能分析”，而是先把 BGP 领域知识做成标准化数据资产。

最终你应该得到这些东西：

```text
BGP 原始资料库
BGP 清洗文本库
BGP 知识片段库
BGP 概念实体库
BGP 异常类型库
BGP 数据源说明库
BGP 证据字段库
BGP 案例库
BGP 术语表
BGP 关系表
质量检查报告
```

核心目标可以概括为：

```text
原始资料
  -> 清洗文本
  -> 知识片段
  -> 结构化实体
  -> 关系组织
  -> 质量评估
```

注意，这里还没有进入 RAG 阶段。
这一阶段只解决：

```text
知识从哪里来？
知识如何清洗？
知识如何拆分？
知识如何分类？
知识如何结构化？
知识如何追溯？
知识如何更新？
```

---

# 二、知识库范围：先做 BGP 核心知识，不要泛化

你现在不要一开始就做“网络安全知识库”“威胁检测知识库”“Agent 知识库”。范围太大，很容易失控。

第一版只做 **BGP 领域知识库**，建议分成 8 类。

## 1. BGP 基础概念知识

这一类用于解释 BGP 的基本对象和术语。

包括：

```text
BGP
AS / ASN
Prefix
IP Prefix
Origin AS
AS_PATH
Next Hop
RIB
FIB
BGP Update
Announcement
Withdrawal
Route Collector
VP / Vantage Point
Peer
Collector
RouteViews
RIPE RIS
MRT 格式
```

BEAR 论文中明确使用 BGPStream 从 BGP update message 和 RIB records 中提取 AS path，并构造事件相关数据；同时说明 RIPE RIS collector 会连接多个 peer，收集 BGP updates，并定期抽取 RIB 快照。
所以第一批概念必须围绕 **RIB / update / AS path / prefix / collector / peer / VP** 建立。

---

## 2. BGP 路由机制知识

这一类用于解释 BGP 路由如何传播、如何形成路径。

包括：

```text
路径向量协议
路由通告传播
AS_PATH prepend
路由选择
路由策略
eBGP / iBGP
Provider / Customer / Peer
P2C / C2P / P2P
Valley-free 原则
AS 关系图
AS routing role
```

语义路由异常检测论文指出，BGP 是一种 path-vector routing protocol，会维护 AS-level path information，并随着 BGP announcements 传播而更新；同时，AS business relationship 会影响 AS 如何处理从邻居收到的路由以及如何继续传播路由。
因此，你的知识库里不能只存“AS_PATH 是路径”，还要存：

```text
AS_PATH 为什么会变化
AS 关系为什么影响路由传播
route leak 为什么和 valley-free 有关
provider/customer/peer 关系如何影响异常判断
```

---

## 3. BGP 数据源知识

这一类用于解释 BGP 数据从哪里来、格式是什么、有什么限制。

包括：

```text
RouteViews
RIPE RIS
BGPStream
RIB dump
Update dump
MRT
Collector
Peer
Vantage Point
CAIDA AS Relationship
CAIDA ASRank
RIPEstat
RPKI / ROA
IRR / WHOIS / RDAP
PeeringDB
```

BEAR 中的数据组织方式非常适合作为你知识库的数据源说明模板：它用 RIB records 构造历史路径，用 update messages 构造事件前后路径，并把结果保存为 `{collector:{peer:[AS path]}}` 形式的 JSON 数据。
BGPShield 也强调多源 AS 信息，包括 CAIDA AS Relationship、ASRank 和 AS Organization 数据，并把这些信息转化为 AS 描述文本。

所以这一层不仅要写“RouteViews 是什么”，还要写清楚：

```text
数据粒度是什么？
时间分辨率是什么？
主要字段是什么？
适合回答什么问题？
不适合回答什么问题？
能作为强证据还是辅助证据？
```

---

## 4. BGP 异常类型知识

这一类用于定义不同异常类型及其边界。

第一版建议只做：

```text
Prefix Hijack
Subprefix Hijack
Path Hijack / Path Manipulation
Route Leak
MOAS
Prefix Outage
AS Outage
Country-level Outage
Origin Change
ROA Misconfiguration
Weak Path Tampering
```

语义路由异常检测论文把 BGP anomalies 分成 hijacking 和 route leak，并说明 hijacking 可表现为错误宣称 prefix ownership，或者宣布伪造且更优的路径；route leak 则是把路由传播给不该传播的 AS。
BGPShield 的评估中也把异常模式细化为 Origin Change、Route Leaks、Path Manipulation、ROA Misconfiguration、Weak Path Tampering 等类型。

因此，异常类型不要只写“劫持/泄露”，而要做成结构化条目。

---

## 5. BGP 检测与证据知识

这一类不是让你实现检测算法，而是整理“判断某类异常需要哪些证据”。

例如：

```text
prefix hijack 需要哪些证据
subprefix hijack 需要哪些证据
route leak 需要哪些证据
outage 需要哪些证据
MOAS 如何区分正常多源和异常多源
RPKI 能证明什么、不能证明什么
AS_PATH 变化能证明什么、不能证明什么
collector 缺失会造成什么误判
```

BEAR 的事件解释任务要求根据事件 prefix 和时间，从 BGP 数据中构造 historical AS paths、before-event AS paths、after-event AS paths，再比较路径变化来解释异常。
这说明证据知识至少要覆盖：

```text
历史路径
事件前路径
事件后路径
origin AS 是否变化
destination AS 是否变化
是否出现新 sub-prefix
collector / peer 观察范围
AS_PATH 差异
```

---

## 6. BGP 误报与边界知识

这一类非常重要。没有误报知识，后续模型很容易过度解释。

包括：

```text
VP 局部观测异常
collector 故障或缺失
短时 route flap
合法流量工程
合法 MOAS
anycast
RPKI 部署不完整
AS relationship 数据错误
AS_PATH prepend 导致的路径差异
历史路径不稳定
单个 collector 视角不足
```

BEAM 论文中提到，BGP route announcement 数据可能包含未揭示异常带来的噪声，同时 AS routing role 会随互联网路由和拓扑演化而变化。
所以知识库里必须有“证据边界”和“误报模式”，不能只存定义。

---

## 7. BGP 论文方法知识

这一类用于整理重要论文的方法，而不是全文堆进去。

第一批建议整理：

```text
BEAR
BEAM / Learning with Semantics
BGPShield
ASwatch
BGP2Vec / AP2Vec
RPKI / ROV 相关资料
Route leak 检测相关论文
BGP hijack 检测相关论文
```

但每篇论文不要只做摘要，要抽取成固定结构：

```text
论文名称
研究问题
输入数据
核心概念
方法流程
输出结果
适用异常类型
依赖数据源
优点
局限
可沉淀到知识库的概念
可沉淀到知识库的证据模板
```

例如 BEAR 不是普通检测论文，它主要解决“BGP anomaly event explanation”，重点是把 tabular BGP data 转成 textual descriptions，再生成事件报告。
BGPShield 不是普通 embedding 论文，它把 AS 多源信息构造成 LLM-readable description，用于捕获 AS 的 behavioral semantics 和 routing policy rationale。

---

## 8. BGP 历史案例知识

这一类用于沉淀真实事件。

包括：

```text
事件名称
事件时间
异常类型
受影响 prefix
受害 AS
异常 AS / 泄露 AS / 劫持 AS
事件描述
观测来源
证据
影响范围
处置过程
参考链接
是否已确认
```

BEAR 构造数据集时收集了 10 个公开、文档完整的 BGP anomaly events，并记录 event type、relevant ASes、target IP、start time、end time、event name 和 event description link。
这可以直接作为你历史案例库的字段参考。

---

# 三、总体技术架构

建议采用六层结构。

```text
第 1 层：原始资料层
第 2 层：解析清洗层
第 3 层：知识片段层
第 4 层：结构化实体层
第 5 层：关系组织层
第 6 层：质量治理层
```

当前阶段不要引入复杂系统，先用文件化工程实现即可。

---

# 四、目录结构设计

建议先建立一个独立目录：

```text
bgp_knowledge_base/
├── README.md
├── config/
│   ├── source_types.yaml
│   ├── topic_taxonomy.yaml
│   ├── entity_types.yaml
│   └── quality_rules.yaml
│
├── raw/
│   ├── standards/
│   ├── papers/
│   ├── data_docs/
│   ├── tools_docs/
│   ├── cases/
│   └── notes/
│
├── parsed/
│   ├── standards/
│   ├── papers/
│   ├── data_docs/
│   └── cases/
│
├── cleaned/
│   ├── standards/
│   ├── papers/
│   ├── data_docs/
│   └── cases/
│
├── chunks/
│   ├── bgp_chunks.jsonl
│   ├── paper_chunks.jsonl
│   ├── standard_chunks.jsonl
│   └── case_chunks.jsonl
│
├── entities/
│   ├── bgp_concepts.jsonl
│   ├── routing_mechanisms.jsonl
│   ├── anomaly_types.jsonl
│   ├── data_sources.jsonl
│   ├── data_fields.jsonl
│   ├── evidence_templates.jsonl
│   ├── false_positive_patterns.jsonl
│   ├── papers.jsonl
│   └── cases.jsonl
│
├── relationships/
│   └── relationships.jsonl
│
├── schemas/
│   ├── source.schema.json
│   ├── chunk.schema.json
│   ├── concept.schema.json
│   ├── anomaly_type.schema.json
│   ├── data_source.schema.json
│   ├── evidence_template.schema.json
│   ├── paper.schema.json
│   └── case.schema.json
│
├── inventory/
│   └── sources.csv
│
├── reports/
│   ├── ingestion_report.md
│   ├── quality_report.md
│   └── coverage_report.md
│
└── scripts/
    ├── parse_documents.py
    ├── clean_text.py
    ├── build_chunks.py
    ├── extract_entities.py
    ├── build_relationships.py
    └── quality_check.py
```

这套结构的重点是：**原始资料、清洗文本、知识片段、结构化实体、关系、质量报告分开保存**。

不要把所有东西混在一个 `documents/` 目录里。

---

# 五、第一批资料清单

第一版不要贪多，建议先收 20～30 份资料。

## 1. 标准与协议类

```text
RFC 4271：BGP-4
RFC 6480：RPKI 架构
RFC 6811：BGP Prefix Origin Validation
RFC 8210：RPKI-Router Protocol
RFC 7908：Route Leak Problem Definition
RFC 9234：Route Leak Prevention and Detection Using Roles
```

这些资料用于建设：

```text
BGP 基础概念
RPKI / ROA / ROV
Route Leak 定义
BGP Roles
路径验证边界
```

---

## 2. 数据源文档类

```text
RouteViews documentation
RIPE RIS documentation
BGPStream documentation
CAIDA AS Relationship documentation
CAIDA ASRank documentation
RIPEstat API documentation
PeeringDB documentation
MANRS incident reports
APNIC blog / incident analysis
```

这些资料用于建设：

```text
数据源说明
字段说明
时间粒度
观测范围
证据可信度
数据局限性
```

---

## 3. 论文类

第一版建议整理：

```text
BEAR
Learning with Semantics / BEAM
BGPShield
ASwatch
BGP2Vec / AP2Vec
Route leak detection 相关论文
BGP hijack detection 相关论文
RPKI deployment / ROV measurement 相关论文
```

---

## 4. 案例类

第一版建议先选 5～10 个公开事件：

```text
Pakistan Telecom / YouTube Hijack
Indosat route leak
China Telecom route leak
Facebook 2021 outage
Vodafone Idea AS55410 route leak
CelerBridge BGP hijack
Cloudflare / BGP incident reports
MANRS documented incidents
Dyn historical BGP reports
```

案例不需要一开始很多，但每个案例要结构化。

---

# 六、元数据设计

所有资料必须先进入 `sources.csv`。
这是知识库建设的第一张表。

## 1. source inventory 字段

```csv
source_id,title,source_type,domain,authority,author,organization,publish_date,version,language,path,url,trust_level,review_status,ingest_date,notes
```

示例：

```csv
rfc4271,A Border Gateway Protocol 4,standard,BGP,IETF,Y. Rekhter et al.,IETF,2006-01,RFC4271,en,raw/standards/rfc4271.pdf,https://www.rfc-editor.org/rfc/rfc4271,high,approved,2026-06-08,BGP core standard
bear_2025,BEAR: BGP Event Analysis and Reporting,paper,BGP anomaly explanation,arXiv,Hanqing Li et al.,Northwestern/AWS,2025-06,v1,en,raw/papers/bear.pdf,,medium,pending,2026-06-08,LLM-based BGP event explanation
bgpshield_2025,BGPShield,paper,BGP anomaly detection,arXiv,Heng Zhao et al.,ZJU,2025-11,v1,en,raw/papers/bgpshield.pdf,,medium,pending,2026-06-08,LLM embeddings for AS semantics
```

## 2. source_type 分类

```yaml
standard:
  description: "RFC, IETF draft, protocol standard"
paper:
  description: "Academic paper"
data_doc:
  description: "Data source documentation"
tool_doc:
  description: "Tool documentation"
case_report:
  description: "BGP incident report"
blog:
  description: "Technical blog"
manual_note:
  description: "Human-written note"
```

## 3. trust_level 规则

```text
high:
  RFC / 官方文档 / 数据源官方说明

medium:
  顶会论文 / 可信研究机构报告 / MANRS / APNIC / Cloudflare 等技术报告

low:
  普通博客 / 二手资料 / 未验证案例

internal:
  自己整理的笔记，必须保留来源
```

---

# 七、BGP 主题分类体系

建议先设计 `topic_taxonomy.yaml`。

```yaml
BGP基础:
  - AS
  - ASN
  - Prefix
  - BGP Speaker
  - BGP Session
  - eBGP
  - iBGP

BGP消息与数据:
  - RIB
  - Update
  - Announcement
  - Withdrawal
  - MRT
  - BGPStream
  - RouteViews
  - RIPE RIS

路径与属性:
  - AS_PATH
  - Origin AS
  - NEXT_HOP
  - LOCAL_PREF
  - MED
  - COMMUNITY
  - AS_PATH Prepending

AS关系与路由策略:
  - Provider-Customer
  - Peer-Peer
  - Customer-Provider
  - Valley-free
  - Routing Policy
  - AS Routing Role
  - Customer Cone

BGP安全:
  - Prefix Hijack
  - Subprefix Hijack
  - Route Leak
  - Path Manipulation
  - MOAS
  - RPKI
  - ROA
  - ROV
  - BGPsec
  - ASPA

异常检测:
  - Origin Change
  - Path Change
  - Withdrawal Burst
  - Outage
  - Prefix Outage
  - AS Outage
  - Route Flap
  - False Positive

事件解释:
  - Evidence
  - Affected Prefix
  - Victim AS
  - Hijacker AS
  - Leaker AS
  - Collector Coverage
  - Before-After Path Change
```

每个 chunk 和每个实体都应该至少挂 1～3 个 topic。

---

# 八、文档解析与清洗方案

## 1. PDF 论文解析

论文类资料建议解析成 Markdown 或 JSON。

输出结构：

```json
{
  "doc_id": "bear_2025",
  "title": "BEAR: BGP Event Analysis and Reporting",
  "sections": [
    {
      "section_id": "1",
      "heading": "Introduction",
      "level": 1,
      "content": "...",
      "page_start": 1,
      "page_end": 2
    },
    {
      "section_id": "3.2",
      "heading": "Data Retrieval",
      "level": 2,
      "content": "...",
      "page_start": 4,
      "page_end": 5
    }
  ],
  "figures": [
    {
      "figure_id": "fig4",
      "caption": "An example of a BGP update message",
      "page": 4,
      "related_section": "3.2"
    }
  ]
}
```

论文解析时要重点保留：

```text
标题
作者
摘要
章节层级
图标题
表标题
算法流程
数据集说明
方法输入
方法输出
实验对象
局限性
```

不要把论文直接切成碎文本。
先恢复结构，再切分。

---

## 2. RFC / 标准解析

RFC 比论文更适合按 section 切分。

结构：

```json
{
  "doc_id": "rfc4271",
  "section": "5.1.2",
  "section_title": "AS_PATH",
  "content": "...",
  "topic": ["AS_PATH", "BGP Path Attribute"],
  "authority": "IETF"
}
```

RFC 处理重点：

```text
保留 section 编号
保留 MUST / SHOULD / MAY 等规范词
保留字段定义
保留协议行为
保留状态机或消息格式
```

---

## 3. 网页 / 技术报告解析

网页要清理：

```text
导航栏
广告
推荐阅读
页脚
评论区
无关链接
```

保留：

```text
标题
发布时间
作者
正文
图表说明
引用链接
事件时间线
关键证据
```

---

## 4. 表格和字段说明解析

数据源文档和 API 文档中经常有表格，不能直接转纯文本。

建议转成：

```json
{
  "table_id": "ripe_ris_fields",
  "source_doc": "ripe_ris_doc",
  "columns": [
    {
      "field": "timestamp",
      "meaning": "time when BGP message was observed",
      "type": "datetime",
      "notes": "UTC"
    },
    {
      "field": "peer_asn",
      "meaning": "ASN of peer connected to collector",
      "type": "integer"
    }
  ]
}
```

---

# 九、Chunk 设计

这一阶段的 chunk 不是为了向量检索，而是为了形成稳定的知识片段。

## 1. chunk 类型

建议分成 8 种：

```text
concept_definition
protocol_behavior
data_source_description
field_description
anomaly_definition
evidence_rule
paper_method
case_description
```

## 2. chunk schema

```json
{
  "chunk_id": "bear_2025_sec3_2_001",
  "doc_id": "bear_2025",
  "source_type": "paper",
  "title": "BEAR: BGP Event Analysis and Reporting",
  "section_path": ["III. Methodology", "B. Data Retrieval"],
  "page_start": 4,
  "page_end": 4,
  "chunk_type": "paper_method",
  "topics": ["BGPStream", "RIB", "Update", "AS_PATH"],
  "content": "After obtaining the target IP prefix and start time, BEAR uses BGPStream to retrieve AS path information from BGP update messages and RIB records...",
  "entities": ["BGPStream", "RIPE RIS", "RIB", "Update", "AS_PATH"],
  "source_ref": "BEAR.pdf:p4:III-B",
  "language": "en",
  "review_status": "pending"
}
```

## 3. chunk 长度建议

```text
概念定义：100～300 字
协议行为：300～800 字
论文方法：500～1200 字
案例描述：500～1500 字
字段说明：单字段或一组相关字段
```

## 4. 切分规则

```text
优先按章节切
章节过长再按自然段切
表格单独成 chunk
图注和图一起成 chunk
算法步骤单独成 chunk
案例时间线单独成 chunk
不要把定义和例子分开
不要把异常类型和证据条件分开
```

---

# 十、结构化实体设计

这是知识库的核心。
第一版至少建 8 类实体。

```text
BGPConcept
RoutingMechanism
AnomalyType
DataSource
DataField
EvidenceTemplate
PaperMethod
Case
```

---

## 1. BGPConcept

用于保存基础概念。

```json
{
  "id": "concept_as_path",
  "entity_type": "BGPConcept",
  "name": "AS_PATH",
  "aliases": ["AS path", "AS-level path"],
  "definition": "AS_PATH is the sequence of AS numbers that a BGP route announcement has traversed.",
  "category": "路径与属性",
  "related_terms": ["Origin AS", "BGP Update", "Prefix", "Route Announcement"],
  "common_misunderstandings": [
    "AS_PATH is not an IP-level traceroute path.",
    "The last AS in AS_PATH is usually the origin AS for the prefix."
  ],
  "source_refs": ["rfc4271", "bear_2025", "beam_2024"],
  "review_status": "approved"
}
```

---

## 2. RoutingMechanism

用于保存机制类知识。

```json
{
  "id": "mechanism_valley_free",
  "entity_type": "RoutingMechanism",
  "name": "Valley-free Routing",
  "definition": "Valley-free routing describes policy-compliant AS path propagation based on provider-customer and peer-peer relationships.",
  "used_for": ["Route Leak Detection", "Routing Policy Reasoning"],
  "depends_on": ["AS Relationship", "Provider-Customer", "Peer-Peer"],
  "evidence": ["AS relationship graph", "AS_PATH"],
  "limitations": [
    "Requires accurate AS relationship inference.",
    "Cannot fully capture hidden or complex routing policies."
  ],
  "source_refs": ["rfc7908", "beam_2024"]
}
```

---

## 3. AnomalyType

用于保存异常类型定义。

```json
{
  "id": "anomaly_prefix_hijack",
  "entity_type": "AnomalyType",
  "name": "Prefix Hijack",
  "category": "BGP Hijacking",
  "definition": "A prefix hijack occurs when an AS illegitimately announces reachability for an IP prefix it does not own.",
  "typical_signals": [
    "origin AS changes to an unauthorized AS",
    "new path appears with suspicious origin",
    "affected collectors observe changed AS_PATH"
  ],
  "required_evidence": [
    "target prefix",
    "historical origin AS",
    "event-time origin AS",
    "AS_PATH before event",
    "AS_PATH after event",
    "RPKI/ROA status if available",
    "collector/VP coverage"
  ],
  "possible_false_positives": [
    "legitimate MOAS",
    "prefix transfer",
    "ROA not updated",
    "anycast",
    "traffic engineering"
  ],
  "forbidden_claims_without_evidence": [
    "Do not claim malicious hijack solely from one collector observation.",
    "Do not claim prefix ownership without RPKI/WHOIS/IRR or authoritative evidence."
  ],
  "source_refs": ["rfc4271", "bear_2025", "beam_2024"]
}
```

---

## 4. DataSource

用于保存外部数据源说明。

```json
{
  "id": "datasource_routeviews",
  "entity_type": "DataSource",
  "name": "RouteViews",
  "category": "BGP collector",
  "description": "RouteViews collects BGP routing information from global peers and provides RIB and update data.",
  "data_objects": ["RIB dump", "Update dump", "MRT file"],
  "time_granularity": {
    "rib": "periodic snapshot",
    "update": "near-real-time update stream"
  },
  "suitable_for": [
    "AS_PATH reconstruction",
    "origin change observation",
    "prefix reachability analysis",
    "historical event analysis"
  ],
  "limitations": [
    "Visibility depends on collectors and peers.",
    "Absence of observation does not necessarily mean global absence.",
    "Collector outages may affect conclusions."
  ],
  "related_tools": ["BGPStream", "bgpdump"],
  "source_refs": ["routeviews_doc", "bear_2025", "bgpshield_2025"]
}
```

---

## 5. DataField

用于保存字段语义。

```json
{
  "id": "field_as_path",
  "entity_type": "DataField",
  "name": "as_path",
  "belongs_to": ["BGP Update", "RIB Record"],
  "type": "list[int]",
  "meaning": "Sequence of ASNs in the route announcement.",
  "used_for": [
    "origin AS identification",
    "path change comparison",
    "route leak analysis",
    "path manipulation analysis"
  ],
  "interpretation_rules": [
    "The last AS is usually the origin AS.",
    "Repeated ASNs may indicate AS path prepending.",
    "AS_SET should be treated carefully because it is unordered."
  ],
  "common_errors": [
    "Mistaking intermediate AS for origin AS.",
    "Ignoring AS path prepending.",
    "Comparing paths syntactically without considering routing semantics."
  ],
  "source_refs": ["rfc4271", "bear_2025"]
}
```

BEAR 特别提到，LLM 可能会把 AS path `[4608, 1221, 4637, 15169]` 的目的 AS 误判为 AS4637，而不是正确的 AS15169。
所以字段知识里必须写清楚 AS_PATH 的解释规则。

---

## 6. EvidenceTemplate

用于保存每类异常需要的证据。

```json
{
  "id": "evidence_route_leak",
  "entity_type": "EvidenceTemplate",
  "applies_to": "Route Leak",
  "required_evidence": [
    {
      "name": "AS_PATH before event",
      "description": "Path before suspicious propagation.",
      "strength": "required"
    },
    {
      "name": "AS_PATH after event",
      "description": "Path after suspicious propagation.",
      "strength": "required"
    },
    {
      "name": "AS relationship sequence",
      "description": "Provider/customer/peer relationship sequence along path.",
      "strength": "required"
    },
    {
      "name": "valley-free violation",
      "description": "Whether the AS path violates expected export policy.",
      "strength": "required"
    },
    {
      "name": "leaker AS",
      "description": "AS that improperly propagates route.",
      "strength": "required"
    }
  ],
  "optional_evidence": [
    "RPKI status",
    "historical similar paths",
    "collector coverage",
    "known incident report"
  ],
  "false_positive_checks": [
    "AS relationship inference error",
    "legitimate complex relationship",
    "temporary routing policy change",
    "collector-specific artifact"
  ]
}
```

---

## 7. PaperMethod

用于保存论文方法。

```json
{
  "id": "paper_method_bear",
  "entity_type": "PaperMethod",
  "paper": "BEAR",
  "problem": "BGP anomaly event explanation",
  "input": [
    "target IP prefix",
    "event start time",
    "BGP RIB records",
    "BGP update messages"
  ],
  "process": [
    "retrieve historical AS paths",
    "construct paths before event",
    "construct paths after event",
    "compare path changes",
    "classify anomaly type",
    "generate event report"
  ],
  "output": [
    "event type",
    "affected ASes",
    "AS path change report",
    "natural language event report"
  ],
  "useful_knowledge_for_kb": [
    "before/after path comparison template",
    "BGP evidence fields",
    "event report structure"
  ],
  "limitations": [
    "Focused on hijack and route leak.",
    "Requires detected event prefix and timestamp."
  ],
  "source_refs": ["bear_2025"]
}
```

---

## 8. Case

用于保存历史案例。

```json
{
  "id": "case_vodafone_2021_route_leak",
  "entity_type": "Case",
  "name": "Vodafone Idea AS55410 Route Leak",
  "event_type": "Route Leak",
  "date": "2021-04-16",
  "involved_ases": [
    {
      "asn": 55410,
      "role": "leaker"
    },
    {
      "asn": 270497,
      "role": "legitimate origin"
    }
  ],
  "affected_prefixes": ["24.152.117.0/24"],
  "summary": "A route leak involving AS55410 changed the observed AS path and affected global routing stability.",
  "evidence": [
    "historical AS path",
    "updated AS path",
    "leaker AS",
    "affected prefix"
  ],
  "source_refs": ["bgpshield_2025"]
}
```

BGPShield 的 case study 描述了 Vodafone India AS55410 route leak，涉及 prefix `24.152.117.0/24`，合法 origin AS 为 AS270497，泄露源为 AS55410，并给出了 historical path 和 updated path 的变化。

---

# 十一、关系设计

只做知识库数据准备，也需要关系表。
因为 BGP 知识不是孤立定义，而是有依赖链。

## 1. relationship schema

```json
{
  "src_id": "anomaly_route_leak",
  "src_type": "AnomalyType",
  "relation": "requires_evidence",
  "dst_id": "evidence_route_leak",
  "dst_type": "EvidenceTemplate",
  "source_refs": ["rfc7908", "beam_2024"],
  "confidence": 0.9
}
```

## 2. 第一批核心关系

```text
AS_PATH belongs_to BGP Update
AS_PATH belongs_to RIB Record
Origin AS derived_from AS_PATH
RouteViews provides RIB Dump
RouteViews provides Update Dump
RIPE RIS provides RIB Record
RIPE RIS provides Update Message
BGPStream retrieves RIB and Update
Prefix Hijack requires Origin Change Evidence
Subprefix Hijack requires More-specific Prefix Evidence
Route Leak requires Valley-free Violation Evidence
MOAS may_explain Origin Change
Anycast may_explain MOAS
RPKI validates Prefix-Origin Authorization
RPKI does_not_validate Full AS_PATH
AS Relationship supports Route Leak Analysis
AS Relationship supports Routing Role Analysis
BEAR uses Before-After AS Path Comparison
BEAM uses AS Relationship Graph
BGPShield uses AS Description and LLM Embedding
```

---

# 十二、数据处理流水线

技术流程可以这样设计：

```text
Step 1：资料登记
Step 2：原始文件归档
Step 3：解析为结构化文本
Step 4：清洗文本
Step 5：生成 chunk
Step 6：抽取实体
Step 7：构造关系
Step 8：人工校验
Step 9：生成质量报告
```

---

## Step 1：资料登记

输入：

```text
PDF
HTML
Markdown
TXT
CSV
API docs
case report
```

输出：

```text
inventory/sources.csv
```

要求：

```text
每个资料必须有 source_id
每个 source_id 全局唯一
必须记录 source_type
必须记录 trust_level
必须记录 review_status
```

---

## Step 2：原始文件归档

原始文件不修改，直接放入 `raw/`。

```text
raw/standards/rfc4271.pdf
raw/papers/bear_2025.pdf
raw/papers/bgpshield_2025.pdf
raw/data_docs/routeviews_doc.html
raw/cases/vodafone_2021.md
```

所有后续数据都必须能回到 raw。

---

## Step 3：解析

输出到 `parsed/`。

```text
parsed/papers/bear_2025.json
parsed/standards/rfc4271.json
parsed/cases/vodafone_2021.json
```

解析后应该有：

```text
标题
章节
段落
表格
图片说明
页码
引用位置
```

---

## Step 4：清洗

输出到 `cleaned/`。

清洗规则：

```text
去掉页眉页脚
去掉参考文献噪声，或单独保存
修复断词
合并错误换行
保留章节标题
保留图表说明
保留公式和算法编号
保留 RFC section 编号
统一 AS 写法：AS15169 / ASN15169 / 15169
统一 prefix 写法
```

不要清洗掉：

```text
RFC 编号
section 编号
figure 编号
table 编号
AS 号
prefix
时间
collector 名称
peer 信息
```

---

## Step 5：生成 chunk

输出：

```text
chunks/bgp_chunks.jsonl
```

生成策略：

```text
RFC：按 section 切
论文：按 section + 方法单元切
数据源文档：按数据对象 / 字段切
案例：按事件摘要 / 时间线 / 证据 / 影响切
概念：一概念一 chunk
表格：一表一 chunk 或一组字段一 chunk
```

---

## Step 6：抽取实体

输出：

```text
entities/bgp_concepts.jsonl
entities/anomaly_types.jsonl
entities/data_sources.jsonl
entities/evidence_templates.jsonl
entities/papers.jsonl
entities/cases.jsonl
```

实体抽取可以先人工做，不必一开始自动化。
第一版人工更稳。

---

## Step 7：构造关系

输出：

```text
relationships/relationships.jsonl
```

先做核心关系，不要追求完整图谱。

---

## Step 8：人工校验

每个实体都加：

```json
{
  "review_status": "pending | approved | rejected",
  "reviewer": "",
  "review_time": "",
  "review_notes": ""
}
```

---

## Step 9：质量报告

输出：

```text
reports/quality_report.md
```

包含：

```text
导入了多少资料
生成了多少 chunk
抽取了多少概念
抽取了多少异常类型
抽取了多少数据源
多少条缺少 source_ref
多少条未审核
多少条重复
哪些概念缺定义
哪些异常类型缺证据模板
哪些数据源缺局限性说明
```

---

# 十三、第一版 MVP 建设内容

不要一开始做全量。
第一版 MVP 建议只做这些。

## 1. 资料

```text
RFC4271
RFC6811
RFC7908
RouteViews 文档
RIPE RIS 文档
BGPStream 文档
BEAR
BEAM
BGPShield
5 个公开 BGP 事件案例
```

## 2. 实体数量目标

```text
BGPConcept：30 个
RoutingMechanism：10 个
AnomalyType：8 个
DataSource：8 个
DataField：30 个
EvidenceTemplate：8 个
PaperMethod：5 个
Case：5 个
Relationship：100 条左右
```

---

# 十四、第一批 BGPConcept 清单

你可以先人工整理这 30 个。

```text
BGP
AS
ASN
Prefix
Origin AS
AS_PATH
BGP Speaker
BGP Session
eBGP
iBGP
RIB
FIB
BGP Update
Announcement
Withdrawal
MRT
Route Collector
Vantage Point
Peer
RouteViews
RIPE RIS
BGPStream
RPKI
ROA
ROV
IRR
WHOIS / RDAP
AS Relationship
Customer Cone
Valley-free
```

---

# 十五、第一批 AnomalyType 清单

```text
prefix_hijack
subprefix_hijack
path_hijack
route_leak
moas
origin_change
path_manipulation
prefix_outage
```

每个异常类型都按下面模板写。

```json
{
  "id": "",
  "name": "",
  "definition": "",
  "typical_signals": [],
  "required_evidence": [],
  "optional_evidence": [],
  "possible_false_positives": [],
  "related_concepts": [],
  "source_refs": [],
  "review_status": "pending"
}
```

---

# 十六、第一批 EvidenceTemplate

## 1. prefix_hijack

```json
{
  "id": "evidence_prefix_hijack",
  "applies_to": "prefix_hijack",
  "required_evidence": [
    "target_prefix",
    "historical_origin_as",
    "event_origin_as",
    "before_event_as_path",
    "after_event_as_path",
    "collector_peer_observations",
    "prefix_ownership_evidence"
  ],
  "optional_evidence": [
    "RPKI_ROA_status",
    "IRR_record",
    "WHOIS_RDAP",
    "known_incident_report"
  ],
  "false_positive_checks": [
    "legitimate_moas",
    "prefix_transfer",
    "anycast",
    "ROA_not_updated",
    "single_collector_bias"
  ]
}
```

## 2. subprefix_hijack

```json
{
  "id": "evidence_subprefix_hijack",
  "applies_to": "subprefix_hijack",
  "required_evidence": [
    "victim_prefix",
    "more_specific_prefix",
    "historical_origin_as_of_parent_prefix",
    "event_origin_as_of_subprefix",
    "before_event_paths",
    "after_event_paths",
    "collector_coverage"
  ],
  "optional_evidence": [
    "RPKI_ROA_status",
    "prefix_ownership_record",
    "traffic_impact_report"
  ],
  "false_positive_checks": [
    "legitimate_deaggregation",
    "traffic_engineering",
    "CDN_anycast",
    "temporary_route_optimization"
  ]
}
```

## 3. route_leak

```json
{
  "id": "evidence_route_leak",
  "applies_to": "route_leak",
  "required_evidence": [
    "before_event_as_path",
    "after_event_as_path",
    "as_relationship_sequence",
    "suspected_leaker_as",
    "valley_free_violation",
    "affected_prefixes",
    "collector_observations"
  ],
  "optional_evidence": [
    "MANRS_report",
    "operator_statement",
    "historical_similar_route",
    "RPKI_status"
  ],
  "false_positive_checks": [
    "incorrect_as_relationship",
    "complex_business_relationship",
    "legitimate_policy_change",
    "temporary_route_flap"
  ]
}
```

## 4. prefix_outage

```json
{
  "id": "evidence_prefix_outage",
  "applies_to": "prefix_outage",
  "required_evidence": [
    "target_prefix",
    "reachable_vp_set_before",
    "reachable_vp_set_during",
    "withdrawal_updates",
    "as_path_disappearance",
    "start_time",
    "end_time",
    "collector_coverage"
  ],
  "optional_evidence": [
    "external_reachability_measurement",
    "operator_status_page",
    "historical_baseline"
  ],
  "false_positive_checks": [
    "collector_failure",
    "vp_side_issue",
    "short_route_flap",
    "planned_maintenance",
    "anycast_behavior"
  ]
}
```

---

# 十七、质量检查规则

建议写成 `quality_rules.yaml`。

```yaml
required_fields:
  BGPConcept:
    - id
    - name
    - definition
    - source_refs
    - review_status

  AnomalyType:
    - id
    - name
    - definition
    - required_evidence
    - possible_false_positives
    - source_refs

  DataSource:
    - id
    - name
    - description
    - suitable_for
    - limitations
    - source_refs

  EvidenceTemplate:
    - id
    - applies_to
    - required_evidence
    - false_positive_checks

quality_checks:
  - no_empty_definition
  - no_missing_source_ref
  - no_duplicate_entity_id
  - no_orphan_relationship
  - anomaly_type_must_have_evidence_template
  - data_source_must_have_limitations
  - case_must_have_event_type
  - case_must_have_time
  - case_must_have_source
```

---

# 十八、交付物标准

这一阶段完成后，你应该能交付：

```text
1. sources.csv
   所有资料来源登记表

2. cleaned/*.md
   清洗后的可读文本

3. chunks/*.jsonl
   标准知识片段

4. entities/*.jsonl
   结构化 BGP 知识实体

5. relationships/relationships.jsonl
   BGP 知识关系

6. schemas/*.json
   数据格式约束

7. reports/quality_report.md
   知识库质量报告

8. reports/coverage_report.md
   BGP 知识覆盖情况报告
```

其中最重要的是：

```text
entities/bgp_concepts.jsonl
entities/anomaly_types.jsonl
entities/data_sources.jsonl
entities/evidence_templates.jsonl
relationships/relationships.jsonl
```

---

# 十九、建议开发顺序

按这个顺序做，不要跳。

```text
第 1 周：建目录 + sources.csv + topic_taxonomy.yaml

第 2 周：整理 RFC4271、RFC6811、RFC7908
        输出 BGPConcept 和 RoutingMechanism

第 3 周：整理 RouteViews、RIPE RIS、BGPStream
        输出 DataSource 和 DataField

第 4 周：整理 BEAR、BEAM、BGPShield
        输出 PaperMethod、AnomalyType、EvidenceTemplate

第 5 周：整理 5 个历史案例
        输出 Case 和案例证据结构

第 6 周：构造 relationships.jsonl
        输出 quality_report 和 coverage_report
```

---

# 二十、最终你应该得到的能力

完成这一阶段后，你的 BGP 知识库应该能回答这些“数据准备层面”的问题：

```text
AS_PATH 是什么？它来自哪些数据源？
RIB 和 update 的区别是什么？
RouteViews 和 RIPE RIS 分别能提供什么？
prefix hijack 需要哪些证据？
subprefix hijack 和 prefix hijack 有什么区别？
route leak 为什么需要 AS relationship？
RPKI 能证明什么，不能证明什么？
MOAS 什么时候是异常，什么时候可能是正常？
collector 缺失会导致什么误判？
BEAR 使用什么数据解释 BGP 事件？
BEAM 如何理解 AS routing role？
BGPShield 如何构造 AS description？
一个历史 BGP 事件应该记录哪些字段？
```

这说明你的知识库已经不只是“文档集合”，而是一个真正的 **BGP 领域知识底座**。

---

一句话总结：

> 第一阶段不要做 RAG，不要做 Agent，不要接业务系统。
> 先把 BGP 知识拆成：**概念、机制、异常类型、数据源、字段、证据模板、论文方法、历史案例、关系**。
> 这一步做好，后面无论做问答、检测解释、报告生成还是 Agent 工作流，都会有稳定基础。
