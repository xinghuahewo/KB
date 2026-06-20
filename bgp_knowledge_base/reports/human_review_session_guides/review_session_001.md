# review_session_001 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. aggregator

- 实体 ID：`field_aggregator`
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

#### `extract_field_aggregator_01`

- chunk：`rfc4271_s026_4_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4`
- section_path：Optional non-transitive.
- match_score：12
- matched_terms：aggregator, as_path, atomic_aggregate, attribute, attributes, context, origin, path, present, rfc4271

> New, transitive optional attributes MAY be attached to the path by the originator or by any other BGP speaker in the path. If they are not attached by the originator, the Partial bit in the Attribute Flags octet is set to 1. The rules for attaching new non-transitive optional attributes will depend on the nature of the specific attribute. The documentation of each new non-transitive optional attribute will be expected to include such rules (the description of the MULTI_EXIT_DISC attribute gives an example). All optional attributes (both transitive and non-transitive), MAY be updated (if appropriate) by BGP speakers in the path. The sender of...

#### `extract_field_aggregator_02`

- chunk：`rfc4271_s076_10_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#10`
- section_path：BGP Timers
- match_score：12
- matched_terms：aggregation, aggregator, as_path, atomic_aggregate, attribute, path, prefix, rfc4271, routes, speaker

> The relationship between the immediate next hop, and the next hop as specified in the NEXT_HOP path attribute. Clarification of the tie-breaking procedures. Clarification of the frequency of route advertisements. Optional Parameter Type 1 (Authentication Information) has been deprecated. UPDATE Message Error subcode 7 (AS Routing Loop) has been deprecated. OPEN Message Error subcode 5 (Authentication Failure) has been deprecated. Use of the Marker field for authentication has been deprecated. Implementations MUST support TCP MD5 [RFC2385] for authentication. Clarification of BGP FSM. Rekhter, et al. Standards Track [Page 92] RFC 4271 BGP-4 Ja...

#### `extract_field_aggregator_03`

- chunk：`rfc4271_s021_2_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#2`
- section_path：AS_SEQUENCE: ordered set of ASes a route in
- match_score：10
- matched_terms：aggregator, attribute, attributes, path, prefix, rfc4271, routes, speaker, update, use

> AGGREGATOR is an optional transitive attribute of length 6. The attribute contains the last AS number that formed the aggregate route (encoded as 2 octets), followed by the IP address of the BGP speaker that formed the aggregate route (encoded as 4 octets). This SHOULD be the same address as the one used for the BGP Identifier of the speaker. Usage of this attribute is defined in 5.1.7. Rekhter, et al. Standards Track [Page 19] RFC 4271 BGP-4 January 2006 Network Layer Reachability Information: This variable length field contains a list of IP address prefixes. The length, in octets, of the Network Layer Reachability Information is not encoded...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. ASPA

- 实体 ID：`datasource_aspa`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `arin_aspa_doc`
- `ripe_aspa_doc`
- `rfc6480`

### cleaned 路径

- `cleaned/data_docs/arin_aspa_doc.md`
- `cleaned/data_docs/ripe_aspa_doc.md`
- `cleaned/standards/rfc6480.md`

### parsed 路径

- `parsed/data_docs/arin_aspa_doc.json`
- `parsed/data_docs/ripe_aspa_doc.json`
- `parsed/standards/rfc6480.json`

### Top 摘录

#### `extract_datasource_aspa_01`

- chunk：`arin_aspa_doc_s001_full_002`
- 文档：`arin_aspa_doc`
- source_ref：`raw/data_docs/arin_aspa_doc.html#full`
- section_path：Autonomous System Provider Authorizations (ASPAs) - American Registry for Internet Numbers
- match_score：13
- matched_terms：allow, arin_aspa_doc, aspa, authorization, authorize, autonomous, customer, holder, must, object

