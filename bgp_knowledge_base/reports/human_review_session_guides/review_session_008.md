# review_session_008 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- manual_followup：1
- ready_to_apply：9

## 1. Learning with Semantics / BEAM

- 实体 ID：`paper_method_beam`
- 实体类型：PaperMethod
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `beam_2024`
- `context_2026`

### cleaned 路径

- `cleaned/papers/beam_2024.md`

### parsed 路径

- `parsed/papers/beam_2024.json`

### Top 摘录

#### `extract_paper_method_beam_01`

- chunk：`beam_2024_s004_page_4_002`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-4`
- section_path：Page 4
- match_score：12
- matched_terms：announcements, anomaly, beam, beam_2024, business, learning, model, relationship, relationships, roles

> The other category of BGP anomalies is route leak: a misbehaved AS propagates BGP announcements to another AS in violation of the intended policies, resulting in traffic forwarded through unintended links. The Gao-Rexford model [30] describes the restrictions on BGP route propagation and can be used to identify BGP route leak ( i.e., the valley-free criterion). For example, in 2019, AS 21217 (Safe Host) broke the valley-free criterion by propagating announcements received from its providers ( e.g., AS 13237 ( euNetworks GmbH)) to another provider AS 4134 (China Telecom), redirecting large amounts of Internet traffic destined for European mobi...

#### `extract_paper_method_beam_02`

- chunk：`beam_2024_s005_page_5_001`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-5`
- section_path：Page 5
- match_score：12
- matched_terms：anomaly, beam, beam_2024, business, learning, model, policy, relationship, relationships, roles

> To our best knowledge, BEAM is the first dedicated network representation learning model that fully integrates BGP semantics into the training process and enables meaningful and accurate representation of ASes’ routing roles. Applying network representation learning, rather than using “raw” AS business relationships, is essential to characterize ASes’ routing roles. In particular, our network representation learning model can capture the global routing characteristics of each AS and translate them into embedding vectors, while the original AS business relationships can only indicate the local routing policy between two directly connected ASes...

#### `extract_paper_method_beam_03`

- chunk：`beam_2024_s015_page_15_002`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-15`
- section_path：Page 15
- match_score：12
- matched_terms：anomaly, beam, beam_2024, information, learning, model, path, relationship, relationships, roles

> Moreover, we can retrain BEAM with latest AS relationships to keep up with the routing role evolution. It takes ∼10 hours to train the model on our platform with GeForce RTX 2080 Ti, which is acceptable since CAIDA releases a new dataset roughly every month. Detection with Unknown ASes. BEAM cannot learn routing roles of ASes whose relationships with other ASes are unknown ( i.e., unknown ASes). Fortunately, the existing study [34] has revealed AS relationships for most ASes absent in the dataset. For instance, there are only 368 unknown ASes in the most recent events that we analyze, which is only 0.5040% of the total ASes. Further, our meas...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. Legitimate MOAS

- 实体 ID：`fp_legitimate_moas`
- 实体类型：FalsePositivePattern
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_fp_legitimate_moas_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：5
- matched_terms：check, context_2026, evidence, legitimate, relationship

> Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_fp_legitimate_moas_02`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：5
- matched_terms：ases, can, origin, rfc6811, roa

> ...cates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process them. The cache must also be refreshed period...

#### `extract_fp_legitimate_moas_03`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：4
- matched_terms：ases, context_2026, evidence, origin

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. MOAS

- 实体 ID：`anomaly_moas`
- 实体类型：AnomalyType
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_anomaly_moas_01`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：ases, authorization, can, depending, origin, prefix, rfc6811

> ...cates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process them. The cache must also be refreshed period...

#### `extract_anomaly_moas_02`

- chunk：`rfc6811_s001_1_003`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：6
- matched_terms：ases, context, operational, origin, prefix, rfc6811

> Although RPKI provides the context for this document, it is equally possible to use any other database that is able to map prefixes to their authorized origin ASes. Each distinct database will have its Mohapatra, et al. Standards Track [Page 3] RFC 6811 BGP Prefix Origin Validation January 2013 own particular operational and security characteristics; such characteristics are beyond the scope of this document.

#### `extract_anomaly_moas_03`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：5
- matched_terms：ases, context, context_2026, origin, prefix

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. MOAS

- 实体 ID：`concept_moas`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_concept_moas_01`

- chunk：`rfc6811_s003_2_003`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：8
- matched_terms：can, more, not, one, origin, prefix, rfc6811, than

