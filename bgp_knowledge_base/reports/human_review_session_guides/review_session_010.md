# review_session_010 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. RIPE RIS

- 实体 ID：`datasource_ripe_ris`
- 实体类型：DataSource
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

#### `extract_datasource_ripe_ris_01`

- chunk：`ripe_ris_docs_s001_full_001`
- 文档：`ripe_ris_docs`
- source_ref：`raw/data_docs/ripe_ris_docs.html#full`
- section_path：RIPE Atlas docs \| RIPE RIS Docs Centre \| Docs
- match_score：13
- matched_terms：collection, collector, collectors, data, mrt, platform, raw, rib, ripe, ripe_ris_docs

> RIPE Atlas docs \| RIPE RIS Docs Centre \| Docs RIPE RIS Docs Centre Route collectors Route Collection Raw Data: MRT Files RIS Live RISwhois Routing Beacons Historical List of RIS Routing Beacons Prototypes Legal Information # RIPE RIS Docs Centre Welcome to the RIPE RIS Documentation. The Documentation is divided into sections that are featured in the sidebar to the left. You can switch between these sections and items at any time by clicking on the links. You can also use the searchbar above to search for any word or phrase in any document. RIPE RIS is a BGP routing data collection platform, and here we document the various pieces of this pla...

#### `extract_datasource_ripe_ris_02`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：10
- matched_terms：collector, collectors, context_2026, data, datasource, evidence, peer, rib, ripe, ris

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_datasource_ripe_ris_03`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：4
- matched_terms：context_2026, data, evidence, update

> ...es. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. ROA

- 实体 ID：`concept_roa`
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

#### `extract_concept_roa_01`

- chunk：`rfc6811_s003_2_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：8
- matched_terms：can, length, maximum, origin, prefix, rfc6811, rov, rpki

> o Matched: A Route Prefix is said to be Matched by a VRP when the Route Prefix is Covered by that VRP, the Route prefix length is less than or equal to the VRP maximum length, and the Route Origin ASN is equal to the VRP ASN. Given these definitions, any given BGP Route will be found to have one of the following validation states: o NotFound: No VRP Covers the Route Prefix. o Valid: At least one VRP Matches the Route Prefix. o Invalid: At least one VRP Covers the Route Prefix, but no VRP Matches it. We observe that no VRP can have the value "NONE" as its VRP ASN. Thus, a Route whose Origin ASN is "NONE" cannot be Matched by any VRP. Similarly...

#### `extract_concept_roa_02`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：authorization, can, origin, prefix, rfc6811, roa, rpki

> The RPKI system is based on resource certificates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process t...

#### `extract_concept_roa_03`

- chunk：`rfc6811_s003_2_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：7
- matched_terms：length, maximum, origin, prefix, rfc6811, roa, rpki

> ...BGP speaker loads validated objects from the cache into local storage. The objects loaded have the content (IP address, prefix length, maximum length, origin AS number). We refer to such a locally stored object as a "Validated ROA Payload" or "VRP". We define several terms in addition to "VRP". Where these terms are used, they are capitalized: o Prefix: (IP address, prefix length), interpreted as is customary (see [RFC4632]). o Route: Data derived from a received BGP UPDATE, as defined in [RFC4271], Section 1.1. The Route includes one Prefix and an AS_PATH; it may include other attributes to characterize the prefix. o VRP Prefix: The Prefix f...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. roa_status

- 实体 ID：`field_roa_status`
- 实体类型：DataField
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

#### `extract_field_roa_status_01`

- chunk：`rfc6811_s003_2_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：8
- matched_terms：data, invalid, not, origin, result, rfc6811, rov, when

> o Matched: A Route Prefix is said to be Matched by a VRP when the Route Prefix is Covered by that VRP, the Route prefix length is less than or equal to the VRP maximum length, and the Route Origin ASN is equal to the VRP ASN. Given these definitions, any given BGP Route will be found to have one of the following validation states: o NotFound: No VRP Covers the Route Prefix. o Valid: At least one VRP Matches the Route Prefix. o Invalid: At least one VRP Covers the Route Prefix, but no VRP Matches it. We observe that no VRP can have the value "NONE" as its VRP ASN. Thus, a Route whose Origin ASN is "NONE" cannot be Matched by any VRP. Similarly...

