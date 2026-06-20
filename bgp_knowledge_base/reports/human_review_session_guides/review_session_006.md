# review_session_006 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- blocked_by_llm：1
- ready_to_apply：9

## 1. ASN

- 实体 ID：`concept_asn`
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

#### `extract_concept_asn_01`

- chunk：`rfc4271_s064_9_1_2_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1.2.2`
- section_path：Breaking Ties (Phase 2)
- match_score：8
- matched_terms：as_path, autonomous, may, not, number, origin, rfc4271, system

> In its Adj-RIBs-In, a BGP speaker may have several routes to the same destination that have the same degree of preference. The local speaker can select only one of these routes for inclusion in the associated Loc-RIB. The local speaker considers all routes with the same degrees of preference, both those received from internal peers, and those received from external peers. The following tie-breaking procedure assumes that, for each candidate route, all the BGP speakers within an autonomous system can ascertain the cost of a path (interior distance) to the address depicted by the NEXT_HOP attribute of the route, and follow the same route select...

#### `extract_concept_asn_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：7
- matched_terms：as_path, asn, context_2026, may, not, origin, prefix

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_concept_asn_03`

- chunk：`rfc4271_s029_5_1_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#5.1.2`
- section_path：AS_PATH
- match_score：7
- matched_terms：as_path, autonomous, not, number, origin, rfc4271, system

> AS_PATH is a well-known mandatory attribute. This attribute identifies the autonomous systems through which routing information carried in this UPDATE message has passed. The components of this list can be AS_SETs or AS_SEQUENCEs. When a BGP speaker propagates a route it learned from another BGP speaker's UPDATE message, it modifies the route's AS_PATH attribute based on the location of the BGP speaker to which the route will be sent: a) When a given BGP speaker advertises the route to an internal peer, the advertising speaker SHALL NOT modify the AS_PATH attribute associated with the route. b) When a given BGP speaker advertises the route to...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. BEAR: BGP Event Analysis and Reporting

- 实体 ID：`paper_method_bear`
- 实体类型：PaperMethod
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bear_2025.md`

### parsed 路径

- `parsed/papers/bear_2025.json`

### Top 摘录

#### `extract_paper_method_bear_01`

- chunk：`bear_2025_s002_page_2_003`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-2`
- section_path：Page 2
- match_score：15
- matched_terms：analysis, anomaly, bear, bear_2025, event, explanation, path, paths, prefix, report

> ...ing prompt augmentation and self-consistency mechanisms, the approach achieves 100% accuracy and generates detailed BGP anomaly event reports, effectively identifying missing key elements such as event types, relevant ASes, and comprehensive explanations. • Robustness of Availability of Collectors : In real world, collectors can be down. We study such an impact by creating settings with limited availabilities of collectors. With respect to LLMs, this accommodates the use of LLMs with a limited number of input tokens. Leveraging fewer collectors also results in a faster explanation of the events and a quicker mitigation and remediation, thus r...

#### `extract_paper_method_bear_02`

- chunk：`bear_2025_s002_page_2_002`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-2`
- section_path：Page 2
- match_score：13
- matched_terms：analysis, anomaly, bear, bear_2025, event, explanation, path, prefix, report, reporting

> Moreover, we introduce the first approach to generate synthetic BGP anomaly event data, addressing the scarcity of fully documented BGP anomaly events. To create high-quality synthetic events, we leverage an LLM to produce specific details of an anomaly, such as the timestamp, victim IP prefix, event type, hijacker or route leaker, AS path after the event, and detection rate. Using the generated details, we extract relevant BGP data from an existing BGP dataset based on the timestamp and victim IP prefix. This data is then modified according to the LLM-specified details, creating synthetic BGP data that simulates the occurrence of an anomaly...

#### `extract_paper_method_bear_03`

- chunk：`bear_2025_s005_page_5_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-5`
- section_path：Page 5
- match_score：13
- matched_terms：analysis, anomaly, bear, bear_2025, event, path, paths, prefix, report, reporting

> Fig. 5. Number of AS path per IP prefix. Fig. 6. Overview of the framework that generates report for BGP anomaly events The method begins with a data analysis phase designed to transform tabular BGP data into textual descriptions, as illustrated in Figure 6. The LLM is first provided with the BGP data in a tabular format and prompted to describe changes in AS paths by comparing Daf ter with Dbef ore, using Dhistory as a reference. The prompt is carefully structured to decompose the reasoning process, directing the LLM to analyze AS path changes systematically. The LLM is required to answer the following key questions. • Does the existing path...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. Before-after AS path comparison

- 实体 ID：`mechanism_before_after_path_comparison`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bear_2025.md`