> We observe that a Route can be Matched or Covered by more than one VRP. This procedure does not mandate an order in which VRPs must be visited; however, the validation state output is fully determined. Mohapatra, et al. Standards Track [Page 5] RFC 6811 BGP Prefix Origin Validation January 2013

#### `extract_concept_moas_02`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：can, not, one, origin, prefix, rfc6811, than

> ...cates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process them. The cache must also be refreshed period...

#### `extract_concept_moas_03`

- chunk：`rfc6811_s003_2_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：7
- matched_terms：more, one, origin, prefix, rfc6811, than, where

> ...BGP speaker loads validated objects from the cache into local storage. The objects loaded have the content (IP address, prefix length, maximum length, origin AS number). We refer to such a locally stored object as a "Validated ROA Payload" or "VRP". We define several terms in addition to "VRP". Where these terms are used, they are capitalized: o Prefix: (IP address, prefix length), interpreted as is customary (see [RFC4632]). o Route: Data derived from a received BGP UPDATE, as defined in [RFC4271], Section 1.1. The Route includes one Prefix and an AS_PATH; it may include other attributes to characterize the prefix. o VRP Prefix: The Prefix f...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. MRT

- 实体 ID：`concept_mrt`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `ripe_ris_docs`
- `bgpstream_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`
- `cleaned/data_docs/ripe_ris_docs.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`
- `parsed/data_docs/ripe_ris_docs.json`

### Top 摘录

#### `extract_concept_mrt_01`

- chunk：`ripe_ris_docs_s001_full_001`
- 文档：`ripe_ris_docs`
- source_ref：`raw/data_docs/ripe_ris_docs.html#full`
- section_path：RIPE Atlas docs \| RIPE RIS Docs Centre \| Docs
- match_score：9
- matched_terms：collectors, data, format, mrt, ripe, ripe_ris_docs, ris, source, update

> RIPE Atlas docs \| RIPE RIS Docs Centre \| Docs RIPE RIS Docs Centre Route collectors Route Collection Raw Data: MRT Files RIS Live RISwhois Routing Beacons Historical List of RIS Routing Beacons Prototypes Legal Information # RIPE RIS Docs Centre Welcome to the RIPE RIS Documentation. The Documentation is divided into sections that are featured in the sidebar to the left. You can switch between these sections and items at any time by clicking on the links. You can also use the searchbar above to search for any word or phrase in any document. RIPE RIS is a BGP routing data collection platform, and here we document the various pieces of this pla...

#### `extract_concept_mrt_02`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：8
- matched_terms：collectors, context_2026, data, ripe, ris, routeviews, source, table

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_concept_mrt_03`

- chunk：`bgpstream_docs_s001_full_001`
- 文档：`bgpstream_docs`
- source_ref：`raw/tools_docs/bgpstream_docs.html#full`
- section_path：BGPStream
- match_score：4
- matched_terms：bgpstream_docs, data, dump, source

> BGPStream Toggle navigation Home News Components Download Documentation Publications Data Providers Acknowledgements Contact Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutorials BGPReader libBGPStream PyBGPStream Docker Data Encoding Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutoria...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. Origin AS

- 实体 ID：`concept_origin_as`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `rfc6811`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc4271.md`
- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc4271.json`
- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_concept_origin_as_01`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：11
- matched_terms：as_path, asn, careful, context_2026, intermediate, not, origin, path, prefix, simple

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_concept_origin_as_02`

- chunk：`rfc4271_s005_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1`
- section_path：Introduction
- match_score：6
- matched_terms：as_path, not, path, prefix, reachability, rfc4271

> ...P) is an inter-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity for this reachability, from which routing loops may be pruned and, at the AS level, some policy decisions may be enforced. BGP-4 provides a set of mechanisms for supporting Classless Inter- Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support...

#### `extract_concept_origin_as_03`

- chunk：`rfc4271_s009_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：5
- matched_terms：as_path, origin, path, prefix, rfc4271

> ...through but) beyond that neighboring AS, intending that the traffic take a different route to that taken by the traffic originating in the neighboring AS (for that same destination). On the other hand, BGP can support any policy conforming to the destination-based forwarding paradigm. BGP-4 provides a new set of mechanisms for supporting Classless Inter-Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertising a set of destinations as an IP prefix and eliminating the concept of a network "class" within BGP. BGP-4 also introduces mechanisms that allow aggregation of routes, including aggregation of AS paths. Th...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. Origin Change

- 实体 ID：`anomaly_origin_change`
- 实体类型：AnomalyType
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`
- `bgpshield_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bgpshield_2025.md`
- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/papers/bgpshield_2025.json`
- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_anomaly_origin_change_01`