#### `extract_field_roa_status_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：7
- matched_terms：as_path, context_2026, data, datafield, evidence, not, origin

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_field_roa_status_03`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：as_path, authorization, data, not, origin, rfc6811, roa

> ...cates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process them. The cache must also be refreshed period...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. Route Collector

- 实体 ID：`concept_route_collector`
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

#### `extract_concept_route_collector_01`

- chunk：`routeviews_api_doc_s001_full_001`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：8
- matched_terms：collector, collectors, information, not, peer, peers, routes, routeviews_api_doc

> ...e # RouteViews API Documentation ## Table of Contents * [Introduction](#introduction) * [Access](#access) * [End points not discoverable from API root](#undiscoverable) * [`/meta/collectors`](#meta_collectors) - metadata about RouteViews BGP collectors and their data availability * [`/asn/`*asn*](#asn) - query routes originated by an Autonomous System * [`/prefix/`*prefix*](#prefix) - query a route (or its parent) in the RIB * [`/rib/collectors`](#rib_collectors) - get list of collectors for which we have current RIB information * [`/rib/peers`](#rib_peers) - near realtime information about peers talking to our collectors * [`/rib/prefixes-fr...

#### `extract_concept_route_collector_02`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：6
- matched_terms：collector, collectors, context_2026, observation, peer, should

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_concept_route_collector_03`

- chunk：`routeviews_api_doc_s001_full_002`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：6
- matched_terms：collector, collectors, global, information, not, routeviews_api_doc

> ...erators and researchers who need to make regular access to _current_ RouteViews data as part of their monitoring of the global routing system. The API is not intended for deep historical queries; the [MRT archive](https://archive.routeviews.org) combined with tools from [BGPKIT](https://bgpkit.com/parser) and [CAIDA](https://bgpstream.caida.org/) are recommended for this use case. Historically the RouteViews collectors have offered command line access for network operators to make quick checks about BGP announcements and general reachability information. However, with the continue growth of the Internet, and the ever increasing size of both t...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. Route Leak

- 实体 ID：`anomaly_route_leak`
- 实体类型：AnomalyType
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

#### `extract_anomaly_route_leak_01`

- chunk：`beam_2024_s003_page_3_001`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-3`
- section_path：Page 3
- match_score：6
- matched_terms：are, beam_2024, expected, leak, propagated, routes

> ...routing anomaly detection system centering around a novel network representation learning model, BEAM (BGP sEmAntics aware network eMbedding). Instead of learning any latent or opaque features, BEAM enables interpretable and accurate routing anomaly detection based on the intrinsic routing characteristics of ASes that are derived from the domain specific knowledge of BGP semantics. Specifically, we propose the concept of AS routing role to meaningfully characterize ASes in BGP route announcements. The design of routing role is derived from the AS business relationship graph (rather than any handcrafted features), because an AS’s business rel...

#### `extract_anomaly_route_leak_02`

- chunk：`beam_2024_s003_page_3_003`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-3`
- section_path：Page 3
- match_score：6
- matched_terms：are, beam_2024, intended, leak, propagated, routes

> L A B C D BGP Route Leak: A C V A H to a.b.c.*/24 better path: H BGP Hijacking: A H fake link ( I ) (II) P2P V H victim hijacker L leaker other AS a.b.c.*/24 path: V a.b.c.*/24 path: B C V a.b.c.*/24 path: H a.b.c.*/24 path: H V to a.b.c.*/24 better path: H V C B a.b.c.*/24 path: C V P2C C B V a.b.c.*/24 path: B C V a.b.c.*/24 path: C V a.b.c.*/24 path: V leaks leaks leaks leaks Figure 1: Illustrations of BGP anomalies. In BGP hijacking, the adversary can either (I) falsely claim the ownership of a prefix, or (II) announce a fake yet more preferable route. In BGP route leak, routes are propagated to unintended ASes. route announcements (about...

#### `extract_anomaly_route_leak_03`

- chunk：`beam_2024_s004_page_4_002`
- 文档：`beam_2024`
- source_ref：`raw/papers/beam_2024.pdf#page-4`
- section_path：Page 4
- match_score：6
- matched_terms：are, beam_2024, intended, leak, valley-free, violation

> The other category of BGP anomalies is route leak: a misbehaved AS propagates BGP announcements to another AS in violation of the intended policies, resulting in traffic forwarded through unintended links. The Gao-Rexford model [30] describes the restrictions on BGP route propagation and can be used to identify BGP route leak ( i.e., the valley-free criterion). For example, in 2019, AS 21217 (Safe Host) broke the valley-free criterion by propagating announcements received from its providers ( e.g., AS 13237 ( euNetworks GmbH)) to another provider AS 4134 (China Telecom), redirecting large amounts of Internet traffic destined for European mobi...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. Route Origin Validation

- 实体 ID：`mechanism_route_origin_validation`
- 实体类型：RoutingMechanism
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