### parsed 路径

- `parsed/papers/bear_2025.json`

### Top 摘录

#### `extract_mechanism_before_after_path_comparison_01`

- chunk：`bear_2025_s004_page_4_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-4`
- section_path：Page 4
- match_score：10
- matched_terms：as_path, bear_2025, collector, event, historical, path, paths, prefixes, rib, update

> Fig. 3. Overview of how BGP messages and routing information are collected. Fig. 4. An example of a BGP update message. event E and identify key unknown features, such as the event type and relevant ASes. B. Data Retrieval After obtaining the target IP prefix ip and the specific start time t, we utilize the open-source software framework BGPStream [43] to retrieve relevant AS path information from the BGP dataset DBGP . Specifically, we extract AS paths from BGP update messages and routing information base (RIB) records to construct three datasets: historical AS paths, AS paths before the event, and AS paths after the event. BGPStream accesse...

#### `extract_mechanism_before_after_path_comparison_02`

- chunk：`bear_2025_s004_page_4_003`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-4`
- section_path：Page 4
- match_score：10
- matched_terms：as_path, bear_2025, can, collector, event, path, paths, prefixes, rib, update

> 3) Data After the Event ( Daf ter): Dbef ore is further updated using BGP update messages collected between five minutes before t and five minutes after t, or up to one second before the event ends if the end time is earlier than t + 5m. The update process follows the same procedure as in Dbef ore, ensuring Daf ter reflects the network state after the anomaly event starts. To account for sub-prefix anomaly scenarios, we also collect RIB records and BGP update messages for IP prefixes that are more or less specific than ip, updating Dhistory, Dbef ore, and Daf ter accordingly. All three datasets are stored as structured tabular data in the JSO...

#### `extract_mechanism_before_after_path_comparison_03`

- chunk：`bear_2025_s002_page_2_003`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-2`
- section_path：Page 2
- match_score：9
- matched_terms：as_path, bear_2025, can, collector, event, path, paths, prefixes, rib

> ...pt augmentation and self-consistency mechanisms, the approach achieves 100% accuracy and generates detailed BGP anomaly event reports, effectively identifying missing key elements such as event types, relevant ASes, and comprehensive explanations. • Robustness of Availability of Collectors : In real world, collectors can be down. We study such an impact by creating settings with limited availabilities of collectors. With respect to LLMs, this accommodates the use of LLMs with a limited number of input tokens. Leveraging fewer collectors also results in a faster explanation of the events and a quicker mitigation and remediation, thus reducing...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. BGP

- 实体 ID：`concept_bgp`
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

#### `extract_concept_bgp_01`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：13
- matched_terms：autonomous, border, exchange, gateway, information, interior, path, prefix, protocol, reachability

> ...for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. Standards Track [Page 5] RFC 4271 BGP-4 January 2006 d...

#### `extract_concept_bgp_02`

- chunk：`rfc4271_s005_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1`
- section_path：Introduction
- match_score：12
- matched_terms：autonomous, border, exchange, gateway, information, not, path, prefix, protocol, reachability

> The Border Gateway Protocol (BGP) is an inter-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity for this reachability, from which routing loops may be pruned and, at the AS level, some policy decisions may be enforced. BGP-4 provides a set of mechanisms for supporting Classless Inter- Domain Routing (CIDR) [RFC1518, RFC1519]. Th...

#### `extract_concept_bgp_03`

- chunk：`rfc4271_s009_3_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：11
- matched_terms：autonomous, border, does, exchange, gateway, information, not, protocol, reachability, rfc4271

> The Border Gateway Protocol (BGP) is an inter-Autonomous System routing protocol. It is built on experience gained with EGP (as defined in [RFC904]) and EGP usage in the NSFNET Backbone (as described in [RFC1092] and [RFC1093]). For more BGP-related information, see [RFC1772], [RFC1930], [RFC1997], and [RFC2858]. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity,...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. BGP Session

- 实体 ID：`concept_bgp_session`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `ripe_ris_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_docs.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_docs.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_concept_bgp_session_01`

- chunk：`rfc4271_s046_10_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#10`
- section_path：Each timer has a "timer" and a "time" (the initial value).
- match_score：8
- matched_terms：between, over, peer, relationship, rfc4271, session, view, which