- chunk：`bgpshield_2025_s004_page_4_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-4`
- section_path：Page 4
- match_score：7
- matched_terms：as_path, bgpshield_2025, change, changes, origin, prefix, roa

> A route change will be recorded if the updated AS path diverges from the historical path associated with the matched prefix. For example, considering an updated prefix *.*.153.0/24with pathAS7500→AS2497→AS3491→AS17557. If the reference maps the broader historical prefix *.*.152.0/22 toAS7500→AS2497→AS36561, the difference signifies a route change. Notably, although the differences accurately reflect changes in routing behavior, they do not indicate anomalies, as some route changes result from legitimate operational practices (e.g.,traffic engineering or policy adjustments). The objective of BGPShield is to identify truly anomalous route chang...

#### `extract_anomaly_origin_change_02`

- chunk：`bgpshield_2025_s010_page_10_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-10`
- section_path：Page 10
- match_score：7
- matched_terms：before, bgpshield_2025, change, changes, origin, prefix, roa

> ...hus, we consider an alert valid if it matches confirmed information, particularly when the system identifies the target prefix as anomalous and accurately pinpoints the misbehaving AS as the responsible party, indicating successful detection of the confirmed anomaly for that event. Beyond confirmed anomalies, other alerts may indicate previously unrevealed routing anomalies or represent false positives. To validate these unconfirmed alerts, we extend the minor anomaly identification approach from standards introduced in BEAM [21] and redefine five typical anomalous routing change patterns for matching against suspicious routing behaviors (the...

#### `extract_anomaly_origin_change_03`

- chunk：`bgpshield_2025_s012_page_12_003`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-12`
- section_path：Page 12
- match_score：6
- matched_terms：as_path, bgpshield_2025, change, changes, origin, prefix

> In this case, the key ASes include: •AS270497 (RUTE MARIA DA CUNHA): The legitimate origin AS claiming ownership of prefix 24.152.117.0/24 •AS55410 (V odafone Idea Ltd.): The leak source, becoming the new origin AS. To analyze this incident, BGPShield’s LSE (detailed in Sec.4.2 ) first processes multi-source data to generate highdimensional semantic embeddings for ASes. These embeddings are subsequently processed through CDR (detailed in Sec.4.2.3) for optimization, providing informative representations for BAD (detailed in Sec.4.3). Anomaly Detection. Based on the embeddings, BAD further processes BGP updates for prefix 24.152.117.0/24, wher...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. origin_as

- 实体 ID：`field_origin_as`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `rfc6811`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc4271.md`
- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc4271.json`
- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_field_origin_as_01`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：8
- matched_terms：context_2026, datafield, evidence, origin, prefix, update, usually, without

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_field_origin_as_02`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：5
- matched_terms：analysis, change, context_2026, evidence, prefix

> Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_field_origin_as_03`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：5
- matched_terms：change, prefix, rfc4271, rib, update

> ...that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. Standards Track [Page 5] RFC 4271 BGP-4 January 2006 destinations are systems whose IP addresses are contained in one IP address prefix carried in the Network...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. Pakistan Telecom / YouTube Hijack

- 实体 ID：`case_pakistan_youtube_2008`
- 实体类型：Case
- 队列状态：`manual_followup`
- 当前实体状态：`pending`
- 当前人工决策：`needs_source`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：补充来源或记录人工说明；不要自动批准。

### 来源引用

- `youtube_hijack_google_2008`
- `context_2026`

### cleaned 路径

- `cleaned/cases/youtube_hijack_google_2008.md`

### parsed 路径

- `parsed/cases/youtube_hijack_google_2008.json`

### Top 摘录

#### `extract_case_pakistan_youtube_2008_01`

- chunk：`youtube_hijack_google_2008_s001_full_003`
- 文档：`youtube_hijack_google_2008`
- source_ref：`raw/cases/youtube_hijack_google_2008.html#full`
- section_path：YouTube Hijacking (February 24th 2008) Analysis of BGP Routing Dynamics
- match_score：11
- matched_terms：collector, event, hijack, hijacking, pakistan, prefix, public, telecom, which, youtube

> On Sunday, 24 February 2008, Pakistan Telecom (AS17557 ) started an unauthorized announcement of the prefix 208.65.153.0/24. One of Pakistan Telecom’s upstream providers, PCCW Global (AS3491 ) forwarded this announcement to the rest of the Internet, which resulted in the hijacking of YouTube traffic on a global scale. In this report we show how this event was observed by about 300 vantage points (also called collector peers) spread over the Internet by the Routing Information Service (RIS) of RIPE NCC and, in general, how to obtain hard data on network events using public available tools developed by the RIS and by the Compunet Research Group...

#### `extract_case_pakistan_youtube_2008_02`

- chunk：`youtube_hijack_google_2008_s001_full_001`
- 文档：`youtube_hijack_google_2008`
- source_ref：`raw/cases/youtube_hijack_google_2008.html#full`
- section_path：YouTube Hijacking (February 24th 2008) Analysis of BGP Routing Dynamics
- match_score：7
- matched_terms：collector, hijack, hijacking, prefix, public, youtube, youtube_hijack_google_2008

> YouTube Hijacking (February 24th 2008) Analysis of BGP Routing Dynamics Skip to main content Explore our many areas of focus Explore all research areas Applied AI & sciences Earth AI Health AI Science AI Sustainability & crisis resilience Foundational ML & algorithms Algorithms & theory Information retrieval Machine intelligence Machine perception Natural language processing People, systems & quantum AI Human-computer interaction and visualization Networking Quantum AI Responsible AI Anti abuse Software engineering Software systems Learn More Publications Projects Building a collaborative ecosystem Datasets Access high-quality datasets to acc...

#### `extract_case_pakistan_youtube_2008_03`

- chunk：`youtube_hijack_google_2008_s001_full_002`
- 文档：`youtube_hijack_google_2008`
- source_ref：`raw/cases/youtube_hijack_google_2008.html#full`
- section_path：YouTube Hijacking (February 24th 2008) Analysis of BGP Routing Dynamics
- match_score：7
- matched_terms：event, hijack, hijacking, prefix, public, youtube, youtube_hijack_google_2008

> Networking Quantum AI Responsible AI Anti abuse Software engineering Software systems Learn More Publications Projects Resources Building a collaborative ecosystem Datasets Access high-quality datasets to accelerate your research. Tools & services Explore our latest AI models and products. Open source Discover open-source code and collaborate with the community. Conferences & events Careers Shaping the future together See all programs Faculty programs Participating in the academic research community through meaningful engagement with university faculty. Student programs Supporting the next generation of researchers through a wide range of pro...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. Path Hijack

- 实体 ID：`anomaly_path_hijack`
- 实体类型：AnomalyType
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `bgpshield_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bgpshield_2025.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/papers/bgpshield_2025.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_anomaly_path_hijack_01`

- chunk：`bgpshield_2025_s010_page_10_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-10`
- section_path：Page 10
- match_score：12
- matched_terms：bgpshield_2025, change, event, information, manipulation, may, not, origin, path, relationship

> We do not include active probing based methods in our comparison as they require live network access and contemporaneous measurements, making them inherently unsuitable for retrospective analysis of historical BGP datasets. Note that each detection system may generates multiple alerts for a single anomaly event, with each alert reporting a potential anomaly. Thus, we consider an alert valid if it matches confirmed information, particularly when the system identifies the target prefix as anomalous and accurately pinpoints the misbehaving AS as the responsible party, indicating successful detection of the confirmed anomaly for that event. Beyon...

#### `extract_anomaly_path_hijack_02`

- chunk：`bgpshield_2025_s007_page_7_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-7`
- section_path：Page 7
- match_score：11
- matched_terms：as_path, bgpshield_2025, change, event, not, path, relationship, report, sequence, suspicious

> The final stage aggregates scattered anomalous route changes into distinct, temporally bounded anomaly events, which are then compiled into human-readable reports detailing their associated prefixes and responsible ASes. 4.3.1. Path Difference Scoring.Given a route change (see Sec.3), BAD first evaluates its path difference score between historical and updated route. To accurately quantify such difference score, we introduced theAnomalyResponsiveDynamicTimeWarping algorithm (AR-DTW), which aligns AS paths of arbitrary lengths and computes the minimal cumulative sum of pairwise distances between aligned AS embeddings as the path difference sco...

#### `extract_anomaly_path_hijack_03`

- chunk：`bgpshield_2025_s004_page_4_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-4`
- section_path：Page 4
- match_score：10
- matched_terms：as_path, bgpshield_2025, change, information, manipulation, may, not, origin, path, report

> A route change will be recorded if the updated AS path diverges from the historical path associated with the matched prefix. For example, considering an updated prefix *.*.153.0/24with pathAS7500→AS2497→AS3491→AS17557. If the reference maps the broader historical prefix *.*.152.0/22 toAS7500→AS2497→AS36561, the difference signifies a route change. Notably, although the differences accurately reflect changes in routing behavior, they do not indicate anomalies, as some route changes result from legitimate operational practices (e.g.,traffic engineering or policy adjustments). The objective of BGPShield is to identify truly anomalous route chang...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