#### `extract_mechanism_route_origin_validation_01`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：11
- matched_terms：as_path, data, not, origin, prefix, rfc6811, roa, rpki, valid, validate

> The RPKI system is based on resource certificates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process t...

#### `extract_mechanism_route_origin_validation_02`

- chunk：`rfc6811_s008_6_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#6`
- section_path：Security Considerations
- match_score：11
- matched_terms：data, does, invalid, not, origin, prefix, rfc6811, rpki, valid, validate

> Although this specification discusses one portion of a system to validate BGP routes, it should be noted that it relies on a database (RPKI or other) to provide validation information. As such, the security properties of that database must be considered in order to determine the security provided by the overall solution. If "invalid" routes are blocked as this specification suggests, the overall system provides a possible denial-of-service vector; for Mohapatra, et al. Standards Track [Page 7] RFC 6811 BGP Prefix Origin Validation January 2013 example, if an attacker is able to inject (or remove) one or more records into (or from) the validat...

#### `extract_mechanism_route_origin_validation_03`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：10
- matched_terms：as_path, data, origin, prefix, rfc6811, roa, rpki, valid, validate, validation

> A BGP route associates an address prefix with a set of Autonomous Systems (ASes) that identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP ro...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. RouteViews

- 实体 ID：`concept_routeviews`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `routeviews_api_doc`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/routeviews_api_doc.md`

### parsed 路径

- `parsed/data_docs/routeviews_api_doc.json`

### Top 摘录

#### `extract_concept_routeviews_01`

- chunk：`routeviews_api_doc_s001_full_002`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：10
- matched_terms：collector, collectors, data, global, information, mrt, rib, routeviews, routeviews_api_doc, update

> The RouteViews API is intended for network operators and researchers who need to make regular access to _current_ RouteViews data as part of their monitoring of the global routing system. The API is not intended for deep historical queries; the [MRT archive](https://archive.routeviews.org) combined with tools from [BGPKIT](https://bgpkit.com/parser) and [CAIDA](https://bgpstream.caida.org/) are recommended for this use case. Historically the RouteViews collectors have offered command line access for network operators to make quick checks about BGP announcements and general reachability information. However, with the continue growth of the Int...

#### `extract_concept_routeviews_02`

- chunk：`routeviews_api_doc_s001_full_018`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：10
- matched_terms：collector, data, global, information, oregon, peers, project, routeviews, routeviews_api_doc, university

> ```json [ { "asn": 7594, "addr": "45.127.173.66", "collector": "route-views.sydney", "prefix_count": 983449 }, { "asn": 7594, "addr": "2001:de8:6::7594:1", "collector": "route-views.sydney", "prefix_count": 214911 }, { "asn": 24115, "addr": "45.127.172.122", "collector": "route-views.sydney", "prefix_count": 62 }, { "asn": 24115, "addr": "45.127.172.123", "collector": "route-views.sydney", "prefix_count": 62 } ] ``` AS7594 provides a full BGP table (~983k IPv4 and ~215k IPv6 prefixes). Additionally, limited prefixes (62 each) from AS7594 are observed via peers with ASN 24115, indicating these peers are likely route servers. **Notes** * `prefi...

#### `extract_concept_routeviews_03`

- chunk：`routeviews_api_doc_s001_full_001`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：9
- matched_terms：collector, collectors, data, information, its, peers, rib, routeviews, routeviews_api_doc

> RouteViews API Documentation API Home Documentation Playground Member area Version: v0.10.2-129-g07aea9e # RouteViews API Documentation ## Table of Contents * [Introduction](#introduction) * [Access](#access) * [End points not discoverable from API root](#undiscoverable) * [`/meta/collectors`](#meta_collectors) - metadata about RouteViews BGP collectors and their data availability * [`/asn/`*asn*](#asn) - query routes originated by an Autonomous System * [`/prefix/`*prefix*](#prefix) - query a route (or its parent) in the RIB * [`/rib/collectors`](#rib_collectors) - get list of collectors for which we have current RIB information * [`/rib/pee...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. RouteViews

- 实体 ID：`datasource_routeviews`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `routeviews_api_doc`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/routeviews_api_doc.md`

### parsed 路径

- `parsed/data_docs/routeviews_api_doc.json`

### Top 摘录

#### `extract_datasource_routeviews_01`

- chunk：`routeviews_api_doc_s001_full_001`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：12
- matched_terms：api, asn, collector, data, information, metadata, peer, peers, prefix, rib

> RouteViews API Documentation API Home Documentation Playground Member area Version: v0.10.2-129-g07aea9e # RouteViews API Documentation ## Table of Contents * [Introduction](#introduction) * [Access](#access) * [End points not discoverable from API root](#undiscoverable) * [`/meta/collectors`](#meta_collectors) - metadata about RouteViews BGP collectors and their data availability * [`/asn/`*asn*](#asn) - query routes originated by an Autonomous System * [`/prefix/`*prefix*](#prefix) - query a route (or its parent) in the RIB * [`/rib/collectors`](#rib_collectors) - get list of collectors for which we have current RIB information * [`/rib/pee...

