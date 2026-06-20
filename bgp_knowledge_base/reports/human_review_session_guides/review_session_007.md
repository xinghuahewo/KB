# review_session_007 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- manual_followup：3
- ready_to_apply：7

## 1. CAIDA AS Relationships

- 实体 ID：`datasource_caida_as_relationships`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `caida_as_relationships`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`

### Top 摘录

#### `extract_datasource_caida_as_relationships_01`

- chunk：`caida_as_relationships_s001_full_011`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：12
- matched_terms：analysis, caida, caida_as_relationships, cone, customer, dataset, inferred, links, provides, relationship

> AS relationships are more complex than allowed for in our approach. The semantics of routing relationships between the same two ASes can differ by peering location or even by prefix; our model oversimplifies these cases by assigning a single relationship to each pair of ASes. A truly accurate picture of the Internet topology would require collection of data from every AS, while our automated ranking procedure is limited to the measurement points publicly available at Route Views. As in all analyses of massive datasets, our heuristics have a number of associated external parameters. We fine tune the values of these parameters based on our pre-...

#### `extract_datasource_caida_as_relationships_02`

- chunk：`caida_as_relationships_s001_full_012`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：12
- matched_terms：business, caida, caida_as_relationships, customer, customer-provider, dataset, graph, inferred, links, relationship

> Serial-1 data is available from 1998 to present, with one file created per month. Each file contains a full AS graph derived from RouteViews and RIPE RIS BGP table snapshots taken at 24-hour intervals over a 5-day period. The AS relationships available are customer-provider (and provider-customer in the opposite direction), and peer-to-peer. See the README in the Serial-1 data directory for details of the file formats. The general serial-1 procedure for creating a file is as follows: Extract and clean AS paths from the BGP table snapshots. Infer the ASes that form a clique of transit-free networks at the top of the AS topology (Tier-1 ASes),...

#### `extract_datasource_caida_as_relationships_03`

- chunk：`caida_as_relationships_s001_full_013`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：12
- matched_terms：caida, caida_as_relationships, cone, customer, dataset, graph, inferred, links, related, relationship

> Links discovered in this way are assumed to be peering links, since customer provider links are normally visible in the Routeviews BGP tables. The general serial-2 procedure for creating a file is as follows: Collect BGP communites from IX looking glass servers. Infer peering links between pairs of AS which accept routes from each other. Collect archived BGP data from Routeviews and RIPE RIS. Infer peering links at points in the observed AS paths that cross an known IX. Collect traceroutes from ark monitors. Convert the IP path to AS path using inferred ownership and keep the first AS link in the path. Merge all newly inferred links to the se...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. CelerBridge BGP Hijack

- 实体 ID：`case_celerbridge_bgp_hijack`
- 实体类型：Case
- 队列状态：`manual_followup`
- 当前实体状态：`pending`
- 当前人工决策：`needs_source`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：补充来源或记录人工说明；不要自动批准。

### 来源引用

- `bgpshield_2025`
- `context_2026`

### cleaned 路径

- `cleaned/papers/bgpshield_2025.md`

### parsed 路径

- `parsed/papers/bgpshield_2025.json`

### Top 摘录

#### `extract_case_celerbridge_bgp_hijack_01`

- chunk：`bgpshield_2025_s002_page_2_001`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-2`
- section_path：Page 2
- match_score：9
- matched_terms：bgpshield_2025, celerbridge, event, hijack, historical, incident, prefix, report, requires

> ...bedded inconsistently, inevitably degrading anomaly detection precision. For instance, even BEAM can not detect several reported hijack incidents (e.g.,the CelerBridge event [22]), revealing its limitations in maintaining high detection precision and a low false discovery rate (FDR) [23]. Generalizability for Evolving Network Conditions.Another limitation lies in the static nature of topology-based embeddings, which capture only surface structural features while neglecting deeper routing policy semantics that remain relatively stable over time. Thus, embeddings derived from historical AS-level graphs may not adapt to evolving business relatio...

#### `extract_case_celerbridge_bgp_hijack_02`

- chunk：`bgpshield_2025_s004_page_4_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-4`
- section_path：Page 4
- match_score：8
- matched_terms：authoritative, bgpshield_2025, historical, incident, origin, prefix, public, report