> ...mmunity Blog Pay Now Feedback Home IP Addresses & ASNs Resource Management Services Resource Public Key Infrastructure (RPKI) Autonomous System Provider Authorizations (ASPAs) Resource Public Key Infrastructure (RPKI) Autonomous System Provider Authorizations (ASPAs) On this page Skip to main text Scroll for more Autonomous System Provider Authorization (ASPA) Overview Creating an ASPA in ARIN Online Viewing Your ASPAs Using the API Using ARIN Online Verifying Your ASPAs Are Active Modifying an ASPA Using the API Using ARIN Online Removing an ASPA Using the API Using ARIN Online Jump to related content Autonomous System Provider Authorization...

#### `extract_datasource_aspa_02`

- chunk：`arin_aspa_doc_s001_full_001`
- 文档：`arin_aspa_doc`
- source_ref：`raw/data_docs/arin_aspa_doc.html#full`
- section_path：Autonomous System Provider Authorizations (ASPAs) - American Registry for Internet Numbers
- match_score：9
- matched_terms：arin_aspa_doc, aspa, authorization, autonomous, provider, records, rpki, set, system

> Autonomous System Provider Authorizations (ASPAs) - American Registry for Internet Numbers Skip to main content Your IP address is Log in Log in User Dashboard Settings Profile and security information Log Out Search all requests subject to terms of use Search IP Addresses & ASNs Get Started ARIN Account Management Requesting IP Addresses or ASNs IPv6 Information IPv4 Addressing Options Autonomous System Numbers Legacy Resources at ARIN Fee & Billing Information Fee Schedule Premier Support Plan (PSP) Make a Payment How Billing Works Resource Revocation, Returns, and Reinstatement IP & ASN Registry Services Managing Resource Records Transferr...

#### `extract_datasource_aspa_03`

- chunk：`arin_aspa_doc_s001_full_004`
- 文档：`arin_aspa_doc`
- source_ref：`raw/data_docs/arin_aspa_doc.html#full`
- section_path：Autonomous System Provider Authorizations (ASPAs) - American Registry for Internet Numbers
- match_score：9
- matched_terms：arin_aspa_doc, aspa, authorization, autonomous, object, provider, rpki, set, system

