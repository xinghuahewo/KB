# review_session_009 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. Path Manipulation

- 实体 ID：`anomaly_path_manipulation`
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

#### `extract_anomaly_path_manipulation_01`

- chunk：`bgpshield_2025_s004_page_4_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-4`
- section_path：Page 4
- match_score：8
- matched_terms：as_path, bgpshield_2025, change, changes, manipulation, path, policy, refers

> A route change will be recorded if the updated AS path diverges from the historical path associated with the matched prefix. For example, considering an updated prefix *.*.153.0/24with pathAS7500→AS2497→AS3491→AS17557. If the reference maps the broader historical prefix *.*.152.0/22 toAS7500→AS2497→AS36561, the difference signifies a route change. Notably, although the differences accurately reflect changes in routing behavior, they do not indicate anomalies, as some route changes result from legitimate operational practices (e.g.,traffic engineering or policy adjustments). The objective of BGPShield is to identify truly anomalous route chang...

#### `extract_anomaly_path_manipulation_02`

- chunk：`bgpshield_2025_s007_page_7_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-7`
- section_path：Page 7
- match_score：8
- matched_terms：artifacts, as_path, bgpshield_2025, change, changes, path, such, suspicious

> The final stage aggregates scattered anomalous route changes into distinct, temporally bounded anomaly events, which are then compiled into human-readable reports detailing their associated prefixes and responsible ASes. 4.3.1. Path Difference Scoring.Given a route change (see Sec.3), BAD first evaluates its path difference score between historical and updated route. To accurately quantify such difference score, we introduced theAnomalyResponsiveDynamicTimeWarping algorithm (AR-DTW), which aligns AS paths of arbitrary lengths and computes the minimal cumulative sum of pairwise distances between aligned AS embeddings as the path difference sco...

#### `extract_anomaly_path_manipulation_03`

- chunk：`bgpshield_2025_s005_page_5_001`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-5`
- section_path：Page 5
- match_score：7
- matched_terms：as_path, bgpshield_2025, change, changes, path, such, suspicious

> ...DistanceSimilarOrganization Neg:DivergentRole Org-Based Grouping Pos:SimilarRole ASOrganization ASRoleRepresentation Ⅰ. Path Difference ScoringCurrent RouteOrigin RouteT Route PathPrefixRoute PathPrefix𝐳"1, 𝐳"4... ,𝐳"8*.*.*.*/20𝐳"1, 𝐳"4... , 𝐳"2*.*.*.*/18**.** 𝐳"3, 𝐳"9... , 𝐳"7*.*.*.*/18𝐳"3, 𝐳"5... , 𝐳"7*.*.*.*/18**.** ............... Path Diff ScoreCurrent RouteOrigin RouteT Route PathPrefixRoute PathPrefix 20.01𝐳"1, 𝐳"4... , 𝐳"8*.*.*.*/20𝐳"1, 𝐳"4... , 𝐳"2*.*.*.*/18**.** 18.18𝐳"3, 𝐳"9... , 𝐳"7*.*.*.*/18𝐳"3, 𝐳"5... , 𝐳"7*.*.*.*/18**.** .................. AR-DTW Ⅲ. Multi-View Event AggregationHuman ReadableReport Prefix-Aggregation PrefixAS Pa...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. Path-vector routing

- 实体 ID：`mechanism_path_vector`
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

#### `extract_mechanism_path_vector_01`

- chunk：`rfc4271_s005_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1`
- section_path：Introduction
- match_score：9
- matched_terms：as_path, ases, can, information, loops, path, policy, reachability, rfc4271

> ...P) is an inter-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity for this reachability, from which routing loops may be pruned and, at the AS level, some policy decisions may be enforced. BGP-4 provides a set of mechanisms for supporting Classless Inter- Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support...

#### `extract_mechanism_path_vector_02`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：7
- matched_terms：ases, can, information, path, reachability, rfc4271, update

> For the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the...

#### `extract_mechanism_path_vector_03`

- chunk：`rfc4271_s009_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：6
- matched_terms：as_path, ases, can, path, policy, rfc4271