> A route change will be recorded if the updated AS path diverges from the historical path associated with the matched prefix. For example, considering an updated prefix *.*.153.0/24with pathAS7500→AS2497→AS3491→AS17557. If the reference maps the broader historical prefix *.*.152.0/22 toAS7500→AS2497→AS36561, the difference signifies a route change. Notably, although the differences accurately reflect changes in routing behavior, they do not indicate anomalies, as some route changes result from legitimate operational practices (e.g.,traffic engineering or policy adjustments). The objective of BGPShield is to identify truly anomalous route chang...

#### `extract_case_celerbridge_bgp_hijack_03`

- chunk：`bgpshield_2025_s010_page_10_002`
- 文档：`bgpshield_2025`
- source_ref：`raw/papers/bgpshield_2025.pdf#page-10`
- section_path：Page 10
- match_score：8
- matched_terms：before, bgpshield_2025, event, historical, origin, prefix, report, target

> ...e live network access and contemporaneous measurements, making them inherently unsuitable for retrospective analysis of historical BGP datasets. Note that each detection system may generates multiple alerts for a single anomaly event, with each alert reporting a potential anomaly. Thus, we consider an alert valid if it matches confirmed information, particularly when the system identifies the target prefix as anomalous and accurately pinpoints the misbehaving AS as the responsible party, indicating successful detection of the confirmed anomaly for that event. Beyond confirmed anomalies, other alerts may indicate previously unrevealed routing...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. collector

- 实体 ID：`field_collector`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `routeviews_api_doc`
- `ripe_ris_docs`
- `bgpstream_docs`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/bgpstream_docs.md`
- `cleaned/data_docs/ripe_ris_docs.md`
- `cleaned/data_docs/routeviews_api_doc.md`

### parsed 路径

- `parsed/data_docs/bgpstream_docs.json`
- `parsed/data_docs/ripe_ris_docs.json`
- `parsed/data_docs/routeviews_api_doc.json`

### Top 摘录

#### `extract_field_collector_01`

- chunk：`context_2026_datasource_001`
- 文档：`context_2026`
- source_ref：`../context.md:BGP 数据源知识`
- section_path：BGP 数据源知识
- match_score：7
- matched_terms：bgpstream, collector, context_2026, evidence, ripe, ris, routeviews

> ...source should be described by data granularity, time resolution, main fields, suitable questions, unsuitable questions, evidence strength, and limitations. Collector and peer observation scope must be retained because missing collectors can produce false positives or unsupported claims.

#### `extract_field_collector_02`

- chunk：`routeviews_api_doc_s001_full_002`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：6
- matched_terms：api, bgpstream, collector, routeviews, routeviews_api_doc, set

> The RouteViews API is intended for network operators and researchers who need to make regular access to _current_ RouteViews data as part of their monitoring of the global routing system. The API is not intended for deep historical queries; the [MRT archive](https://archive.routeviews.org) combined with tools from [BGPKIT](https://bgpkit.com/parser) and [CAIDA](https://bgpstream.caida.org/) are recommended for this use case. Historically the RouteViews collectors have offered command line access for network operators to make quick checks about BGP announcements and general reachability information. However, with the continue growth of the Int...

#### `extract_field_collector_03`

- chunk：`bgpstream_docs_s001_full_001`
- 文档：`bgpstream_docs`
- source_ref：`raw/tools_docs/bgpstream_docs.html#full`
- section_path：BGPStream
- match_score：5
- matched_terms：api, bgpstream, bgpstream_docs, record, report

> BGPStream Toggle navigation Home News Components Download Documentation Publications Data Providers Acknowledgements Contact Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutorials BGPReader libBGPStream PyBGPStream Docker Data Encoding Overview Record Processing Record Extraction Data Access Install libBGPStream PyBGPStream Upgrade from Version 1 BGPReader APIs C/C++ bgpstream.h bgpstream_record.h bgpstream_elem.h Python low-level high-level HTTP (Metadata) Tutoria...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. Customer Cone

- 实体 ID：`concept_customer_cone`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `caida_as_relationships`
- `context_2026`

### cleaned 路径

- `cleaned/data_docs/caida_as_relationships.md`

### parsed 路径

- `parsed/data_docs/caida_as_relationships.json`

### Top 摘录

#### `extract_concept_customer_cone_01`

