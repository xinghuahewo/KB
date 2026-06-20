# review_session_004 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. vrp_asn

- 实体 ID：`field_vrp_asn`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`

### cleaned 路径

- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_field_vrp_asn_01`

- chunk：`rfc6811_s003_2_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：10
- matched_terms：as_path, asn, covered, number, origin, payload, rfc6811, roa, validated, vrp

> The BGP speaker loads validated objects from the cache into local storage. The objects loaded have the content (IP address, prefix length, maximum length, origin AS number). We refer to such a locally stored object as a "Validated ROA Payload" or "VRP". We define several terms in addition to "VRP". Where these terms are used, they are capitalized: o Prefix: (IP address, prefix length), interpreted as is customary (see [RFC4632]). o Route: Data derived from a received BGP UPDATE, as defined in [RFC4271], Section 1.1. The Route includes one Prefix and an AS_PATH; it may include other attributes to characterize the prefix. o VRP Prefix: The Pref...

#### `extract_field_vrp_asn_02`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：8
- matched_terms：against, as_path, ases, authorized, number, origin, rfc6811, roa

> A BGP route associates an address prefix with a set of Autonomous Systems (ASes) that identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP ro...

#### `extract_field_vrp_asn_03`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：against, as_path, ases, authorization, origin, rfc6811, roa

> ...cates that define extensions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process them. The cache must also be refreshed period...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. vrp_max_length

- 实体 ID：`field_vrp_max_length`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`

### cleaned 路径

- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_field_vrp_max_length_01`

- chunk：`rfc6811_s003_2_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：13
- matched_terms：all, its, length, max, origin, payload, prefix, rfc6811, roa, valid

> The BGP speaker loads validated objects from the cache into local storage. The objects loaded have the content (IP address, prefix length, maximum length, origin AS number). We refer to such a locally stored object as a "Validated ROA Payload" or "VRP". We define several terms in addition to "VRP". Where these terms are used, they are capitalized: o Prefix: (IP address, prefix length), interpreted as is customary (see [RFC4632]). o Route: Data derived from a received BGP UPDATE, as defined in [RFC4271], Section 1.1. The Route includes one Prefix and an AS_PATH; it may include other attributes to characterize the prefix. o VRP Prefix: The Pref...

#### `extract_field_vrp_max_length_02`

- chunk：`rfc6811_s003_2_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：10
- matched_terms：all, its, length, max, origin, prefix, rfc6811, valid, vrp, when

> o Matched: A Route Prefix is said to be Matched by a VRP when the Route Prefix is Covered by that VRP, the Route prefix length is less than or equal to the VRP maximum length, and the Route Origin ASN is equal to the VRP ASN. Given these definitions, any given BGP Route will be found to have one of the following validation states: o NotFound: No VRP Covers the Route Prefix. o Valid: At least one VRP Matches the Route Prefix. o Invalid: At least one VRP Covers the Route Prefix, but no VRP Matches it. We observe that no VRP can have the value "NONE" as its VRP ASN. Thus, a Route whose Origin ASN is "NONE" cannot be Matched by any VRP. Similarly...

#### `extract_field_vrp_max_length_03`

- chunk：`rfc6811_s004_2_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2.1`
- section_path：Pseudo-Code
- match_score：8
- matched_terms：all, length, max, origin, prefix, rfc6811, valid, vrp

> ...ve, rather than the pseudo-code, should be taken as authoritative. result = BGP_PFXV_STATE_NOT_FOUND; //Iterate through all the Covering entries in the local VRP //database, pfx_validate_table. entry = next_lookup_result(pfx_validate_table, route_prefix); while (entry != NULL) { prefix_exists = TRUE; if (route_prefix_length <= entry->max_length) { if (route_origin_as != NONE && entry->origin_as != 0 && route_origin_as == entry->origin_as) { result = BGP_PFXV_STATE_VALID; return (result); } } entry = next_lookup_result(pfx_validate_table, input.prefix); } //If one or more VRP entries Covered the route prefix, but //none Matched, return "Invali...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. vrp_prefix

- 实体 ID：`field_vrp_prefix`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc6811`