> The optional Session attributes are listed below. These optional attributes may be supported, either per connection or per local system: 1) AcceptConnectionsUnconfiguredPeers 2) AllowAutomaticStart 3) AllowAutomaticStop 4) CollisionDetectEstablishedState 5) DampPeerOscillations 6) DelayOpen 7) DelayOpenTime 8) DelayOpenTimer 9) IdleHoldTime 10) IdleHoldTimer 11) PassiveTcpEstablishment 12) SendNOTIFICATIONwithoutOPEN 13) TrackTcpState Rekhter, et al. Standards Track [Page 37] RFC 4271 BGP-4 January 2006 The optional session attributes support different features of the BGP functionality that have implications for the BGP FSM state transitions....

#### `extract_concept_bgp_session_02`

- chunk：`rfc4271_s011_3_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.2`
- section_path：Routing Information Base
- match_score：6
- matched_terms：between, information, peer, relationship, rfc4271, speakers

> The Routing Information Base (RIB) within a BGP speaker consists of three distinct parts: a) Adj-RIBs-In: The Adj-RIBs-In stores routing information learned from inbound UPDATE messages that were received from other BGP speakers. Their contents represent routes that are available as input to the Decision Process. b) Loc-RIB: The Loc-RIB contains the local routing information the BGP speaker selected by applying its local policies to the routing information contained in its Adj-RIBs-In. These are the routes that will be used by the local BGP speaker. The next hop for each of these routes MUST be resolvable via the local BGP speaker's Routing T...

#### `extract_concept_bgp_session_03`

- chunk：`rfc4271_s047_8_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#8.1.1`
- section_path：Optional Events Linked to Optional Session Attributes
- match_score：6
- matched_terms：between, peer, relationship, rfc4271, session, which

> ...puts to the BGP FSM are events. Events can either be mandatory or optional. Some optional events are linked to optional session attributes. Optional session attributes enable several groups of FSM functionality. The linkage between FSM functionality, events, and the optional session attributes are described below. Group 1: Automatic Administrative Events (Start/Stop) Optional Session Attributes: AllowAutomaticStart, AllowAutomaticStop, DampPeerOscillations, IdleHoldTime, IdleHoldTimer Option 1: AllowAutomaticStart Description: A BGP peer connection can be started and stopped by administrative control. This administrative control can either be...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. BGP Speaker

- 实体 ID：`concept_bgp_speaker`
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

#### `extract_concept_bgp_speaker_01`

- chunk：`rfc4271_s006_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：8
- matched_terms：information, peer, peers, process, rfc4271, router, speaker, update

> ...ave a specific meaning to the BGP protocol and that are used throughout the text. Adj-RIB-In The Adj-RIBs-In contains unprocessed routing information that has been advertised to the local BGP speaker by its peers. Adj-RIB-Out The Adj-RIBs-Out contains the routes for advertisement to specific peers by means of the local speaker's UPDATE messages. Autonomous System (AS) The classic definition of an Autonomous System is a set of routers under a single technical administration, using an interior gateway protocol (IGP) and common metrics to determine how to route packets within the AS, and using an inter-AS routing protocol to determine how to rou...

#### `extract_concept_bgp_speaker_02`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：8
- matched_terms：information, peer, peers, process, rfc4271, router, speaker, update

> ...oute An advertised route that is available for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. Standards Tr...

#### `extract_concept_bgp_speaker_03`

- chunk：`rfc4271_s009_3_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：8
- matched_terms：can, forwarding, information, peer, peers, rfc4271, router, speaker

> ...fined in [RFC904]) and EGP usage in the NSFNET Backbone (as described in [RFC1092] and [RFC1093]). For more BGP-related information, see [RFC1772], [RFC1930], [RFC1997], and [RFC2858]. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity, from which routing loops may be pruned, and, at the AS level, some policy decisions may be enforced. In the context of this docume...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. BGP Update