> ...oute to that taken by the traffic originating in the neighboring AS (for that same destination). On the other hand, BGP can support any policy conforming to the destination-based forwarding paradigm. BGP-4 provides a new set of mechanisms for supporting Classless Inter-Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertising a set of destinations as an IP prefix and eliminating the concept of a network "class" within BGP. BGP-4 also introduces mechanisms that allow aggregation of routes, including aggregation of AS paths. This document uses the term `Autonomous System' (AS) throughout. The classic definition...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. Peer

- 实体 ID：`concept_peer`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `routeviews_api_doc`
- `ripe_ris_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_docs.md`
- `cleaned/data_docs/routeviews_api_doc.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_docs.json`
- `parsed/data_docs/routeviews_api_doc.json`

### Top 摘录

#### `extract_concept_peer_01`

- chunk：`routeviews_api_doc_s001_full_001`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：7
- matched_terms：are, collector, not, peer, peers, routes, routeviews_api_doc

> RouteViews API Documentation API Home Documentation Playground Member area Version: v0.10.2-129-g07aea9e # RouteViews API Documentation ## Table of Contents * [Introduction](#introduction) * [Access](#access) * [End points not discoverable from API root](#undiscoverable) * [`/meta/collectors`](#meta_collectors) - metadata about RouteViews BGP collectors and their data availability * [`/asn/`*asn*](#asn) - query routes originated by an Autonomous System * [`/prefix/`*prefix*](#prefix) - query a route (or its parent) in the RIB * [`/rib/collectors`](#rib_collectors) - get list of collectors for which we have current RIB information * [`/rib/pee...

#### `extract_concept_peer_02`

- chunk：`routeviews_api_doc_s001_full_003`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：7
- matched_terms：all, are, collector, exchanges, not, peer, routeviews_api_doc

> Exchange \| collector ---------\|----------- AMS-IX Amsterdam, Netherlands \| amsix.ams.routeviews.org LINX, London, United Kingdom \| route-views.linx.routeviews.org NAPAfrica, Johannesburg, South Africa \| route-views.napafrica.routeviews.org Equinix SG1, Singapore, Singapore \| route-views.sg.routeviews.org Equinix SYD1, Sydney, Australia \| route-views.sydney.routeviews.org IX.br (PTT.br), São Paulo, Brazil \| ix-br2.gru.routeviews.org Multi-hop at U of Oregon \| route-views3.routeviews.org Multi-hop at U of Oregon \| route-views4.routeviews.org Multi-hop at U of Oregon \| route-views5.routeviews.org Multi-hop at U of Oregon \| route-views6.routeview...

#### `extract_concept_peer_03`

- chunk：`routeviews_api_doc_s001_full_007`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：6
- matched_terms：all, collector, not, peer, peers, routeviews_api_doc