- chunk：`caida_as_relationships_s001_full_007`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：16
- matched_terms：addresses, ases, caida_as_relationships, cone, customer, data, following, graph, inferred, links

> ..., like the random breaking of ties which can yield obviously incorrect inferences, e.g., well-known large providers are inferred as customers of small ASes. In the first paper 6 we handled this issue with multiobjective optimization techniques that incorporated AS degree into the inference. In a subsequent paper 7 we introduced improved algorithms that determine not only c2p but also p2p links (for those we can detect from BGP data). These improvements achieved more accurate AS relationship inferences, which we demonstrate against ground truth for a set of ASes. Benjamin Hummel and Sven Kosub 8 introduced the idea that the resulting graph sho...

#### `extract_concept_customer_cone_02`

- chunk：`caida_as_relationships_s001_full_008`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：15
- matched_terms：addresses, ases, caida_as_relationships, cone, customer, data, following, graph, links, not

> Looking specifically at the AS customer cone , we define an AS A 's AS customer cone as the AS A itself plus all the ASes that can be reached from A following only p2c links in BGP paths we observed . In other words, A 's customer cone contains A , plus A 's customers, plus its customers' customers, and so on. Each AS announces a set of IPv4 prefixes. Each IPv4 prefix represents a set of contiguous IPv4 addresses which are routed as a unit. Prefixes can be nested, with the most specific prefix used for routing over less specific prefixes. To find the set of prefixes which are reachable in AS A 's IPv4 prefix customer cone create the union of...

#### `extract_concept_customer_cone_03`

- chunk：`caida_as_relationships_s001_full_012`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：15
- matched_terms：addresses, ases, available, caida_as_relationships, customer, data, graph, inferred, links, not

> Serial-1 data is available from 1998 to present, with one file created per month. Each file contains a full AS graph derived from RouteViews and RIPE RIS BGP table snapshots taken at 24-hour intervals over a 5-day period. The AS relationships available are customer-provider (and provider-customer in the opposite direction), and peer-to-peer. See the README in the Serial-1 data directory for details of the file formats. The general serial-1 procedure for creating a file is as follows: Extract and clean AS paths from the BGP table snapshots. Infer the ASes that form a clique of transit-free networks at the top of the AS topology (Tier-1 ASes),...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. eBGP

- 实体 ID：`concept_ebgp`
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

#### `extract_concept_ebgp_01`

- chunk：`rfc4271_s009_3_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：10
- matched_terms：between, different, does, ebgp, external, not, peer, relationship, rfc4271, systems

> ...explicit update fragmentation, retransmission, acknowledgement, and sequencing. BGP listens on TCP port 179. The error notification mechanism used in BGP assumes that TCP supports a "graceful" close (i.e., that all outstanding data will be delivered before the connection is closed). A TCP connection is formed between two systems. They exchange messages to open and confirm the connection parameters. The initial data flow is the portion of the BGP routing table that is allowed by the export policy, called the Adj-Ribs-Out (see 3.2). Incremental updates are sent as the routing tables change. BGP does not require a periodic refresh of the routin...

#### `extract_concept_ebgp_02`

- chunk：`rfc4271_s006_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：8
- matched_terms：autonomous, between, different, ebgp, external, peer, relationship, rfc4271

> ...IB-In The Adj-RIBs-In contains unprocessed routing information that has been advertised to the local BGP speaker by its peers. Adj-RIB-Out The Adj-RIBs-Out contains the routes for advertisement to specific peers by means of the local speaker's UPDATE messages. Autonomous System (AS) The classic definition of an Autonomous System is a set of routers under a single technical administration, using an interior gateway protocol (IGP) and common metrics to determine how to route packets within the AS, and using an inter-AS routing protocol to determine how to route packets to other ASes. Since this classic definition was developed, it has become co...

#### `extract_concept_ebgp_03`

- chunk：`rfc4271_s030_5_1_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#5.1.3`
- section_path：NEXT_HOP
- match_score：8
- matched_terms：does, ebgp, external, itself, not, peer, relationship, rfc4271

> - Otherwise, if the route being announced was learned from an external peer, the speaker can use an IP address of any adjacent router (known from the received NEXT_HOP attribute) that the speaker itself uses for local route calculation in the NEXT_HOP attribute, provided that peer X shares a common subnet with this address. This is a second form of "third party" NEXT_HOP attribute. - Otherwise, if the external peer to which the route is being advertised shares a common subnet with one of the interfaces of the announcing BGP speaker, the speaker MAY use the IP address associated with such an interface in the NEXT_HOP attribute. This is known a...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. Facebook 2021 Outage