#### `extract_datasource_routeviews_02`

- chunk：`routeviews_api_doc_s001_full_004`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：11
- matched_terms：api, collector, data, dump, endpoints, information, metadata, rib, routeviews, routeviews_api_doc

> There are several endpoints not currently discoverable from the API root in the Django testing playground at https://api.routeviews.org/guest/. These endpoints provide access to various types of data including collector metadata, near realtime RIB data (the same data that is streamed via our Kafka feed), and RPKI validation information. ### Collectors Metadata The collectors metadata endpoint provides comprehensive information about all RouteViews BGP collectors, including their data availability periods, dump schedules, and access URLs for both RIB and UPDATE data. ```sh curl -L -s "https://api.routeviews.org/meta/collectors" \| jq . ``` whic...

#### `extract_datasource_routeviews_03`

- chunk：`routeviews_api_doc_s001_full_005`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：11
- matched_terms：api, asn, collector, data, dump, information, metadata, rib, routeviews, routeviews_api_doc

> - **project**: Always "routeviews" for RouteViews collectors - **baseURL**: Direct URL to the collector's archive directory - **kafkaTopics**: Regular expression pattern for Kafka topic names streaming this collector's data - **dataTypes**: Information about available data types: - **ribs**: Routing Information Base dumps - **dumpPeriod**: Time between dumps in seconds (7200 = 2 hours) - **dumpDuration**: Expected dump duration in seconds (120 = 2 minutes) - **oldestDumpTime**: Unix timestamp of oldest available RIB dump - **latestDumpTime**: Unix timestamp of most recent RIB dump - **latestDumpFile**: Direct download URL for latest RIB dump...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. ROV

- 实体 ID：`concept_rov`
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

#### `extract_concept_rov_01`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：9
- matched_terms：authorization, data, not, origin, path, rfc6811, roa, rpki, validation

> The RPKI system is based on resource certificates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process t...

#### `extract_concept_rov_02`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：8
- matched_terms：authorized, data, origin, path, rfc6811, roa, rpki, validation

> A BGP route associates an address prefix with a set of Autonomous Systems (ASes) that identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP ro...

#### `extract_concept_rov_03`

- chunk：`rfc6811_s008_6_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#6`
- section_path：Security Considerations
- match_score：8
- matched_terms：data, not, origin, path, rfc6811, rov, rpki, validation

> Although this specification discusses one portion of a system to validate BGP routes, it should be noted that it relies on a database (RPKI or other) to provide validation information. As such, the security properties of that database must be considered in order to determine the security provided by the overall solution. If "invalid" routes are blocked as this specification suggests, the overall system provides a possible denial-of-service vector; for Mohapatra, et al. Standards Track [Page 7] RFC 6811 BGP Prefix Origin Validation January 2013 example, if an attacker is able to inject (or remove) one or more records into (or from) the validat...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. RPKI

- 实体 ID：`concept_rpki`
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

#### `extract_concept_rpki_01`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：13
- matched_terms：as_path, holder, infrastructure, key, number, origin, public, resource, rfc6811, roa

> ...identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP route) is in fact authorized by the prefix holder to do so. This document describes a si...

#### `extract_concept_rpki_02`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：10
- matched_terms：as_path, internet, not, origin, resource, rfc6811, roa, rpki, validate, validation

> The RPKI system is based on resource certificates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process t...

#### `extract_concept_rpki_03`

- chunk：`rfc6811_s008_6_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#6`
- section_path：Security Considerations
- match_score：8
- matched_terms：does, information, not, origin, rfc6811, rpki, validate, validation

> Although this specification discusses one portion of a system to validate BGP routes, it should be noted that it relies on a database (RPKI or other) to provide validation information. As such, the security properties of that database must be considered in order to determine the security provided by the overall solution. If "invalid" routes are blocked as this specification suggests, the overall system provides a possible denial-of-service vector; for Mohapatra, et al. Standards Track [Page 7] RFC 6811 BGP Prefix Origin Validation January 2013 example, if an attacker is able to inject (or remove) one or more records into (or from) the validat...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
