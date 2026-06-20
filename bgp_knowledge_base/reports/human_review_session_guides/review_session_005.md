# review_session_005 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. anomaly_prefix_outage

- 实体 ID：`evidence_prefix_outage`
- 实体类型：EvidenceTemplate
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_evidence_prefix_outage_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：2
- matched_terms：context_2026, evidencetemplate

> Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_evidence_prefix_outage_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：1
- matched_terms：context_2026

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_evidence_prefix_outage_03`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：1
- matched_terms：context_2026

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. anomaly_route_leak

- 实体 ID：`evidence_route_leak`
- 实体类型：EvidenceTemplate
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc7908`
- `rfc9234`
- `beam_2024`
- `context_2026`

### cleaned 路径

- `cleaned/papers/beam_2024.md`
- `cleaned/standards/rfc7908.md`
- `cleaned/standards/rfc9234.md`

### parsed 路径

- `parsed/papers/beam_2024.json`
- `parsed/standards/rfc7908.json`
- `parsed/standards/rfc9234.json`

### Top 摘录

#### `extract_evidence_route_leak_01`

- chunk：`beam_2024_s002_page_2_003`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-2`
- section_path：Page 2
- match_score：1
- matched_terms：beam_2024

> Although several security extensions have been proposed to counter these threats,e.g., BGPsec [4], psBGP [5] and S-BGP [6], they are not widely deployed, possibly due to incompatibility with the current Internet architecture. Besides, while RPKI [7] has gained traction in providing authoritative information about IP prefix ownership, its effectiveness is largely limited by the incomplete deployment of ROV [8]. More importantly, RPKI is not designed to mitigate route manipulation attacks or route leaks. Detecting routing anomalies in the global Internet is the first step towards secure Internet routing. The community has proposed significant r...

#### `extract_evidence_route_leak_02`

- chunk：`beam_2024_s003_page_3_001`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-3`
- section_path：Page 3
- match_score：1
- matched_terms：beam_2024

> tical guidance for network operators to fix routing anomalies. To address these challenges, we present a routing anomaly detection system centering around a novel network representation learning model, BEAM (BGP sEmAntics aware network eMbedding). Instead of learning any latent or opaque features, BEAM enables interpretable and accurate routing anomaly detection based on the intrinsic routing characteristics of ASes that are derived from the domain specific knowledge of BGP semantics. Specifically, we propose the concept of AS routing role to meaningfully characterize ASes in BGP route announcements. The design of routing role is derived from...

#### `extract_evidence_route_leak_03`

- chunk：`beam_2024_s003_page_3_002`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-3`
- section_path：Page 3
- match_score：1
- matched_terms：beam_2024

> To address the above challenges, BEAM employs a novel embedding mechanism to learn an embedding vector for each AS based on the AS graph constructed from AS relationships. The key of BEAM’s embedding is to preserve an AS’s proximity and hierarchy properties that are essential to its routing role. The exact definitions of proximity and hierarchy are given in §3.2. The embedding vectors are further employed to uniquely represent and interpret the routing roles of ASes, based on which our routing anomaly detection system reports routing anomalies upon observing abnormal routing role churns. Further, we design our learning mechanism to ensure tha...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. anomaly_subprefix_hijack

- 实体 ID：`evidence_subprefix_hijack`
- 实体类型：EvidenceTemplate
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

#### `extract_evidence_subprefix_hijack_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：2
- matched_terms：context_2026, evidencetemplate

> Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_evidence_subprefix_hijack_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：1
- matched_terms：context_2026

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_evidence_subprefix_hijack_03`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：1
- matched_terms：context_2026

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. AS

- 实体 ID：`concept_as`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_concept_as_01`

