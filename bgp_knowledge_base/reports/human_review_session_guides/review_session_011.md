# review_session_011 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. RPKI / ROA

- 实体 ID：`datasource_rpki_roa`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`
- `routeviews_api_doc`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/routeviews_api_doc.md`
- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/data_docs/routeviews_api_doc.json`
- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_datasource_rpki_roa_01`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：10
- matched_terms：authorization, data, not, origin, prefix, rfc6811, roa, rpki, state, validation

> The RPKI system is based on resource certificates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process t...

#### `extract_datasource_rpki_roa_02`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：9
- matched_terms：authorize, data, origin, originate, prefix, rfc6811, roa, rpki, validation

> A BGP route associates an address prefix with a set of Autonomous Systems (ASes) that identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP ro...

#### `extract_datasource_rpki_roa_03`

- chunk：`rfc6811_s003_2_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：9
- matched_terms：data, origin, payload, prefix, rfc6811, roa, rpki, validated, validation

> The BGP speaker loads validated objects from the cache into local storage. The objects loaded have the content (IP address, prefix length, maximum length, origin AS number). We refer to such a locally stored object as a "Validated ROA Payload" or "VRP". We define several terms in addition to "VRP". Where these terms are used, they are capitalized: o Prefix: (IP address, prefix length), interpreted as is customary (see [RFC4632]). o Route: Data derived from a received BGP UPDATE, as defined in [RFC4271], Section 1.1. The Route includes one Prefix and an AS_PATH; it may include other attributes to characterize the prefix. o VRP Prefix: The Pref...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. Short route flap

- 实体 ID：`fp_short_route_flap`
- 实体类型：FalsePositivePattern
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

#### `extract_fp_short_route_flap_01`

- chunk：`rfc4271_s066_9_1_4_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1.4`
- section_path：Overlapping Routes
- match_score：5
- matched_terms：may, reachability, rfc4271, short, than

> A BGP speaker may transmit routes with overlapping Network Layer Reachability Information (NLRI) to another BGP speaker. NLRI overlap occurs when a set of destinations are identified in non-matching multiple routes. Because BGP encodes NLRI using IP prefixes, overlap will always exhibit subset relationships. A route describing a smaller set of destinations (a longer prefix) is said to be more specific than a route describing a larger set of destinations (a shorter prefix); similarly, a route describing a larger set of destinations is said to be less specific than a route describing a smaller set of destinations. The precedence relationship ef...

#### `extract_fp_short_route_flap_02`

- chunk：`rfc4271_s058_8_2_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#8.2.2`
- section_path：Finite State Machine
- match_score：4
- matched_terms：changes, may, rfc4271, short

> Idle state: Initially, the BGP peer FSM is in the Idle state. Hereafter, the BGP peer FSM will be shortened to BGP FSM. In this state, BGP FSM refuses all incoming BGP connections for this peer. No resources are allocated to the peer. In response to a ManualStart event (Event 1) or an AutomaticStart event (Event 3), the local system: - initializes all BGP resources for the peer connection, - sets ConnectRetryCounter to zero, - starts the ConnectRetryTimer with the initial value, - initiates a TCP connection to the other BGP peer, - listens for a connection that may be initiated by the remote BGP peer, and - changes its state to Connect. The M...

#### `extract_fp_short_route_flap_03`

- chunk：`rfc4271_s069_9_2_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.2.1.1`
- section_path：Frequency of Route Advertisement
- match_score：4
- matched_terms：outage, rfc4271, short, than

> ...needed within an autonomous system, either (a) the MinRouteAdvertisementIntervalTimer used for internal peers SHOULD be shorter than the MinRouteAdvertisementIntervalTimer used for external peers, or (b) the procedure describe in this section SHOULD NOT apply to routes sent to internal peers. This procedure does not limit the rate of route selection, but only the rate of route advertisement. If new routes are selected multiple times while awaiting the expiration of MinRouteAdvertisementIntervalTimer, the last route selected SHALL be advertised at the end of MinRouteAdvertisementIntervalTimer.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. Single collector bias

- 实体 ID：`fp_single_collector_bias`
- 实体类型：FalsePositivePattern
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

#### `extract_fp_single_collector_bias_01`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：7
- matched_terms：collector, collectors, context_2026, coverage, missing, peer, views