- 实体 ID：`concept_bgp_update`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `bgpstream_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_concept_bgp_update_01`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：8
- matched_terms：are, attributes, message, peer, previously, reachability, rfc4271, update

> ...oute An advertised route that is available for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. Standards Tr...

#### `extract_concept_bgp_update_02`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：8
- matched_terms：are, attributes, message, peer, previously, reachability, rfc4271, update

> For the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the...

#### `extract_concept_bgp_update_03`

- chunk：`rfc4271_s076_10_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#10`
- section_path：BGP Timers
- match_score：7
- matched_terms：are, collector, message, must, new, rfc4271, update

> ...n of the frequency of route advertisements. Optional Parameter Type 1 (Authentication Information) has been deprecated. UPDATE Message Error subcode 7 (AS Routing Loop) has been deprecated. OPEN Message Error subcode 5 (Authentication Failure) has been deprecated. Use of the Marker field for authentication has been deprecated. Implementations MUST support TCP MD5 [RFC2385] for authentication. Clarification of BGP FSM. Rekhter, et al. Standards Track [Page 92] RFC 4271 BGP-4 January 2006 Appendix B. Comparison with RFC 1267 All the changes listed in Appendix A, plus the following. BGP-4 is capable of operating in an environment where a set of...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. BGPShield

- 实体 ID：`paper_method_bgpshield`
- 实体类型：PaperMethod
- 队列状态：`blocked_by_llm`
- 当前实体状态：`pending`
- 当前人工决策：`needs_semantic_review`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：该项需要语义流程或 LLM，按当前规则跳过并保留记录。

### 来源引用

- `bgpshield_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bgpshield_2025.md`

### parsed 路径

- `parsed/papers/bgpshield_2025.json`

### Top 摘录

#### `extract_paper_method_bgpshield_01`

- chunk：`bgpshield_2025_s004_page_4_003`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-4`
- section_path：Page 4
- match_score：14
- matched_terms：anomaly, asrank, behavior, bgpshield, bgpshield_2025, caida, data, descriptions, event, organization

> For each documented incident, we collect all UPDATE data observed within a 24hour window centered around the target event, extracting the corresponding BGP update streams from RouteViews. This time window encompasses the 12-hour period preceding and following the incident occurrence timestamp, ensures the inclusion of both anomalous routing behaviors and sufficient legitimate routing dynamics. The total number of collected route changes is 1,327,756,266. 4. BGPShield System 4.1. System Overview As illustrated in Fig.2, BGPShield consists of two core modules: the LLM-based Semantic Encoder (LSE) and the BGP Anomaly Detector (BAD). LSE aggregat...

#### `extract_paper_method_bgpshield_02`

- chunk：`bgpshield_2025_s013_page_13_003`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-13`
- section_path：Page 13
- match_score：11
- matched_terms：anomaly, behavior, bgpshield, bgpshield_2025, data, descriptions, detection, features, path, semantic

> ...dimensions below this threshold might suffer from insufficient representational capacity to adequately capture network features, while embeddings exceeding this dimension may become over-parameterized, prone to learning dataset noise rather than generalizable patterns, leading to overfitting and degraded generalization performance. The underlying causes of this “optimal dimension” are likely multifaceted, influenced by graph structural complexity, task difficulty, as well as data scale and quality. 8. Conclusion In this paper, we propose BGPShield, a novel anomaly detection framework which is built on LLM embeddings that capture both theBeha...

#### `extract_paper_method_bgpshield_03`

- chunk：`bgpshield_2025_s003_page_3_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-3`
- section_path：Page 3
- match_score：10
- matched_terms：anomaly, behavior, bgpshield, bgpshield_2025, detection, event, path, requires, semantic, semantics

> The experimental results show thatBGPShield detects 100% of publicly reported BGP anomaly events, while the SOTA method BEAM only identifies 81% of them.Simultaneously, BGPShield achieves an average FDR that is 2-3×lower than BEAM, demonstrating an improvement in detection precision.Even with 25% noise in AS-level information, BGPShield still sustains 98.8% precision, indicating robust generalizability to evolving BGP networks. Moreover, BGPShield can generate embeddings for newly observed ASes within one second per AS, whereas BEAM requires thorough retraining on the entire AS graph, which takes an average of 65 hours. This capability enable...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. BGPStream