### cleaned 路径

- `cleaned/standards/rfc6811.md`

### parsed 路径

- `parsed/standards/rfc6811.json`

### Top 摘录

#### `extract_field_vrp_prefix_01`

- chunk：`rfc6811_s003_2_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：12
- matched_terms：are, bits, cover, covered, origin, payload, prefix, rfc6811, roa, validated

> The BGP speaker loads validated objects from the cache into local storage. The objects loaded have the content (IP address, prefix length, maximum length, origin AS number). We refer to such a locally stored object as a "Validated ROA Payload" or "VRP". We define several terms in addition to "VRP". Where these terms are used, they are capitalized: o Prefix: (IP address, prefix length), interpreted as is customary (see [RFC4632]). o Route: Data derived from a received BGP UPDATE, as defined in [RFC4271], Section 1.1. The Route includes one Prefix and an AS_PATH; it may include other attributes to characterize the prefix. o VRP Prefix: The Pref...

#### `extract_field_vrp_prefix_02`

- chunk：`rfc6811_s003_2_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：9
- matched_terms：are, cover, covered, matches, origin, prefix, rfc6811, vrp, when

> o Matched: A Route Prefix is said to be Matched by a VRP when the Route Prefix is Covered by that VRP, the Route prefix length is less than or equal to the VRP maximum length, and the Route Origin ASN is equal to the VRP ASN. Given these definitions, any given BGP Route will be found to have one of the following validation states: o NotFound: No VRP Covers the Route Prefix. o Valid: At least one VRP Matches the Route Prefix. o Invalid: At least one VRP Covers the Route Prefix, but no VRP Matches it. We observe that no VRP can have the value "NONE" as its VRP ASN. Thus, a Route whose Origin ASN is "NONE" cannot be Matched by any VRP. Similarly...

#### `extract_field_vrp_prefix_03`

- chunk：`rfc6811_s003_2_003`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#2`
- section_path：Prefix-to-AS Mapping Database
- match_score：6
- matched_terms：cover, covered, origin, prefix, rfc6811, vrp

> We observe that a Route can be Matched or Covered by more than one VRP. This procedure does not mandate an order in which VRPs must be visited; however, the validation state output is fully determined. Mohapatra, et al. Standards Track [Page 5] RFC 6811 BGP Prefix Origin Validation January 2013

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. withdrawn_routes

- 实体 ID：`field_withdrawn_routes`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`

### cleaned 路径

- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_field_withdrawn_routes_01`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：8
- matched_terms：nlri, peer, prefix, prefixes, rfc4271, routes, update, withdrawn

> ...of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the NLRI field of the UPDATE message. Routes are stored in the Routing Information Bases (RIBs): namely, the Adj-RIBs-In, the Loc-RIB,...

#### `extract_field_withdrawn_routes_02`

- chunk：`rfc4271_s059_9_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9`
- section_path：UPDATE Message Handling
- match_score：7
- matched_terms：nlri, prefix, prefixes, rfc4271, routes, update, withdrawn

> An UPDATE message may be received only in the Established state. Receiving an UPDATE message in any other state is an error. When an UPDATE message is received, each field is checked for validity, as specified in Section 6.3. If an optional non-transitive attribute is unrecognized, it is quietly ignored. If an optional transitive attribute is unrecognized, the Partial bit (the third high-order bit) in the attribute flags octet is set to 1, and the attribute is retained for propagation to other BGP speakers. If an optional attribute is recognized and has a valid value, then, depending on the type of the optional attribute, it is processed loca...

#### `extract_field_withdrawn_routes_03`

- chunk：`rfc4271_s061_9_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1.1`
- section_path：Phase 1: Calculation of Degree of Preference
- match_score：7
- matched_terms：newly, peer, rfc4271, routes, separate, update, withdrawn