- 实体 ID：`case_facebook_2021_outage`
- 实体类型：Case
- 队列状态：`manual_followup`
- 当前实体状态：`pending`
- 当前人工决策：`needs_source`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：补充来源或记录人工说明；不要自动批准。

### 来源引用

- `facebook_outage_cloudflare_2021`
- `facebook_outage_meta_2021`
- `context_2026`

### cleaned 路径

- `cleaned/cases/facebook_outage_cloudflare_2021.md`
- `cleaned/cases/facebook_outage_meta_2021.md`

### parsed 路径

- `parsed/cases/facebook_outage_cloudflare_2021.json`
- `parsed/cases/facebook_outage_meta_2021.json`

### Top 摘录

#### `extract_case_facebook_2021_outage_01`

- chunk：`facebook_outage_cloudflare_2021_s001_full_004`
- 文档：`facebook_outage_cloudflare_2021`
- source_ref：`raw/cases/facebook_outage_cloudflare_2021.html#full`
- section_path：Understanding how Facebook disappeared from the Internet
- match_score：7
- matched_terms：2021, facebook, facebook_outage_cloudflare_2021, outage, prefix, updates, withdrawal

> We keep track of all the BGP updates and announcements we see in our global network. At our scale, the data we collect gives us a view of how the Internet is connected and where the traffic is meant to flow from and to everywhere on the planet. A BGP UPDATE message informs a router of any changes you’ve made to a prefix advertisement or entirely withdraws the prefix. We can clearly see this in the number of updates we received from Facebook when checking our time-series BGP database. Normally this chart is fairly quiet: Facebook doesn’t make a lot of changes to its network minute to minute. But at around 15:40 UTC we saw a peak of routing cha...

#### `extract_case_facebook_2021_outage_02`

- chunk：`facebook_outage_cloudflare_2021_s001_full_008`
- 文档：`facebook_outage_cloudflare_2021`
- source_ref：`raw/cases/facebook_outage_cloudflare_2021.html#full`
- section_path：Understanding how Facebook disappeared from the Internet
- match_score：7
- matched_terms：2021, case, collector, facebook, facebook_outage_cloudflare_2021, outage, report

> ...implemented safer configuration changes and automated best practices to prevent future incidents. ... By Jeremy Hartman Outage , Post Mortem , Code Orange Getting Started Free plans For enterprises Compare plans Get a recommendation Request a demo Contact Sales Resources Learning Center Analyst reports Cloudflare Radar Cloudflare TV Case Studies Webinars White Papers Developer docs theNet Solutions Connectivity cloud SSE and SASE services Application services Network services Developer services Community Community Hub Project Galileo Athenian Project Cloudflare for Campaigns Connect 2024 Support Help center Cloudflare Status Compliance GDPR T...

#### `extract_case_facebook_2021_outage_03`

- chunk：`facebook_outage_cloudflare_2021_s001_full_001`
- 文档：`facebook_outage_cloudflare_2021`
- source_ref：`raw/cases/facebook_outage_cloudflare_2021.html#full`
- section_path：Understanding how Facebook disappeared from the Internet
- match_score：6
- matched_terms：2021, 2021-10-04, facebook, facebook_outage_cloudflare_2021, outage, report

> Understanding how Facebook disappeared from the Internet Get Started Free \| Contact Sales \| ▼ The Cloudflare Blog Subscribe to receive notifications of new posts: Subscribe AI Developers Radar Product News Security Policy & Legal Zero Trust Speed & Reliability Life at Cloudflare Partners AI Developers Radar Product News Security Policy & Legal Zero Trust Speed & Reliability Life at Cloudflare Partners Understanding how Facebook disappeared from the Internet 2021-10-04 Celso Martinho Tom Strickx 5 min read This post is also available in 简体中文 , Français , Deutsch , Italiano , 日本語 , 한국어 , Português , Español , Рyсский and 繁體中文 . The Internet - A...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. FIB

- 实体 ID：`concept_fib`
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

#### `extract_concept_fib_01`