> ...n to ARIN Online and select Routing Security from the navigation menu. In the ‘Your Organization’ window, select Manage RPKI to view those created for the organization. Select the ASPA object you wish to modify. In the ‘Autonomous System Provider Authorizations (ASPAs)’ window, select Modify. Make changes to the ‘Set of Provier ASes,’ then select submit. Changes will take effect in the RPKI database immediately and will be reflected in the public RPKI repository within 24 hours. Removing an ASPA You can delete your ASPAs using one of the following methods: Using the API Visit ARIN’s RPKI RESTful API User Guide to delete an ASPA (note that you...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. ASPA Path Verification

- 实体 ID：`mechanism_aspa_path_verification`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `arin_aspa_doc`
- `ripe_aspa_doc`

### cleaned 路径

- `cleaned/data_docs/arin_aspa_doc.md`
- `cleaned/data_docs/ripe_aspa_doc.md`

### parsed 路径

- `parsed/data_docs/arin_aspa_doc.json`
- `parsed/data_docs/ripe_aspa_doc.json`

### Top 摘录

#### `extract_mechanism_aspa_path_verification_01`

- chunk：`ripe_aspa_doc_s001_full_007`
- 文档：`ripe_aspa_doc`
- source_ref：`raw/data_docs/ripe_aspa_doc.html#full`
- section_path：Autonomous System Provider Authorization (ASPA) — RIPE Network Coordination Centre
- match_score：14
- matched_terms：are, aspa, authorization, evaluate, objects, path, paths, plausible, provider, providers

> As with ROAs, if you choose to sign an ASPA object for your AS, make sure that you include all your upstream providers and keep this object up to date in lockstep with changes in your blend of upstream providers. The RIPE NCC RPKI Dashboard gives no hints or guidance about which providers are seen for your AS in BGP, so you will need to ensure this yourself. If you forget or neglect to include a provider, this can lead to the rejection of routes you send via the unlisted provider. Just like signing ROAs, signing ASPA objects is therefore not without risk if you are not prepared to proactively maintain these objects as part of your network ope...

#### `extract_mechanism_aspa_path_verification_02`

- chunk：`ripe_aspa_doc_s001_full_008`
- 文档：`ripe_aspa_doc`
- source_ref：`raw/data_docs/ripe_aspa_doc.html#full`
- section_path：Autonomous System Provider Authorization (ASPA) — RIPE Network Coordination Centre
- match_score：11
- matched_terms：are, aspa, authorization, path, paths, plausible, provider, providers, ripe_aspa_doc, rpki

> No Attestation There is no ASPA object signed by the prospective customer AS. Therefore, any other AS may appear as its provider. The full path received from a customer can have the following status outcomes: Valid Each AS-to-AS Authorization Function yields “provider”. Invalid At least one AS-to-AS Authorization Function yields “not provider”. Unknown At least one AS-to-AS Authorization Function yields “no attestation”, but there is no occurrence of “not provider”. Paths that are verifiably invalid should be rejected. Both valid and unknown paths should be accepted. The latter is important, not only because of partial adoption of ASPA signin...

#### `extract_mechanism_aspa_path_verification_03`

- chunk：`ripe_aspa_doc_s001_full_009`
- 文档：`ripe_aspa_doc`
- source_ref：`raw/data_docs/ripe_aspa_doc.html#full`
- section_path：Autonomous System Provider Authorization (ASPA) — RIPE Network Coordination Centre
- match_score：11
- matched_terms：are, as_path, aspa, aspa-based, authorization, path, paths, provider, ripe_aspa_doc, rpki

> ...route that goes “up”, then “down”, and then “up” again, and presumably “down” again, has a “valley” in the middle. Such paths are considered harmful as they usually are route leaks that make routing less optimal (e.g. longer latency, congested links, potentially more expensive). In essence, the ASPA verification process yields invalid for any paths that it can prove to have such a valley. To determine this, the process relies on finding the longest possible customer-to-provider paths from both directions in the path. These longest possible paths terminate at the first “not provider” AS to AS relationship that is found. The path as a whole is...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. asrank_rank

- 实体 ID：`field_asrank_rank`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `caida_asrank_api`

### cleaned 路径

- `cleaned/data_docs/caida_asrank_api.md`

### parsed 路径

- `parsed/data_docs/caida_asrank_api.json`

### Top 摘录

#### `extract_field_asrank_rank_01`

- chunk：`caida_asrank_api_s001_full_001`
- 文档：`caida_asrank_api`
- source_ref：`raw/data_docs/caida_asrank_api.html#full`
- section_path：AS Rank API
- match_score：12
- matched_terms：asrank, caida, caida_asrank_api, does, high, low, not, only, prove, rank

> AS Rank API About Background - AS Ranking - Cust. Cone - Citation Ranking AS Ranking Org Ranking Search Contact Data (external links) AS Relationship AS Organization AS Rank API v2 How tos FAQ Feedback AS Rank API ( [ doc ] ) CAIDA's AS Rank project has been analyzing macroscopic Internet topology for over 20 years, working to improve the integrity and utility of the relationship-based Autonomous Systems (AS) ranking by using vantage points, active probing, cross-validation in conjunction with other sources of data, and powerful data processing techniques to support large topology samples. The AS Rank API allows users to query for CAIDA's ran...

#### `extract_field_asrank_rank_02`

- chunk：`caida_asrank_api_s001_full_002`
- 文档：`caida_asrank_api`
- source_ref：`raw/data_docs/caida_asrank_api.html#full`
- section_path：AS Rank API
- match_score：6
- matched_terms：asrank, caida, caida_asrank_api, low, rank, use

> The AS Rank API provides a RESTful API for CAIDA's AS Rank service. The current version 2 of the API is based on the Symfony 4 PHP web application framework and the PostgreSQL database back-end. The API Examples below may show lower default per-page counts than the default of 500 (or 5000 maximum). We update the AS Rank data monthly. We describe different ways to retrieve various subset(s) of AS Rank data below. For a detailed technical description of the API endpoints, parameters and responses, please refer to the auto-generated Swagger ( OpenAPI ) Documentation . Please send your questions and comments to asrank-feedback@caida.org. Retrievi...

#### `extract_field_asrank_rank_03`

- chunk：`caida_asrank_api_s001_full_005`
- 文档：`caida_asrank_api`
- source_ref：`raw/data_docs/caida_asrank_api.html#full`
- section_path：AS Rank API
- match_score：6
- matched_terms：asrank, caida, caida_asrank_api, low, rank, use

> Finding Autonomous Systems (AS) By ID or Name The API allows users to specify which Autonomous Systems they seek. For example, the following GET request will return information about AS 3356 generated for the latest month: GET Info about a specific ASN / asns /3356 { "data" : { " cone " : { " asns " : 32759 , "prefixes" : 238712 , "addresses" : 795625728 }, "latitude" : "36.6367665181695" , "longitude" : "-92.3312241433131" , "degree" : { " globals " : "5381" , "peers" : 293 , "siblings" : 8 , "customers" : 5088 , "transits" : 5396 }, "name" : "LEVEL3" , "source" : "ARIN" , "clique" : "true" , " country_name " : "United States" , "rank" : "1"...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. asrank_relationship

- 实体 ID：`field_asrank_relationship`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `caida_asrank_api`
- `caida_as_relationships`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`
- `cleaned/data_docs/caida_asrank_api.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`
- `parsed/data_docs/caida_asrank_api.json`

### Top 摘录

#### `extract_field_asrank_relationship_01`

- chunk：`caida_as_relationships_s001_full_011`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：caida, caida_as_relationships, can, every, location, prefix, relationship, relationships, single

> AS relationships are more complex than allowed for in our approach. The semantics of routing relationships between the same two ASes can differ by peering location or even by prefix; our model oversimplifies these cases by assigning a single relationship to each pair of ASes. A truly accurate picture of the Internet topology would require collection of data from every AS, while our automated ranking procedure is limited to the measurement points publicly available at Route Views. As in all analyses of massive datasets, our heuristics have a number of associated external parameters. We fine tune the values of these parameters based on our pre-...

#### `extract_field_asrank_relationship_02`

- chunk：`caida_as_relationships_s001_full_007`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：8
- matched_terms：caida, caida_as_relationships, can, inference, prefix, relationship, relationships, should

> Dimitropoulos, et al. 6 identified still other issues with the ToR formulation, like the random breaking of ties which can yield obviously incorrect inferences, e.g., well-known large providers are inferred as customers of small ASes. In the first paper 6 we handled this issue with multiobjective optimization techniques that incorporated AS degree into the inference. In a subsequent paper 7 we introduced improved algorithms that determine not only c2p but also p2p links (for those we can detect from BGP data). These improvements achieved more accurate AS relationship inferences, which we demonstrate against ground truth for a set of ASes. Ben...

#### `extract_field_asrank_relationship_03`

- chunk：`caida_as_relationships_s001_full_005`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：7
- matched_terms：caida, caida_as_relationships, can, every, inference, relationship, relationships

> ...between ASes to define valid and invalid AS paths. A valid path between source and destination ASes is one in which for every ISP providing transit (a transit provider), there exists a customer immediately adjacent to the ISP in the AS path. An invalid path has at least one transit provider not paid by a neighbor in the path. In figure 2 the top two examples are valid paths, while the bottom two are invalid. In Example 1 the transit providers are A, B, and C. ISPs B and C pay to A, D pays to B, and F pays to C. In Example 2 the transit providers are B and C, and they are paid by D and F, respectively. In contrast, in Example 3 the transit pro...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. atomic_aggregate

- 实体 ID：`field_atomic_aggregate`
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

#### `extract_field_atomic_aggregate_01`

- chunk：`rfc4271_s073_9_2_2_2_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.2.2.2`
- section_path：Aggregating Routing Information
- match_score：9
- matched_terms：aggregate, aggregated, aggregation, all, atomic_aggregate, attributes, path, present, rfc4271

> - determine the longest leading sequence of tuples (as defined above) common to all the AS_PATH attributes of the routes to be aggregated. Make this sequence the leading sequence of the aggregated AS_PATH attribute. - set the type of the rest of the tuples from the AS_PATH attributes of the routes to be aggregated to AS_SET, and append them to the aggregated AS_PATH attribute. - if the aggregated AS_PATH has more than one tuple with the same value (regardless of tuple's type), eliminate all but one such tuple by deleting tuples of the type AS_SET from the aggregated AS_PATH attribute. - for each pair of adjacent tuples in the aggregated AS_PA...

#### `extract_field_atomic_aggregate_02`

- chunk：`rfc4271_s026_4_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4`
- section_path：Optional non-transitive.
- match_score：8
- matched_terms：aggregate, all, atomic_aggregate, attributes, path, present, rfc4271, update

> New, transitive optional attributes MAY be attached to the path by the originator or by any other BGP speaker in the path. If they are not attached by the originator, the Partial bit in the Attribute Flags octet is set to 1. The rules for attaching new non-transitive optional attributes will depend on the nature of the specific attribute. The documentation of each new non-transitive optional attribute will be expected to include such rules (the description of the MULTI_EXIT_DISC attribute gives an example). All optional attributes (both transitive and non-transitive), MAY be updated (if appropriate) by BGP speakers in the path. The sender of...

#### `extract_field_atomic_aggregate_03`

- chunk：`rfc4271_s033_5_1_6_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#5.1.6`
- section_path：ATOMIC_AGGREGATE
- match_score：8
- matched_terms：aggregate, aggregated, all, atomic_aggregate, path, present, rfc4271, when

> ATOMIC_AGGREGATE is a well-known discretionary attribute. When a BGP speaker aggregates several routes for the purpose of advertisement to a particular peer, the AS_PATH of the aggregated route normally includes an AS_SET formed from the set of ASes from which the aggregate was formed. In many cases, the network administrator can determine if the aggregate can safely be advertised without the AS_SET, and without forming route loops. If an aggregate excludes at least some of the AS numbers present in the AS_PATH of the routes that are aggregated as a result of dropping the AS_SET, the aggregated route, when advertised to the peer, SHOULD inclu...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. BGP Decision Process

- 实体 ID：`mechanism_bgp_decision_process`
- 实体类型：RoutingMechanism
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

#### `extract_mechanism_bgp_decision_process_01`

- chunk：`rfc4271_s060_9_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1`
- section_path：Decision Process
- match_score：13
- matched_terms：adj-ribs-in, adj-ribs-out, advertisement, attributes, decision, loc-rib, path, process, rfc4271, rib

> The Decision Process selects routes for subsequent advertisement by applying the policies in the local Policy Information Base (PIB) to the routes stored in its Adj-RIBs-In. The output of the Decision Process is the set of routes that will be advertised to peers; the selected routes will be stored in the local speaker's Adj-RIBs-Out, according to policy. The BGP Decision Process described here is conceptual, and does not have to be implemented precisely as described, as long as the implementations support the described functionality and they exhibit the same externally visible behavior. The selection process is formalized by defining a functi...

#### `extract_mechanism_bgp_decision_process_02`

- chunk：`rfc4271_s011_3_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.2`
- section_path：Routing Information Base
- match_score：11
- matched_terms：adj-ribs-in, adj-ribs-out, advertisement, decision, loc-rib, organizes, process, rfc4271, rib, routes

> The Routing Information Base (RIB) within a BGP speaker consists of three distinct parts: a) Adj-RIBs-In: The Adj-RIBs-In stores routing information learned from inbound UPDATE messages that were received from other BGP speakers. Their contents represent routes that are available as input to the Decision Process. b) Loc-RIB: The Loc-RIB contains the local routing information the BGP speaker selected by applying its local policies to the routing information contained in its Adj-RIBs-In. These are the routes that will be used by the local BGP speaker. The next hop for each of these routes MUST be resolvable via the local BGP speaker's Routing T...

#### `extract_mechanism_bgp_decision_process_03`

- chunk：`rfc4271_s062_9_1_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1.2`
- section_path：Phase 2: Route Selection
- match_score：10
- matched_terms：adj-ribs-in, as_path, decision, next_hop, path, process, rfc4271, rib, routes, selected

> The Phase 2 decision function is invoked on completion of Phase 1. The Phase 2 function is a separate process, which completes when it has no further work to do. The Phase 2 process considers all routes that are eligible in the Adj-RIBs-In. Rekhter, et al. Standards Track [Page 77] RFC 4271 BGP-4 January 2006 The Phase 2 decision function is blocked from running while the Phase 3 decision function is in process. The Phase 2 function locks all Adj-RIBs-In prior to commencing its function, and unlocks them on completion. If the NEXT_HOP attribute of a BGP route depicts an address that is not resolvable, or if it would become unresolvable if the...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. BGP RIB Model

- 实体 ID：`mechanism_rib_model`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `ripe_ris_raw_data`
- `routeviews_archive_index`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_raw_data.md`
- `cleaned/data_docs/routeviews_archive_index.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_raw_data.json`
- `parsed/data_docs/routeviews_archive_index.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_mechanism_rib_model_01`

- chunk：`rfc4271_s011_3_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.2`
- section_path：Routing Information Base
- match_score：14
- matched_terms：adj-ribs-in, adj-ribs-out, advertised, learned, loc-rib, local, model, peer, rfc4271, rib

> The Routing Information Base (RIB) within a BGP speaker consists of three distinct parts: a) Adj-RIBs-In: The Adj-RIBs-In stores routing information learned from inbound UPDATE messages that were received from other BGP speakers. Their contents represent routes that are available as input to the Decision Process. b) Loc-RIB: The Loc-RIB contains the local routing information the BGP speaker selected by applying its local policies to the routing information contained in its Adj-RIBs-In. These are the routes that will be used by the local BGP speaker. The next hop for each of these routes MUST be resolvable via the local BGP speaker's Routing T...

#### `extract_mechanism_rib_model_02`

- chunk：`rfc4271_s006_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：10
- matched_terms：adj-ribs-in, adj-ribs-out, advertised, local, peer, rfc4271, rib, routes, speaker, update

> ...vides definitions for terms that have a specific meaning to the BGP protocol and that are used throughout the text. Adj-RIB-In The Adj-RIBs-In contains unprocessed routing information that has been advertised to the local BGP speaker by its peers. Adj-RIB-Out The Adj-RIBs-Out contains the routes for advertisement to specific peers by means of the local speaker's UPDATE messages. Autonomous System (AS) The classic definition of an Autonomous System is a set of routers under a single technical administration, using an interior gateway protocol (IGP) and common metrics to determine how to route packets within the AS, and using an inter-AS routin...

#### `extract_mechanism_rib_model_03`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：10
- matched_terms：advertised, loc-rib, local, peer, rfc4271, rib, routes, selected, speaker, update

> Feasible route An advertised route that is available for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. St...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. BGP Roles and OTC Route Leak Prevention

- 实体 ID：`mechanism_route_leak_roles_otc`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc9234`

### cleaned 路径

- `cleaned/standards/rfc9234.md`

### parsed 路径

- `parsed/standards/rfc9234.json`

### Top 摘录

#### `extract_mechanism_route_leak_roles_otc_01`

- chunk：`rfc9234_s014_2_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#2`
- section_path：If a route already contains the OTC Attribute, it MUST NOT be
- match_score：16
- matched_terms：attribute, customer, detect, egress, ingress, leak, leaks, only, otc, peer

> propagated to Providers, Peers, or RSes. The above-described procedures provide both leak prevention for the local AS and leak detection and mitigation multiple hops away. In the case of prevention at the local AS, the presence of an OTC Attribute indicates to the egress router that the route was learned from a Peer, a Provider, or an RS, and it can be advertised only to the Customers. The same OTC Attribute that is set locally also provides a way to detect route leaks by an AS multiple hops away if a route is received from a Customer, a Peer, or an RS-Client. For example, if an AS sets the OTC Attribute on a route sent to a Peer and the rout...

#### `extract_mechanism_route_leak_roles_otc_02`

- chunk：`rfc9234_s018_8_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#8`
- section_path：Security Considerations
- match_score：16
- matched_terms：attribute, configured, customer, detect, leak, leaks, only, otc, path, peer

> ...iderations of BGP (as specified in [RFC4271] and [RFC4272]) apply. This document proposes a mechanism that uses the BGP Role for the prevention and detection of route leaks that are the result of BGP policy misconfiguration. A misconfiguration of the BGP Role may affect prefix propagation. For example, if a downstream (i.e., towards a Customer) peering link were misconfigured with a Provider or Peer Role, it would limit the number of prefixes that can be advertised in this direction. On the other hand, if an upstream provider were misconfigured (by a local AS) with the Customer Role, it may result in propagating routes that are received from...

#### `extract_mechanism_route_leak_roles_otc_03`

- chunk：`rfc9234_s009_5_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#5`
- section_path：BGP Only to Customer (OTC) Attribute
- match_score：15
- matched_terms：attribute, customer, detect, ingress, leak, only, otc, path, peer, prevent

> The OTC Attribute is an optional transitive Path Attribute of the UPDATE message with Attribute Type Code 35 and a length of 4 octets. The purpose of this attribute is to enforce that once a route is sent to a Customer, a Peer, or an RS-Client (see definitions in Section 3.1), it will subsequently go only to the Customers. The attribute value is an AS number (ASN) determined by the procedures described below. The following ingress procedure applies to the processing of the OTC Attribute on route receipt:

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. BGP Update and Withdrawal Propagation

- 实体 ID：`mechanism_update_withdrawal`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc4271`
- `ripe_ris_raw_data`
- `bgpstream_docs`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`
- `cleaned/data_docs/ripe_ris_raw_data.md`
- `cleaned/standards/rfc4271.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`
- `parsed/data_docs/ripe_ris_raw_data.json`
- `parsed/standards/rfc4271.json`

### Top 摘录

#### `extract_mechanism_update_withdrawal_01`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：12
- matched_terms：advertised, attributes, messages, nlri, path, previously, rfc4271, routes, service, update

> For the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the...

#### `extract_mechanism_update_withdrawal_02`

- chunk：`rfc4271_s059_9_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9`
- section_path：UPDATE Message Handling
- match_score：11
- matched_terms：advertised, feasible, nlri, previously, propagation, rfc4271, routes, service, update, withdraw

> An UPDATE message may be received only in the Established state. Receiving an UPDATE message in any other state is an error. When an UPDATE message is received, each field is checked for validity, as specified in Section 6.3. If an optional non-transitive attribute is unrecognized, it is quietly ignored. If an optional transitive attribute is unrecognized, the Partial bit (the third high-order bit) in the attribute flags octet is set to 1, and the attribute is retained for propagation to other BGP speakers. If an optional attribute is recognized and has a valid value, then, depending on the type of the optional attribute, it is processed loca...

#### `extract_mechanism_update_withdrawal_03`

- chunk：`rfc4271_s069_9_2_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.2.1.1`
- section_path：Frequency of Route Advertisement
- match_score：8
- matched_terms：advertised, feasible, messages, rfc4271, routes, update, withdraw, withdrawal

> ...nRouteAdvertisementIntervalTimer determines the minimum amount of time that must elapse between an advertisement and/or withdrawal of routes to a particular destination by a BGP speaker to a peer. This rate limiting procedure applies on a per- destination basis, although the value of MinRouteAdvertisementIntervalTimer is set on a per BGP peer basis. Two UPDATE messages sent by a BGP speaker to a peer that advertise feasible routes and/or withdrawal of unfeasible routes to some common set of destinations MUST be separated by at least MinRouteAdvertisementIntervalTimer. This can only be achieved by keeping a separate timer for each common set o...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