> ...ranularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_fp_single_collector_bias_02`

- chunk：`routeviews_api_doc_s001_full_007`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：7
- matched_terms：collector, peer, peers, report, routeviews_api_doc, single, views

> ```json [ { "prefix": "128.223.0.0/16", "origin_asn": 3582, "rpki_state": "not-found", "rpki_roas": null, "reporting_peers": [ { "peer_asn": 267613, "peer_addr": "195.66.226.39", "collector": "route-views.linx", "as_path": "267613 52320 6461 11164 3701 3582 3582 3582 3582 3582 3582", "communities": "5469:11000 5469:10850 5469:2200", "timestamp": "2024-07-09T10:00:06Z" }, { "peer_asn": 1031, "peer_addr": "195.66.231.48", "collector": "route-views.linx", "as_path": "6447 1031 174 3701 3701 3701 3701 3582 3582 3582 3582 3582 3582", "communities": "1031:701 1031:800 1031:802", "timestamp": "2024-07-12T02:47:21Z" }, ... { "peer_asn": 34177, "peer_...

#### `extract_fp_single_collector_bias_03`

- chunk：`routeviews_api_doc_s001_full_001`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：6
- matched_terms：collector, collectors, peer, peers, routeviews_api_doc, views

> RouteViews API Documentation API Home Documentation Playground Member area Version: v0.10.2-129-g07aea9e # RouteViews API Documentation ## Table of Contents * [Introduction](#introduction) * [Access](#access) * [End points not discoverable from API root](#undiscoverable) * [`/meta/collectors`](#meta_collectors) - metadata about RouteViews BGP collectors and their data availability * [`/asn/`*asn*](#asn) - query routes originated by an Autonomous System * [`/prefix/`*prefix*](#prefix) - query a route (or its parent) in the RIB * [`/rib/collectors`](#rib_collectors) - get list of collectors for which we have current RIB information * [`/rib/pee...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. Subprefix Hijack

- 实体 ID：`anomaly_subprefix_hijack`
- 实体类型：AnomalyType
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`
- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bear_2025.md`
- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/papers/bear_2025.json`
- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_anomaly_subprefix_hijack_01`

- chunk：`bear_2025_s001_page_1_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-1`
- section_path：Page 1
- match_score：4
- matched_terms：bear_2025, hijack, prefix, traffic

> ...ems (AS) that rely on the Border Gateway Protocol (BGP) for inter-domain routing. BGP anomalies—such as route leaks and hijacks—can divert traffic through unauthorized or inefficient paths, jeopardizing network reliability and security. Although existing rule-based and machine learning methods can detect these anomalies using structured metrics, they still require experts with indepth BGP knowledge of, for example, AS relationships and historical incidents, to interpret events and propose remediation. In this paper, we introduce BEAR (BGP Event Analysis and Reporting), a novel framework that leverages large language models (LLMs) to automatic...

#### `extract_anomaly_subprefix_hijack_02`

- chunk：`bear_2025_s002_page_2_002`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-2`
- section_path：Page 2
- match_score：4
- matched_terms：bear_2025, hijack, prefix, victim

> ...ate high-quality synthetic events, we leverage an LLM to produce specific details of an anomaly, such as the timestamp, victim IP prefix, event type, hijacker or route leaker, AS path after the event, and detection rate. Using the generated details, we extract relevant BGP data from an existing BGP dataset based on the timestamp and victim IP prefix. This data is then modified according to the LLM-specified details, creating synthetic BGP data that simulates the occurrence of an anomaly event. This method produces high-quality synthetic events. We evaluate BEAR on both real-world BGP anomaly events, including many recent incidents, and synthe...

#### `extract_anomaly_subprefix_hijack_03`

- chunk：`bear_2025_s007_page_7_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-7`
- section_path：Page 7
- match_score：4
- matched_terms：bear_2025, hijack, prefix, when

> Fig. 9. An example report for a BGP hijack event. In this report, BEAR not only identifies the event type but also detects the hijacked sub-prefix. are the most common prompt engineering methods in natural language processing. In the CoT reasoning baseline, we provide definitions for both BGP hijack and BGP route leak, instructing the LLM to explain its reasoning when inferring the event type, thereby encouraging a step-by-step thought process. For the in-context learning baseline, we present the LLM with four synthetic examples of BGP data generated by our synthetic BGP event generation framework. Each example corresponds to a specific event...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. timestamp

- 实体 ID：`field_timestamp`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `bgpstream_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`

### Top 摘录

#### `extract_field_timestamp_01`

- chunk：`bgpstream_docs_s001_full_001`
- 文档：`bgpstream_docs`
- source_ref：`raw/tools_docs/bgpstream_docs.html#full`
- section_path：BGPStream
- match_score：4
- matched_terms：bgpstream_docs, data, local, record

> BGPStream Toggle navigation Home News Components Download Documentation Publications Data Providers Acknowledgements Contact Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutorials BGPReader libBGPStream PyBGPStream Docker Data Encoding Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutoria...

#### `extract_field_timestamp_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：4
- matched_terms：context_2026, data, datafield, update

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_field_timestamp_03`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：4
- matched_terms：context_2026, data, rib, time

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. update_type

- 实体 ID：`field_update_type`
- 实体类型：DataField
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

#### `extract_field_update_type_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：5
- matched_terms：analysis, before, context_2026, event, evidence

> Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_field_update_type_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：4
- matched_terms：context_2026, datafield, evidence, update

> ...es. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_field_update_type_03`

- chunk：`context_2026_paper_bear_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 论文方法知识`
- section_path：BGP 论文方法知识
- match_score：4
- matched_terms：before, context_2026, event, evidence

> BEAR is treated as a method source for BGP anomaly event explanation. The knowledge base should extract its research problem, input data, core concepts, method process, outputs, applicable anomaly types, dependent data sources, strengths, limitations, and reusable evidence templates.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. Valley-free

- 实体 ID：`concept_valley_free`
- 实体类型：BGPConcept
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

#### `extract_concept_valley_free_01`

- chunk：`caida_as_relationships_s001_full_003`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：8
- matched_terms：are, caida_as_relationships, data, not, path, relationship, relationships, require

> Accurate data on the structure of actual relationships among ASes is required for many research efforts concerned with performance, robustness, and evolution of the global Internet. Examples of both research and operational tasks that cannot neglect AS relationships include: realistic simulations trying to model path inflation effects caused by routing policies; understanding how packets are routed in the Internet and how to optimize Internet paths by analyzing existing deficiencies; development of more scalable interdomain routing protocols and architectures, like HLP , that take into account the structure of AS relationships to optimize the...

#### `extract_concept_valley_free_02`

- chunk：`caida_as_relationships_s001_full_007`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：8
- matched_terms：are, caida_as_relationships, data, not, path, relationship, relationships, valley-free

> ...tion, like the random breaking of ties which can yield obviously incorrect inferences, e.g., well-known large providers are inferred as customers of small ASes. In the first paper 6 we handled this issue with multiobjective optimization techniques that incorporated AS degree into the inference. In a subsequent paper 7 we introduced improved algorithms that determine not only c2p but also p2p links (for those we can detect from BGP data). These improvements achieved more accurate AS relationship inferences, which we demonstrate against ground truth for a set of ASes. Benjamin Hummel and Sven Kosub 8 introduced the idea that the resulting graph...

#### `extract_concept_valley_free_03`

- chunk：`caida_as_relationships_s001_full_012`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：8
- matched_terms：are, caida_as_relationships, data, not, path, provider-customer, relationship, relationships

> Serial-1 data is available from 1998 to present, with one file created per month. Each file contains a full AS graph derived from RouteViews and RIPE RIS BGP table snapshots taken at 24-hour intervals over a 5-day period. The AS relationships available are customer-provider (and provider-customer in the opposite direction), and peer-to-peer. See the README in the Serial-1 data directory for details of the file formats. The general serial-1 procedure for creating a file is as follows: Extract and clean AS paths from the BGP table snapshots. Infer the ASes that form a clique of transit-free networks at the top of the AS topology (Tier-1 ASes),...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. Valley-free Routing

- 实体 ID：`mechanism_valley_free`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc7908`
- `caida_as_relationships`
- `beam_2024`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`
- `cleaned/papers/beam_2024.md`
- `cleaned/standards/rfc7908.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`
- `parsed/papers/beam_2024.json`
- `parsed/standards/rfc7908.json`

### Top 摘录

#### `extract_mechanism_valley_free_01`

- chunk：`beam_2024_s004_page_4_001`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-4`
- section_path：Page 4
- match_score：7
- matched_terms：beam_2024, graph, may, path, policy, relationship, relationships

> its routing policy, may stop further propagating the announcement, or append its ASN to the AS-path and send the updated announcement to a selective set of neighbors. Business relationship largely determines one AS’s routing policy [30, 32]. Two neighboring ASes typically have three types of business relationships2: provider-to-customer (P2C), peer-to-peer (P2P) and customer-to-provider (C2P), where a customer AS pays its provider for connectivity while two peering ASes forward traffic to each other free of charge. Thus, the inter-domain routing system of the Internet can be reconstructed as an AS graph based on AS relationships. This AS-leve...

#### `extract_mechanism_valley_free_02`

- chunk：`beam_2024_s005_page_5_001`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-5`
- section_path：Page 5
- match_score：6
- matched_terms：beam_2024, expected, graph, policy, relationship, relationships

> ...te representation of ASes’ routing roles. Applying network representation learning, rather than using “raw” AS business relationships, is essential to characterize ASes’ routing roles. In particular, our network representation learning model can capture the global routing characteristics of each AS and translate them into embedding vectors, while the original AS business relationships can only indicate the local routing policy between two directly connected ASes. Further, with the embedding vectors, we can quantify the difference in routing roles between any pair of ASes, regardless of whether they are connected or not. This enables us to det...

#### `extract_mechanism_valley_free_03`

- chunk：`beam_2024_s004_page_4_002`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-4`
- section_path：Page 4
- match_score：5
- matched_terms：beam_2024, behavior, relationship, relationships, valley-free

> ...d model [30] describes the restrictions on BGP route propagation and can be used to identify BGP route leak ( i.e., the valley-free criterion). For example, in 2019, AS 21217 (Safe Host) broke the valley-free criterion by propagating announcements received from its providers ( e.g., AS 13237 ( euNetworks GmbH)) to another provider AS 4134 (China Telecom), redirecting large amounts of Internet traffic destined for European mobile networks through China Telecom [1]. 3 Semantics Aware Analysis 3.1 BEAM Overview We propose a novel network representation learning model, BEAM, to learn the routing roles of ASes. The routing roles meaningfully chara...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. Vantage Point

- 实体 ID：`concept_vantage_point`
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

#### `extract_concept_vantage_point_01`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：4
- matched_terms：collector, context_2026, coverage, peer

> ...ranularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_concept_vantage_point_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：3
- matched_terms：context_2026, may, path

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_concept_vantage_point_03`

- chunk：`context_2026_paper_bear_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 论文方法知识`
- section_path：BGP 论文方法知识
- match_score：3
- matched_terms：anomaly, context_2026, path

> BEAR is treated as a method source for BGP anomaly event explanation. The knowledge base should extract its research problem, input data, core concepts, method process, outputs, applicable anomaly types, dependent data sources, strengths, limitations, and reusable evidence templates.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. Vodafone Idea AS55410 Route Leak

- 实体 ID：`case_vodafone_2021_route_leak`
- 实体类型：Case
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `bgpshield_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bgpshield_2025.md`

### parsed 路径

- `parsed/papers/bgpshield_2025.json`

### Top 摘录

#### `extract_case_vodafone_2021_route_leak_01`

- chunk：`bgpshield_2025_s012_page_12_003`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-12`
- section_path：Page 12
- match_score：10
- matched_terms：24.152.117.0/24, as55410, bgpshield_2025, case, historical, idea, leak, path, prefix, updated

> In this case, the key ASes include: •AS270497 (RUTE MARIA DA CUNHA): The legitimate origin AS claiming ownership of prefix 24.152.117.0/24 •AS55410 (V odafone Idea Ltd.): The leak source, becoming the new origin AS. To analyze this incident, BGPShield’s LSE (detailed in Sec.4.2 ) first processes multi-source data to generate highdimensional semantic embeddings for ASes. These embeddings are subsequently processed through CDR (detailed in Sec.4.2.3) for optimization, providing informative representations for BAD (detailed in Sec.4.3). Anomaly Detection. Based on the embeddings, BAD further processes BGP updates for prefix 24.152.117.0/24, wher...

#### `extract_case_vodafone_2021_route_leak_02`

- chunk：`bgpshield_2025_s012_page_12_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-12`
- section_path：Page 12
- match_score：8
- matched_terms：24.152.117.0/24, as55410, bgpshield_2025, case, idea, leak, path, prefix

> ...n smaller reductions of 0.4% and 0.6% respectively. This pattern reflects that while complete structural information is ideal, the semantic richness of our embeddings provides substantial redundancy against missing or incorrect topological data. The consistent high performance under extreme noise conditions demonstrates the practical superiority of BGPShield. Real-world AS relationship inference typically exhibits much lower error rates than our tested extreme conditions, suggesting that BGPShield’s semantic embeddings can maintain effective in evolving operational environments over the long term. 6. Case Study Case Background and Data Prepar...

#### `extract_case_vodafone_2021_route_leak_03`

- chunk：`bgpshield_2025_s013_page_13_001`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-13`
- section_path：Page 13
- match_score：8
- matched_terms：24.152.117.0/24, as55410, bgpshield_2025, case, historical, path, prefix, updated

> L2PairwiseDistanceVisualization of RoutingPaths L2PairwiseDistanceVisualization of RoutingPaths Legitimate Route ChangeHistoricalPREFIX: 35.206.9.0/24 UpdatedPREFIX: 24.152.117.0/24Anomalous Route ChangeHistoricalPATH: 2497 174 28598 263362 263362 263362 270497UpdatedPATH: 2497 9498 55410 55410 55410 HistoricalPATH: 14061 1299 15169UpdatedPATH: 14061 2914 6453 19527UpdatedPREFIX: 35.206.9.0/24 HistoricalPREFIX:24.152.117.0/24 Figure 8:Comparison of Legitimate and Anomalous BGP Route Changes Detected by BAD.L2 Pairwise Distance d(left) show similarity between AS pairs (smaller distances indicate higher similarity), whilepath visualizations(rig...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