- chunk：`rfc4271_s009_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：8
- matched_terms：autonomous, inter-domain, multiple, network, rfc4271, same, system, under

> ...ending that the traffic take a different route to that taken by the traffic originating in the neighboring AS (for that same destination). On the other hand, BGP can support any policy conforming to the destination-based forwarding paradigm. BGP-4 provides a new set of mechanisms for supporting Classless Inter-Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertising a set of destinations as an IP prefix and eliminating the concept of a network "class" within BGP. BGP-4 also introduces mechanisms that allow aggregation of routes, including aggregation of AS paths. This document uses the term `Autonomous System...

#### `extract_concept_as_02`

- chunk：`rfc4271_s009_3_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：7
- matched_terms：autonomous, may, network, not, one, rfc4271, system

> The Border Gateway Protocol (BGP) is an inter-Autonomous System routing protocol. It is built on experience gained with EGP (as defined in [RFC904]) and EGP usage in the NSFNET Backbone (as described in [RFC1092] and [RFC1093]). For more BGP-related information, see [RFC1772], [RFC1930], [RFC1997], and [RFC2858]. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity,...

#### `extract_concept_as_03`

- chunk：`rfc4271_s015_4_3_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4.3`
- section_path：UPDATE Message Format
- match_score：7
- matched_terms：autonomous, may, multiple, network, not, rfc4271, system

> ...The information in the UPDATE message can be used to construct a graph that describes the relationships of the various Autonomous Systems. By applying rules to be discussed, routing Rekhter, et al. Standards Track [Page 14] RFC 4271 BGP-4 January 2006 information loops and some other anomalies may be detected and removed from inter-AS routing. An UPDATE message is used to advertise feasible routes that share common path attributes to a peer, or to withdraw multiple unfeasible routes from service (see 3.1). An UPDATE message MAY simultaneously advertise a feasible route and withdraw multiple unfeasible routes from service. The UPDATE message...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. AS Relationship

- 实体 ID：`concept_as_relationship`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `caida_as_relationships`
- `rfc7908`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`
- `cleaned/standards/rfc7908.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`
- `parsed/standards/rfc7908.json`

### Top 摘录

#### `extract_concept_as_relationship_01`

- chunk：`caida_as_relationships_s001_full_004`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：ases, between, business, caida_as_relationships, can, known, links, relationship, relationships