- chunk：`rfc4271_s009_3_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：8
- matched_terms：base, forward, forwarding, information, not, rfc4271, rib, router

> ...otocol. It is built on experience gained with EGP (as defined in [RFC904]) and EGP usage in the NSFNET Backbone (as described in [RFC1092] and [RFC1093]). For more BGP-related information, see [RFC1772], [RFC1930], [RFC1997], and [RFC2858]. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity, from which routing loops may be pruned, and, at the AS level, some policy...

#### `extract_concept_fib_02`

- chunk：`rfc4271_s005_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：base, forward, forwarding, information, not, rfc4271, router

> ...r-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information includes information on the list of Autonomous Systems (ASes) that reachability information traverses. This information is sufficient for constructing a graph of AS connectivity for this reachability, from which routing loops may be pruned and, at the AS level, some policy decisions may be enforced. BGP-4 provides a set of mechanisms for supporting Classless Inter- Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertisi...

#### `extract_concept_fib_03`

- chunk：`rfc4271_s009_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：6
- matched_terms：base, forward, forwarding, packets, rfc4271, router

> RFC 4271 BGP-4 January 2006 traffic to a neighboring AS for forwarding to some destination (reachable through but) beyond that neighboring AS, intending that the traffic take a different route to that taken by the traffic originating in the neighboring AS (for that same destination). On the other hand, BGP can support any policy conforming to the destination-based forwarding paradigm. BGP-4 provides a new set of mechanisms for supporting Classless Inter-Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertising a set of destinations as an IP prefix and eliminating the concept of a network "class" within BGP. BG...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. iBGP

- 实体 ID：`concept_ibgp`
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

#### `extract_concept_ibgp_01`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：11
- matched_terms：autonomous, ibgp, igp, internal, rfc4271, routes, same, single, speaker, system

> Feasible route An advertised route that is available for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. St...

#### `extract_concept_ibgp_02`

- chunk：`rfc4271_s009_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：9
- matched_terms：autonomous, igp, policy, rfc4271, routes, same, single, system, within

> ...ending that the traffic take a different route to that taken by the traffic originating in the neighboring AS (for that same destination). On the other hand, BGP can support any policy conforming to the destination-based forwarding paradigm. BGP-4 provides a new set of mechanisms for supporting Classless Inter-Domain Routing (CIDR) [RFC1518, RFC1519]. These mechanisms include support for advertising a set of destinations as an IP prefix and eliminating the concept of a network "class" within BGP. BGP-4 also introduces mechanisms that allow aggregation of routes, including aggregation of AS paths. This document uses the term `Autonomous System...

#### `extract_concept_ibgp_03`

- chunk：`rfc4271_s009_3_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3`
- section_path：Summary of Operation
- match_score：9
- matched_terms：ibgp, internal, not, policy, rfc4271, routes, same, speaker, system

> ...explicit update fragmentation, retransmission, acknowledgement, and sequencing. BGP listens on TCP port 179. The error notification mechanism used in BGP assumes that TCP supports a "graceful" close (i.e., that all outstanding data will be delivered before the connection is closed). A TCP connection is formed between two systems. They exchange messages to open and confirm the connection parameters. The initial data flow is the portion of the BGP routing table that is allowed by the export policy, called the Adj-Ribs-Out (see 3.2). Incremental updates are sent as the routing tables change. BGP does not require a periodic refresh of the routin...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. Indosat Route Leak

- 实体 ID：`case_indosat_route_leak`
- 实体类型：Case
- 队列状态：`manual_followup`
- 当前实体状态：`pending`
- 当前人工决策：`needs_source`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：补充来源或记录人工说明；不要自动批准。

### 来源引用

- `indosat_route_leak_2014`
- `context_2026`

### cleaned 路径

- `cleaned/cases/indosat_route_leak_2014.md`

### parsed 路径

- `parsed/cases/indosat_route_leak_2014.json`

### Top 摘录

#### `extract_case_indosat_route_leak_01`

- chunk：`context_2026_route_leak_001`
- 文档：`context_2026`
- source_ref：`../context.md:EvidenceTemplate route_leak`
- section_path：EvidenceTemplate / route_leak
- match_score：7
- matched_terms：before, collector, context_2026, evidence, leak, observations, requires

> Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorrect AS relationship inference, complex business relationships, legitimate policy changes, and temporary route flaps.

#### `extract_case_indosat_route_leak_02`

- chunk：`indosat_route_leak_2014_s001_full_002`
- 文档：`indosat_route_leak_2014`
- source_ref：`raw/cases/indosat_route_leak_2014.html#full`
- section_path：Indosat fat-thumbs route announcements (again)
- match_score：5
- matched_terms：case, indosat, indosat_route_leak_2014, leak, report