- 实体 ID：`concept_bgpstream`
- 实体类型：BGPConcept
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

#### `extract_concept_bgpstream_01`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：7
- matched_terms：bgpstream, context_2026, data, rib, ripe, ris, routeviews

> Each BGP data source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_concept_bgpstream_02`

- chunk：`bgpstream_docs_s001_full_001`
- 文档：`bgpstream_docs`
- source_ref：`raw/tools_docs/bgpstream_docs.html#full`
- section_path：BGPStream
- match_score：6
- matched_terms：bgpstream, bgpstream_docs, data, framework, processing, sources

> BGPStream Toggle navigation Home News Components Download Documentation Publications Data Providers Acknowledgements Contact Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutorials BGPReader libBGPStream PyBGPStream Docker Data Encoding Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutoria...

#### `extract_concept_bgpstream_03`

- chunk：`context_2026_paper_bear_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 论文方法知识`
- section_path：BGP 论文方法知识
- match_score：4
- matched_terms：bgpstream, context_2026, data, sources

> ...ted as a method source for BGP anomaly event explanation. The knowledge base should extract its research problem, input data, core concepts, method process, outputs, applicable anomaly types, dependent data sources, strengths, limitations, and reusable evidence templates.

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. BGPStream

- 实体 ID：`datasource_bgpstream`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `bgpstream_docs`
- `bear_2025`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`
- `cleaned/papers/bear_2025.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`
- `parsed/papers/bear_2025.json`

### Top 摘录

#### `extract_datasource_bgpstream_01`

- chunk：`bear_2025_s004_page_4_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-4`
- section_path：Page 4
- match_score：12
- matched_terms：bear_2025, bgpstream, data, framework, historical, multiple, not, open-source, records, rib

> Fig. 3. Overview of how BGP messages and routing information are collected. Fig. 4. An example of a BGP update message. event E and identify key unknown features, such as the event type and relevant ASes. B. Data Retrieval After obtaining the target IP prefix ip and the specific start time t, we utilize the open-source software framework BGPStream [43] to retrieve relevant AS path information from the BGP dataset DBGP . Specifically, we extract AS paths from BGP update messages and routing information base (RIB) records to construct three datasets: historical AS paths, AS paths before the event, and AS paths after the event. BGPStream accesse...

#### `extract_datasource_bgpstream_02`

- chunk：`bear_2025_s010_page_10_004`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-10`
- section_path：Page 10
- match_score：9
- matched_terms：bear_2025, bgpstream, data, framework, historical, live, not, open-source, processing

> Bush, “ispy: Detecting ip prefix hijacking on my own,” Proceedings of the ACM SIGCOMM 2008 Conference on Data Communication , pp. 327–338, 2008. [40] R. Mondal, A. Tang, R. Beckett, T. Millstein, and G. Varghese, “What do LLMs need to synthesize correct router configurations?” Proceedings of the 22nd ACM Workshop on Hot Topics in Networks , pp. 189–195, 2023. [41] K. B. Kan, H. Mun, G. Cao, and Y . Lee, “Mobile-llama: Instruction fine-tuning open-source llm for network analysis in 5g networks,” IEEE Network, 2024. [42] M. Palmero, K. P. Annamalai, H. Singaravelan, D. Zacks, and J. W. Capobianco, “Providing an ai-enabled network assistant for...

#### `extract_datasource_bgpstream_03`

- chunk：`bear_2025_s003_page_3_001`
- 文档：`bear_2025`
- source_ref：`raw/papers/bear_2025.pdf#page-3`
- section_path：Page 3
- match_score：8
- matched_terms：bear_2025, data, framework, not, open-source, rib, time, update

> path [18]. The AS path is a sequential list of AS numbers that a route advertisement has traversed; each time a router forwards the announcement, it prepends its own AS number to the path, thereby creating a path to reach an IP prefix that will be filtered by policy-based routing rules by following the AS to decide whether to take this path and advertise it or not [4]. BGP was originally designed to prioritize functionality and scalability rather than security, so it lacks built-in mechanisms to authenticate the source of route announcements [19]. Because of this trust-based design, any AS can announce routes for IP prefixes regardless of own...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