> figure 1. Types of AS relationships. The ASes at the bottom of the graph, D, E, and F, are customers of those above. ISPs in the middle, B and C, are both providers of ASes below and customers of ISPs above. ISPs B and C are also peers of each other. ISP A at the top is a provider to B and C and a customer of no one. Although business agreements between ISPs can be complicated, the original model introduced by Gao 1 abstracts business relationships into the following three most common types: customer-to-provider ( c2p ) (or if looked at from the opposite direction, provider-to-customer p2c ), peer-to-peer ( p2p ), and sibling-to-sibling ( s2s...

#### `extract_concept_as_relationship_02`

- chunk：`caida_as_relationships_s001_full_005`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：ases, between, business, caida_as_relationships, can, links, relationship, relationships, such

> An s2s link connects two ASes with a common administrative boundary. Such links usually appear as a result of mergers and acquisitions, or under certain network management scenarios. figure 2. The top two paths 1 and 2 are valid, while the bottom two 3 and 4 are invalid. We use the notion of money transfers between ASes to define valid and invalid AS paths. A valid path between source and destination ASes is one in which for every ISP providing transit (a transit provider), there exists a customer immediately adjacent to the ISP in the AS path. An invalid path has at least one transit provider not paid by a neighbor in the path. In figure 2 t...

#### `extract_concept_as_relationship_03`

- chunk：`caida_as_relationships_s001_full_007`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：ases, caida_as_relationships, can, inferred, known, links, relationship, relationships, valley-free

> Dimitropoulos, et al. 6 identified still other issues with the ToR formulation, like the random breaking of ties which can yield obviously incorrect inferences, e.g., well-known large providers are inferred as customers of small ASes. In the first paper 6 we handled this issue with multiobjective optimization techniques that incorporated AS degree into the inference. In a subsequent paper 7 we introduced improved algorithms that determine not only c2p but also p2p links (for those we can detect from BGP data). These improvements achieved more accurate AS relationship inferences, which we demonstrate against ground truth for a set of ASes. Ben...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. AS relationship inference error

- 实体 ID：`fp_as_relationship_error`
- 实体类型：FalsePositivePattern
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `caida_as_relationships`
- `rfc7908`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`
- `cleaned/standards/rfc7908.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`
- `parsed/standards/rfc7908.json`

### Top 摘录

#### `extract_fp_as_relationship_error_01`

- chunk：`caida_as_relationships_s001_full_003`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：8
- matched_terms：caida_as_relationships, can, data, dataset, date, inference, look, relationship

> Accurate data on the structure of actual relationships among ASes is required for many research efforts concerned with performance, robustness, and evolution of the global Internet. Examples of both research and operational tasks that cannot neglect AS relationships include: realistic simulations trying to model path inflation effects caused by routing policies; understanding how packets are routed in the Internet and how to optimize Internet paths by analyzing existing deficiencies; development of more scalable interdomain routing protocols and architectures, like HLP , that take into account the structure of AS relationships to optimize the...

#### `extract_fp_as_relationship_error_02`

- chunk：`caida_as_relationships_s001_full_013`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：8
- matched_terms：caida_as_relationships, data, dataset, date, inference, look, relationship, when

> ...Routeviews BGP tables. The general serial-2 procedure for creating a file is as follows: Collect BGP communites from IX looking glass servers. Infer peering links between pairs of AS which accept routes from each other. Collect archived BGP data from Routeviews and RIPE RIS. Infer peering links at points in the observed AS paths that cross an known IX. Collect traceroutes from ark monitors. Convert the IP path to AS path using inferred ownership and keep the first AS link in the path. Merge all newly inferred links to the serial-1 graph as peering links For details of the algorithms used to infer AS relationships, see the following papers: AS...

#### `extract_fp_as_relationship_error_03`

- chunk：`caida_as_relationships_s001_full_004`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：6
- matched_terms：caida_as_relationships, can, data, dataset, look, relationship

> figure 1. Types of AS relationships. The ASes at the bottom of the graph, D, E, and F, are customers of those above. ISPs in the middle, B and C, are both providers of ASes below and customers of ISPs above. ISPs B and C are also peers of each other. ISP A at the top is a provider to B and C and a customer of no one. Although business agreements between ISPs can be complicated, the original model introduced by Gao 1 abstracts business relationships into the following three most common types: customer-to-provider ( c2p ) (or if looked at from the opposite direction, provider-to-customer p2c ), peer-to-peer ( p2p ), and sibling-to-sibling ( s2s...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. AS_PATH

- 实体 ID：`concept_as_path`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bear_2025.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/papers/bear_2025.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_concept_as_path_01`

- chunk：`bear_2025_s003_page_3_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-3`
- section_path：Page 3
- match_score：10
- matched_terms：announcement, as_path, bear_2025, end, has, not, origin, path, traversed, update

> path [18]. The AS path is a sequential list of AS numbers that a route advertisement has traversed; each time a router forwards the announcement, it prepends its own AS number to the path, thereby creating a path to reach an IP prefix that will be filtered by policy-based routing rules by following the AS to decide whether to take this path and advertise it or not [4]. BGP was originally designed to prioritize functionality and scalability rather than security, so it lacks built-in mechanisms to authenticate the source of route announcements [19]. Because of this trust-based design, any AS can announce routes for IP prefixes regardless of own...

#### `extract_concept_as_path_02`

- chunk：`bear_2025_s004_page_4_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-4`
- section_path：Page 4
- match_score：6
- matched_terms：announcement, as_path, bear_2025, not, path, update

> Fig. 3. Overview of how BGP messages and routing information are collected. Fig. 4. An example of a BGP update message. event E and identify key unknown features, such as the event type and relevant ASes. B. Data Retrieval After obtaining the target IP prefix ip and the specific start time t, we utilize the open-source software framework BGPStream [43] to retrieve relevant AS path information from the BGP dataset DBGP . Specifically, we extract AS paths from BGP update messages and routing information base (RIB) records to construct three datasets: historical AS paths, AS paths before the event, and AS paths after the event. BGPStream accesse...

#### `extract_concept_as_path_03`

- chunk：`bear_2025_s005_page_5_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-5`
- section_path：Page 5
- match_score：6
- matched_terms：as_path, bear_2025, destination, has, not, path

> Fig. 5. Number of AS path per IP prefix. Fig. 6. Overview of the framework that generates report for BGP anomaly events The method begins with a data analysis phase designed to transform tabular BGP data into textual descriptions, as illustrated in Figure 6. The LLM is first provided with the BGP data in a tabular format and prompted to describe changes in AS paths by comparing Daf ter with Dbef ore, using Dhistory as a reference. The prompt is carefully structured to decompose the reasoning process, directing the LLM to analyze AS path changes systematically. The LLM is required to answer the following key questions. • Does the existing path...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. as_path

- 实体 ID：`field_as_path`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bear_2025.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/papers/bear_2025.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_field_as_path_01`

- chunk：`bear_2025_s003_page_3_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-3`
- section_path：Page 3
- match_score：8
- matched_terms：analysis, as_path, bear_2025, origin, path, record, rib, update

> path [18]. The AS path is a sequential list of AS numbers that a route advertisement has traversed; each time a router forwards the announcement, it prepends its own AS number to the path, thereby creating a path to reach an IP prefix that will be filtered by policy-based routing rules by following the AS to decide whether to take this path and advertise it or not [4]. BGP was originally designed to prioritize functionality and scalability rather than security, so it lacks built-in mechanisms to authenticate the source of route announcements [19]. Because of this trust-based design, any AS can announce routes for IP prefixes regardless of own...

#### `extract_field_as_path_02`

- chunk：`bear_2025_s004_page_4_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-4`
- section_path：Page 4
- match_score：8
- matched_terms：analysis, as_path, bear_2025, path, paths, record, rib, update

> Fig. 3. Overview of how BGP messages and routing information are collected. Fig. 4. An example of a BGP update message. event E and identify key unknown features, such as the event type and relevant ASes. B. Data Retrieval After obtaining the target IP prefix ip and the specific start time t, we utilize the open-source software framework BGPStream [43] to retrieve relevant AS path information from the BGP dataset DBGP . Specifically, we extract AS paths from BGP update messages and routing information base (RIB) records to construct three datasets: historical AS paths, AS paths before the event, and AS paths after the event. BGPStream accesse...

#### `extract_field_as_path_03`

- chunk：`bear_2025_s004_page_4_002`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-4`
- section_path：Page 4
- match_score：8
- matched_terms：analysis, as_path, bear_2025, path, paths, record, rib, update

> The format of an RIB record is similar to that of a BGP message, with the key distinction being the identifier letter “R” (highlighted in blue), which denotes an RIB record. To build the datasets we proceed as follows. 1) Historical Data ( Dhistory): We extract RIB records from all RIPE RIS collectors, capturing all AS paths to ip. To ensure Dhistory does not include information about the anomaly event E, we use RIB records from at least eight hours prior to the event’s start time t. Given that RIB records are collected every eight hours, the timestamp for Dhistory is determined as ⌊ t−8h 8h ⌋ × 8h. Since each AS maintains a single AS path to...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. AS_PATH Prepending