> The Phase 1 decision function is invoked whenever the local BGP speaker receives, from a peer, an UPDATE message that advertises a new route, a replacement route, or withdrawn routes. The Phase 1 decision function is a separate process,f which completes when it has no further work to do. The Phase 1 decision function locks an Adj-RIB-In prior to operating on any route contained within it, and unlocks it after operating on all new or unfeasible routes contained within it. For each newly received or replacement feasible route, the local BGP speaker determines a degree of preference as follows: If the route is learned from an internal peer, eith...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. Announcement

- 实体 ID：`concept_announcement`
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

#### `extract_concept_announcement_01`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：7
- matched_terms：as_path, context_2026, not, origin, path, prefix, update

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_concept_announcement_02`

- chunk：`rfc4271_s005_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：as_path, information, not, path, prefix, reachability, rfc4271

> ...P) is an inter-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity for this reachability, from which routing loops may be pruned and, at the AS level, some policy decisions may be enforced. BGP-4 provides a set of mechanisms for supporting Classless Inter- Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support...

#### `extract_concept_announcement_03`

- chunk：`rfc4271_s076_10_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#10`
- section_path：BGP Timers
- match_score：7
- matched_terms：as_path, information, not, path, prefix, rfc4271, update

> The relationship between the immediate next hop, and the next hop as specified in the NEXT_HOP path attribute. Clarification of the tie-breaking procedures. Clarification of the frequency of route advertisements. Optional Parameter Type 1 (Authentication Information) has been deprecated. UPDATE Message Error subcode 7 (AS Routing Loop) has been deprecated. OPEN Message Error subcode 5 (Authentication Failure) has been deprecated. Use of the Marker field for authentication has been deprecated. Implementations MUST support TCP MD5 [RFC2385] for authentication. Clarification of BGP FSM. Rekhter, et al. Standards Track [Page 92] RFC 4271 BGP-4 Ja...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. anomaly_moas

- 实体 ID：`evidence_moas`
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

#### `extract_evidence_moas_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：3
- matched_terms：context_2026, evidencetemplate, prefix

> ...t AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_evidence_moas_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：2
- matched_terms：context_2026, prefix

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_evidence_moas_03`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：2
- matched_terms：prefix, rfc6811

> A BGP route associates an address prefix with a set of Autonomous Systems (ASes) that identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP ro...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. anomaly_origin_change

- 实体 ID：`evidence_origin_change`
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

#### `extract_evidence_origin_change_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：4
- matched_terms：change, context_2026, evidencetemplate, prefix

> ...t AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_evidence_origin_change_02`

- chunk：`rfc6811_s001_1_001`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：4
- matched_terms：announcement, prefix, rfc6811, roa

> A BGP route associates an address prefix with a set of Autonomous Systems (ASes) that identify the interdomain path the prefix has traversed in the form of BGP announcements. This set is represented as the AS_PATH attribute in BGP [RFC4271] and starts with the AS that originated the prefix. To help reduce well-known threats against BGP including prefix mis-announcing and monkey-in-the-middle attacks, one of the security requirements is the ability to validate the origination AS of BGP routes. More specifically, one needs to validate that the AS number claiming to originate an address prefix (as derived from the AS_PATH attribute of the BGP ro...

#### `extract_evidence_origin_change_03`

- chunk：`rfc6811_s001_1_002`
- 文档：`rfc6811`
- source_ref：`raw/standards/rfc6811.txt#1`
- section_path：Introduction
- match_score：4
- matched_terms：announcement, prefix, rfc6811, roa

> ...sions to X.509 to represent IP addresses and AS identifiers [RFC3779], thus the name RPKI. Route Origin Authorizations (ROAs) [RFC6482] are separate digitally signed objects that define associations between ASes and IP address blocks. Finally, the repository system is operated in a distributed fashion through the IANA, Regional Internet Registry (RIR) hierarchy, and ISPs. In order to benefit from the RPKI system, it is envisioned that relying parties at either the AS or organization level obtain a local copy of the signed object collection, verify the signatures, and process them. The cache must also be refreshed periodically. The exact acces...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. anomaly_path_hijack