> The Indosat hijack affected 320,349 prefixes. Most routes via AS4651 (THAI-GATEWAY) and 6939 (HE) pic.twitter.com/bbG23jbT9T — BGPmon.net (@bgpmon) April 2, 2014 As noted by BGPmon, Indosat has form for route announcement hijacks. In 2011 it made a similar mistake, announcing itself as originating “approximately 2800 new unique prefixes of 824 unique Autonomous systems, whereas normally they originate approximately 100 prefixes.” Renesys posted a Tweet saying the global impact would be far less than the 320,000 prefixes: only 354 of the prefixes leaked by Indosat are seen globally, it said, with 104 of those belonging to Akamai. While some er...

#### `extract_case_indosat_route_leak_03`

- chunk：`indosat_route_leak_2014_s001_full_003`
- 文档：`indosat_route_leak_2014`
- source_ref：`raw/cases/indosat_route_leak_2014.html#full`
- section_path：Indosat fat-thumbs route announcements (again)
- match_score：5
- matched_terms：collector, indosat, indosat_route_leak_2014, leak, report

> Ofqual says smart glasses, hidden earpieces, and AI tools are creating a new generation of cheating headaches SaaS AWS reportedly to tuck Elon Musk's Grok into Bedrock, despite zero enterprise demand The energy drink of frontier models security Oxford Uni student data pwned yet again - this time via career platform breach Totally different attack from the break-in last month. Oh so that's OK then MOST POPULAR SECURITY All the passwords were stored in Active Directory description fields AI and ML Netflix wiz creates app to slash AI bills, then open sources it public sector GOV.UK goes Dutch on payments as it dumps Stripe Personal tech Californ...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. IRR

- 实体 ID：`concept_irr`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc2622`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc2622.md`

### parsed 路径

- `parsed/standards/rfc2622.json`

### Top 摘录

#### `extract_concept_irr_01`

- chunk：`rfc2622_s014_1_002`
- 文档：`rfc2622`
- source_ref：`raw/standards/rfc2622.txt#1`
- section_path：Introduction
- match_score：10
- matched_terms：can, data, internet, irr, not, object, policy, prefix, registry, rfc2622

> RPSL was designed so that a view of the global routing policy can be contained in a single cooperatively maintained distributed database to improve the integrity of Internet's routing. RPSL is not designed to be a router configuration language. RPSL is designed so that router configurations can be generated from the description of the policy for one autonomous system (aut-num class) combined with the description of a router (inet-rtr class), mainly providing router ID, autonomous system number of the router, interfaces and peers of the router, and combined with a global database mappings from AS sets to ASes (as-set class), and from origin AS...

#### `extract_concept_irr_02`

- chunk：`context_2026_as_path_001`
- 文档：`context_2026`
- source_ref：`../context.md:DataField field_as_path`
- section_path：结构化实体设计 / DataField
- match_score：7
- matched_terms：context_2026, data, interpretation, not, prefix, should, treated

> AS_PATH must be interpreted carefully. The final AS in a simple AS_PATH is usually the origin AS for the prefix. Intermediate ASes should not be mislabeled as destination or origin ASes. Repeated ASNs may indicate AS_PATH prepending and should not be treated as a distinct route leak without additional evidence.

#### `extract_concept_irr_03`

- chunk：`rfc2622_s016_3_001`
- 文档：`rfc2622`
- source_ref：`raw/standards/rfc2622.txt#3`
- section_path：Contact Information
- match_score：7
- matched_terms：can, data, not, object, policy, registry, rfc2622

> ...act information. The mntner class also specifies authenticaiton information required to create, delete and update other objects. These classes do not specify routing policies and each registry may have different or additional requirements on them. Here we present the common denominator for completeness which is the RIPE database implementation [16]. Please consult your routing registry for the latest specification of these classes and attributes. The "Routing Policy System Security" document [20] describes the authenticaiton and authorization model in more detail. 3.1 mntner Class The mntner class specifies authenticaiton information required...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