- 实体 ID：`mechanism_as_path_prepending`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_mechanism_as_path_prepending_01`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：9
- matched_terms：are, as_path, asn, asns, context_2026, not, path, prepending, repeated

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_mechanism_as_path_prepending_02`

- chunk：`rfc4271_s009_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：6
- matched_terms：appear, are, as_path, path, policy, rfc4271

> ...en by the traffic originating in the neighboring AS (for that same destination). On the other hand, BGP can support any policy conforming to the destination-based forwarding paradigm. BGP-4 provides a new set of mechanisms for supporting Classless Inter-Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertising a set of destinations as an IP prefix and eliminating the concept of a network "class" within BGP. BGP-4 also introduces mechanisms that allow aggregation of routes, including aggregation of AS paths. This document uses the term `Autonomous System' (AS) throughout. The classic definition of an Autonomous...

#### `extract_mechanism_as_path_prepending_03`

- chunk：`rfc4271_s026_4_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4`
- section_path：Optional non-transitive.
- match_score：6
- matched_terms：appear, are, as_path, not, path, rfc4271

> New, transitive optional attributes MAY be attached to the path by the originator or by any other BGP speaker in the path. If they are not attached by the originator, the Partial bit in the Attribute Flags octet is set to 1. The rules for attaching new non-transitive optional attributes will depend on the nature of the specific attribute. The documentation of each new non-transitive optional attribute will be expected to include such rules (the description of the MULTI_EXIT_DISC attribute gives an example). All optional attributes (both transitive and non-transitive), MAY be updated (if appropriate) by BGP speakers in the path. The sender of...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. as_relationship_sequence