- 实体 ID：`evidence_path_hijack`
- 实体类型：EvidenceTemplate
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

#### `extract_evidence_path_hijack_01`

- chunk：`bgpshield_2025_s007_page_7_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-7`
- section_path：Page 7
- match_score：8
- matched_terms：as_path, bgpshield_2025, change, path, relationship, report, rpki, sequence

> The final stage aggregates scattered anomalous route changes into distinct, temporally bounded anomaly events, which are then compiled into human-readable reports detailing their associated prefixes and responsible ASes. 4.3.1. Path Difference Scoring.Given a route change (see Sec.3), BAD first evaluates its path difference score between historical and updated route. To accurately quantify such difference score, we introduced theAnomalyResponsiveDynamicTimeWarping algorithm (AR-DTW), which aligns AS paths of arbitrary lengths and computes the minimal cumulative sum of pairwise distances between aligned AS embeddings as the path difference sco...

#### `extract_evidence_path_hijack_02`

- chunk：`bgpshield_2025_s005_page_5_001`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-5`
- section_path：Page 5
- match_score：7
- matched_terms：as_path, bgpshield_2025, change, inference, path, relationship, report

> ...EMANTICENCODER B. BGP ANOMALY DETECTOR Ⅰ. AS Description AS Information (JSON)Batched Prompts (NLP) ASRankRoleProfileAS Relationship ... Ⅱ. LLMInference Ⅲ. EmbeddingDimensionality ReductionResampling ReductionNeuralNetworkPositive-NegativeSampling Percentile Thresholding Calculate PairwiseDistanceSimilarOrganization Neg:DivergentRole Org-Based Grouping Pos:SimilarRole ASOrganization ASRoleRepresentation Ⅰ. Path Difference ScoringCurrent RouteOrigin RouteT Route PathPrefixRoute PathPrefix𝐳"1, 𝐳"4... ,𝐳"8*.*.*.*/20𝐳"1, 𝐳"4... , 𝐳"2*.*.*.*/18**.** 𝐳"3, 𝐳"9... , 𝐳"7*.*.*.*/18𝐳"3, 𝐳"5... , 𝐳"7*.*.*.*/18**.** ............... Path Diff ScoreCurrent...

#### `extract_evidence_path_hijack_03`

- chunk：`bgpshield_2025_s010_page_10_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-10`
- section_path：Page 10
- match_score：7
- matched_terms：bgpshield_2025, change, path, relationship, report, rpki, status

> ...BGP datasets. Note that each detection system may generates multiple alerts for a single anomaly event, with each alert reporting a potential anomaly. Thus, we consider an alert valid if it matches confirmed information, particularly when the system identifies the target prefix as anomalous and accurately pinpoints the misbehaving AS as the responsible party, indicating successful detection of the confirmed anomaly for that event. Beyond confirmed anomalies, other alerts may indicate previously unrevealed routing anomalies or represent false positives. To validate these unconfirmed alerts, we extend the minor anomaly identification approach f...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. anomaly_path_manipulation

- 实体 ID：`evidence_path_manipulation`
- 实体类型：EvidenceTemplate
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

#### `extract_evidence_path_manipulation_01`

- chunk：`bgpshield_2025_s004_page_4_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-4`
- section_path：Page 4
- match_score：4
- matched_terms：as_path, behavior, bgpshield_2025, policy

> ...36561, the difference signifies a route change. Notably, although the differences accurately reflect changes in routing behavior, they do not indicate anomalies, as some route changes result from legitimate operational practices (e.g.,traffic engineering or policy adjustments). The objective of BGPShield is to identify truly anomalous route changes by capturing subtle deviations in behavioral semantics along routing paths. To comprehensively evaluate BGPShield and verify its effectiveness in real-world scenarios, we construct 16 realworld datasets corresponding to publicly reported BGP incidents spanning from 2008 to 2025. Each dataset includ...

#### `extract_evidence_path_manipulation_02`

- chunk：`bgpshield_2025_s007_page_7_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-7`
- section_path：Page 7
- match_score：4
- matched_terms：artifacts, as_path, behavior, bgpshield_2025

> ...and emphasizes potentially suspicious AS within an AS set 4, thereby improving its responsiveness to anomalous routing behaviors while suppressing its sensitivity to routine routing variations. Formally, let s= [s 1, s2, . . . , sn],t= [t 1, t2, . . . , tm],(5) denote two AS paths, wheres i andt j are AS identifiers. ARDTW first removes consecutive duplicate ASes to eliminate artifacts from route flapping. The cleaned sequences are denoted bys c andt c, with respective lengthsn ′ andm ′. With our LLM-based semantic encoder, each AS nodev i can be represented as a reduced semantic embedding˜z(vi)∈ Rd′ The extent of dissimilarity between nodes...

#### `extract_evidence_path_manipulation_03`

- chunk：`bgpshield_2025_s008_page_8_001`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-8`
- section_path：Page 8
- match_score：4
- matched_terms：as_path, behavior, bgpshield_2025, policy