> ```json [ { "prefix": "128.223.0.0/16", "origin_asn": 3582, "rpki_state": "not-found", "rpki_roas": null, "reporting_peers": [ { "peer_asn": 267613, "peer_addr": "195.66.226.39", "collector": "route-views.linx", "as_path": "267613 52320 6461 11164 3701 3582 3582 3582 3582 3582 3582", "communities": "5469:11000 5469:10850 5469:2200", "timestamp": "2024-07-09T10:00:06Z" }, { "peer_asn": 1031, "peer_addr": "195.66.231.48", "collector": "route-views.linx", "as_path": "6447 1031 174 3701 3701 3701 3701 3582 3582 3582 3582 3582 3582", "communities": "1031:701 1031:800 1031:802", "timestamp": "2024-07-12T02:47:21Z" }, ... { "peer_asn": 34177, "peer_...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. peer_asn

- 实体 ID：`field_peer_asn`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `routeviews_api_doc`
- `ripe_ris_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_docs.md`
- `cleaned/data_docs/routeviews_api_doc.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_docs.json`
- `parsed/data_docs/routeviews_api_doc.json`

### Top 摘录

#### `extract_field_peer_asn_01`

- chunk：`routeviews_api_doc_s001_full_007`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：10
- matched_terms：api, collector, every, not, path, peer, peer_asn, routeviews, routeviews_api_doc, view

> ```json [ { "prefix": "128.223.0.0/16", "origin_asn": 3582, "rpki_state": "not-found", "rpki_roas": null, "reporting_peers": [ { "peer_asn": 267613, "peer_addr": "195.66.226.39", "collector": "route-views.linx", "as_path": "267613 52320 6461 11164 3701 3582 3582 3582 3582 3582 3582", "communities": "5469:11000 5469:10850 5469:2200", "timestamp": "2024-07-09T10:00:06Z" }, { "peer_asn": 1031, "peer_addr": "195.66.231.48", "collector": "route-views.linx", "as_path": "6447 1031 174 3701 3701 3701 3701 3582 3582 3582 3582 3582 3582", "communities": "1031:701 1031:800 1031:802", "timestamp": "2024-07-12T02:47:21Z" }, ... { "peer_asn": 34177, "peer_...

#### `extract_field_peer_asn_02`

- chunk：`routeviews_api_doc_s001_full_008`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：10
- matched_terms：api, collector, global, not, path, peer, peer_asn, routeviews, routeviews_api_doc, view

> ```json [ { "prefix": "2001:468:d01::/48", "origin_asn": 3582, "rpki_state": "not-found", "rpki_roas": null, "reporting_peers": [ { "peer_asn": 18106, "peer_addr": "2001:d98::19", "collector": "route-views6", "as_path": "18106 3701 3582 3582 3582 3582 3582 3582", "communities": "33108:3000", "timestamp": "2024-07-09T10:00:00Z" }, { "peer_asn": 20912, "peer_addr": "2001:40d0::1e", "collector": "route-views6", "as_path": "6447 20912 6939 3701 3582 3582 3582 3582 3582 3582", "communities": "", "timestamp": "2024-07-12T02:32:57Z" }, ... }, { "prefix": "2001:468:d00::/40", "origin_asn": 4600, "rpki_state": "not-found", "rpki_roas": null, "reportin...

#### `extract_field_peer_asn_03`

- chunk：`routeviews_api_doc_s001_full_017`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：9
- matched_terms：api, collector, observed, one, path, peer, routeviews, routeviews_api_doc, view

> This endpoint returns a list of peers connected to RouteViews collectors that provide at least one prefix learned directly from the specified asn. This behavior is equivalent to using the Cisco-style regular expression (^{asn}_) to match routes whose AS path starts with the requested asn. **Path Parameters:** * *`ASN`*: The ASN to query. **Optional Query Parameters:** * `af`: Filter by address family: * 4 or IPv4: IPv4 peers only * 6 or IPv6: IPv6 peers only * `collector`: Specify a particular RouteViews collector to filter results. **Response Structure** The response is a JSON array of peer objects, identical in structure to the [`/rib/peers...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. Prefix

- 实体 ID：`concept_prefix`
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

#### `extract_concept_prefix_01`

- chunk：`rfc4271_s005_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1`
- section_path：Introduction
- match_score：6
- matched_terms：address, cidr, may, prefix, reachability, rfc4271

> ...P) is an inter-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity for this reachability, from which routing loops may be pruned and, at the AS level, some policy decisions may be enforced. BGP-4 provides a set of mechanisms for supporting Classless Inter- Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support...

#### `extract_concept_prefix_02`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：6
- matched_terms：address, may, prefix, reachability, rfc4271, unit

> For the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the...

#### `extract_concept_prefix_03`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：5
- matched_terms：context_2026, may, origin, prefix, usually

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. prefix

- 实体 ID：`field_prefix`
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

#### `extract_field_prefix_01`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：5
- matched_terms：prefix, rfc4271, rib, track, update

> ...Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. Standards Track [Page 5] RFC 4271 BGP-4 January 2006 destinations are systems whose IP addresses are contained in one IP address prefix carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message. The path is th...

#### `extract_field_prefix_02`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：5
- matched_terms：prefix, rfc4271, rib, track, update

> ...the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the NLR...

#### `extract_field_prefix_03`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：4
- matched_terms：context_2026, datafield, prefix, update

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. Prefix Hijack

- 实体 ID：`anomaly_prefix_hijack`
- 实体类型：AnomalyType
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `rfc6811`
- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bear_2025.md`
- `cleaned/standards/rfc4271.md`
- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/papers/bear_2025.json`
- `parsed/standards/rfc4271.json`
- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_anomaly_prefix_hijack_01`

- chunk：`bear_2025_s007_page_7_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-7`
- section_path：Page 7
- match_score：8
- matched_terms：bear_2025, hijack, not, own, prefix, roa, rpki, when

> Fig. 9. An example report for a BGP hijack event. In this report, BEAR not only identifies the event type but also detects the hijacked sub-prefix. are the most common prompt engineering methods in natural language processing. In the CoT reasoning baseline, we provide definitions for both BGP hijack and BGP route leak, instructing the LLM to explain its reasoning when inferring the event type, thereby encouraging a step-by-step thought process. For the in-context learning baseline, we present the LLM with four synthetic examples of BGP data generated by our synthetic BGP event generation framework. Each example corresponds to a specific event...

#### `extract_anomaly_prefix_hijack_02`

- chunk：`bear_2025_s010_page_10_004`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-10`
- section_path：Page 10
- match_score：7
- matched_terms：bear_2025, hijack, hijacking, not, own, prefix, rpki

> Bush, “ispy: Detecting ip prefix hijacking on my own,” Proceedings of the ACM SIGCOMM 2008 Conference on Data Communication , pp. 327–338, 2008. [40] R. Mondal, A. Tang, R. Beckett, T. Millstein, and G. Varghese, “What do LLMs need to synthesize correct router configurations?” Proceedings of the 22nd ACM Workshop on Hot Topics in Networks , pp. 189–195, 2023. [41] K. B. Kan, H. Mun, G. Cao, and Y . Lee, “Mobile-llama: Instruction fine-tuning open-source llm for network analysis in 5g networks,” IEEE Network, 2024. [42] M. Palmero, K. P. Annamalai, H. Singaravelan, D. Zacks, and J. W. Capobianco, “Providing an ai-enabled network assistant for...

#### `extract_anomaly_prefix_hijack_03`

- chunk：`bear_2025_s002_page_2_002`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-2`
- section_path：Page 2
- match_score：6
- matched_terms：as_path, bear_2025, hijack, prefix, roa, rpki

> Moreover, we introduce the first approach to generate synthetic BGP anomaly event data, addressing the scarcity of fully documented BGP anomaly events. To create high-quality synthetic events, we leverage an LLM to produce specific details of an anomaly, such as the timestamp, victim IP prefix, event type, hijacker or route leaker, AS path after the event, and detection rate. Using the generated details, we extract relevant BGP data from an existing BGP dataset based on the timestamp and victim IP prefix. This data is then modified according to the LLM-specified details, creating synthetic BGP data that simulates the occurrence of an anomaly...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. Prefix Outage

- 实体 ID：`anomaly_prefix_outage`
- 实体类型：AnomalyType
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

#### `extract_anomaly_prefix_outage_01`

- chunk：`rfc4271_s058_8_2_2_010`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#8.2.2`
- section_path：Finite State Machine
- match_score：3
- matched_terms：occurs, rfc4271, when

> ...ons attribute is TRUE, and - changes its state to Idle. Collision detection mechanisms (Section 6.8) need to be applied when a valid BGP OPEN message is received (Event 19 or Event 20). Please refer to Section 6.8 for the details of the comparison. A Rekhter, et al. Standards Track [Page 65] RFC 4271 BGP-4 January 2006 CollisionDetectDump event occurs when the BGP implementation determines, by means outside the scope of this document, that a connection collision has occurred. If a connection in the OpenSent state is determined to be the connection that must be closed, an OpenCollisionDump (Event 23) is signaled to the state machine. If such a...

#### `extract_anomaly_prefix_outage_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：2
- matched_terms：context_2026, prefix

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_anomaly_prefix_outage_03`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：2
- matched_terms：context_2026, prefix

> ...t AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. RIB

- 实体 ID：`concept_rib`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `routeviews_api_doc`
- `bgpstream_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`
- `cleaned/data_docs/routeviews_api_doc.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`
- `parsed/data_docs/routeviews_api_doc.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_concept_rib_01`

- chunk：`rfc4271_s011_3_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.2`
- section_path：Routing Information Base
- match_score：9
- matched_terms：base, information, not, process, rfc4271, rib, routes, selected, table

> The Routing Information Base (RIB) within a BGP speaker consists of three distinct parts: a) Adj-RIBs-In: The Adj-RIBs-In stores routing information learned from inbound UPDATE messages that were received from other BGP speakers. Their contents represent routes that are available as input to the Decision Process. b) Loc-RIB: The Loc-RIB contains the local routing information the BGP speaker selected by applying its local policies to the routing information contained in its Adj-RIBs-In. These are the routes that will be used by the local BGP speaker. The next hop for each of these routes MUST be resolvable via the local BGP speaker's Routing T...

#### `extract_concept_rib_02`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：8
- matched_terms：base, change, information, process, rfc4271, rib, routes, selected

> ...that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. Standards Track [Page 5] RFC 4271 BGP-4 January 2006 destinations are systems whose IP addresses are contained in one IP address prefix carried in the Network...

#### `extract_concept_rib_03`

- chunk：`rfc4271_s060_9_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1`
- section_path：Decision Process
- match_score：8
- matched_terms：base, information, not, process, rfc4271, rib, routes, selected

> The Decision Process selects routes for subsequent advertisement by applying the policies in the local Policy Information Base (PIB) to the routes stored in its Adj-RIBs-In. The output of the Decision Process is the set of routes that will be advertised to peers; the selected routes will be stored in the local speaker's Adj-RIBs-Out, according to policy. The BGP Decision Process described here is conceptual, and does not have to be implemented precisely as described, as long as the implementations support the described functionality and they exhibit the same externally visible behavior. The selection process is formalized by defining a functi...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. RIPE RIS

- 实体 ID：`concept_ripe_ris`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `ripe_ris_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_docs.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_docs.json`

### Top 摘录

#### `extract_concept_ripe_ris_01`

- chunk：`ripe_ris_docs_s001_full_001`
- 文档：`ripe_ris_docs`
- source_ref：`raw/data_docs/ripe_ris_docs.html#full`
- section_path：RIPE Atlas docs \| RIPE RIS Docs Centre \| Docs
- match_score：11
- matched_terms：collection, collector, collectors, data, information, mrt, ncc, platform, ripe, ripe_ris_docs

> RIPE Atlas docs \| RIPE RIS Docs Centre \| Docs RIPE RIS Docs Centre Route collectors Route Collection Raw Data: MRT Files RIS Live RISwhois Routing Beacons Historical List of RIS Routing Beacons Prototypes Legal Information # RIPE RIS Docs Centre Welcome to the RIPE RIS Documentation. The Documentation is divided into sections that are featured in the sidebar to the left. You can switch between these sections and items at any time by clicking on the links. You can also use the searchbar above to search for any word or phrase in any document. RIPE RIS is a BGP routing data collection platform, and here we document the various pieces of this pla...

#### `extract_concept_ripe_ris_02`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：8
- matched_terms：collector, collectors, context_2026, data, peer, ripe, ris, view

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_concept_ripe_ris_03`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：4
- matched_terms：all, context_2026, data, not

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