- 实体 ID：`field_as_relationship_sequence`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc7908`
- `caida_as_relationships`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`
- `cleaned/standards/rfc7908.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`
- `parsed/standards/rfc7908.json`

### Top 摘录

#### `extract_field_as_relationship_sequence_01`

- chunk：`caida_as_relationships_s001_full_005`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：6
- matched_terms：as_path, caida_as_relationships, its, relationship, relationships, source

> ...e invalid. We use the notion of money transfers between ASes to define valid and invalid AS paths. A valid path between source and destination ASes is one in which for every ISP providing transit (a transit provider), there exists a customer immediately adjacent to the ISP in the AS path. An invalid path has at least one transit provider not paid by a neighbor in the path. In figure 2 the top two examples are valid paths, while the bottom two are invalid. In Example 1 the transit providers are A, B, and C. ISPs B and C pay to A, D pays to B, and F pays to C. In Example 2 the transit providers are B and C, and they are paid by D and F, respect...

#### `extract_field_as_relationship_sequence_02`

- chunk：`caida_as_relationships_s001_full_012`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：6
- matched_terms：as_path, caida_as_relationships, inferred, provider-customer, relationship, relationships

> ...S graph derived from RouteViews and RIPE RIS BGP table snapshots taken at 24-hour intervals over a 5-day period. The AS relationships available are customer-provider (and provider-customer in the opposite direction), and peer-to-peer. See the README in the Serial-1 data directory for details of the file formats. The general serial-1 procedure for creating a file is as follows: Extract and clean AS paths from the BGP table snapshots. Infer the ASes that form a clique of transit-free networks at the top of the AS topology (Tier-1 ASes), or use a supplied list of these ASes. Break AS paths into triplets, and use these triplets to infer customer-...

#### `extract_field_as_relationship_sequence_03`

- chunk：`caida_as_relationships_s001_full_001`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：5
- matched_terms：caida_as_relationships, its, relationship, relationships, source

> AS Relationships - CAIDA Skip to main content Resource Catalog Datasets Media / Presentations Papers Recipes Software / Tools About Supporting Donate Sponsors Jobs at CAIDA Annual Reports Program Plan Legal Agreements Single Sign-On Staff Blog Contact Us Workshops Projects Funding AS Relationships Catalog Resource Catalog Toggle Dropdown Datasets Overview table Media / Presentations Posters Visualizations Papers External papers Report new publication Recipes Software / Tools About About Toggle Dropdown Supporting Donate Sponsors Jobs at CAIDA Annual Reports Program Plan Legal Agreements Single Sign-On Staff Blog Contact Us Workshops Toggle Dr...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