> ...a threshold. However, as BGP routes exhibits substantial temporal fluctuations (e.g.,transient link failures or routine policy adjustments), using a single static threshold across periods may thus overlook subtle anomalies during stable intervals or trigger excessive false alarms during volatile periods. To address this, we adopt an adaptive thresholding strategy with a sliding window of lengthw (1 hour).

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. anomaly_prefix_hijack

- 实体 ID：`evidence_prefix_hijack`
- 实体类型：EvidenceTemplate
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

#### `extract_evidence_prefix_hijack_01`

- chunk：`bear_2025_s001_page_1_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-1`
- section_path：Page 1
- match_score：1
- matched_terms：bear_2025

> arXiv:2506.04514v1 [cs.NI] 4 Jun 2025 BEAR: BGP Event Analysis and Reporting 1st Hanqing Li Engineering Sciences and Applied Mathematics Department Northwestern University Evanston, USA hanqingli2025@u.northwestern.edu 2nd Melania Fedeli Amazon Web Services (AWS) Dublin, Ireland melaniaf@amazon.com 3rd Vinay Kolar Amazon Web Services (AWS) Cupertino, USA vinkolar@amazon.com 4th Diego Klabjan Industrial Engineering and Management Sciences Department Northwestern University Evanston, USA d-klabjan@northwestern.edu Abstract—The Internet comprises of interconnected, independently managed Autonomous Systems (AS) that rely on the Border Gateway Pro...

#### `extract_evidence_prefix_hijack_02`

- chunk：`bear_2025_s001_page_1_003`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-1`
- section_path：Page 1
- match_score：1
- matched_terms：bear_2025

> While existing methods can detect the occurrence of BGP anomalies [5]–[15], a comprehensive understanding of these events is essential for effective mitigation and prevention. Detailed insights into the event type, affected ASes, pre- and post-event path changes, and identification of the malicious or misconfigured AS are crucial for network operators and security professionals. Such in-depth analysis enables targeted responses, minimizes disruption, and enhances the overall security posture of the Internet’s routing infrastructure. Consequently, it is imperative to develop methods that can automatically generate comprehensive reports upon th...

#### `extract_evidence_prefix_hijack_03`

- chunk：`bear_2025_s002_page_2_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-2`
- section_path：Page 2
- match_score：1
- matched_terms：bear_2025

> from large-scale data, due to their training on textual rather than structured numerical data [17]. Thus, while we use structured models to detect anomalies, our novelty lies in employing LLMs to interpret and explain these anomalies in detail. In this paper, we propose a novel framework, BEAR (BGP Event Analysis and Reporting), designed to leverage an LLM for generating comprehensive reports that explain detected BGP anomaly events. The framework begins by extracting relevant BGP data associated with an anomaly from an online BGP database using the provided timestamp and IP prefix. Recognizing the strengths of LLMs in handling textual data o...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
