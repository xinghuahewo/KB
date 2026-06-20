# review_session_003 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. nlri

- 实体 ID：`field_nlri`
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

#### `extract_field_nlri_01`

- chunk：`rfc4271_s021_2_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#2`
- section_path：AS_SEQUENCE: ordered set of ASes a route in
- match_score：18
- matched_terms：all, attribute, attributes, length, may, multiple, nlri, one, path, prefix

> The Prefix field contains an IP address prefix, followed by enough trailing bits to make the end of the field fall on an octet boundary. Note that the value of the trailing bits is irrelevant. The minimum length of the UPDATE message is 23 octets -- 19 octets for the fixed header + 2 octets for the Withdrawn Routes Length + 2 octets for the Total Path Attribute Length (the value of Withdrawn Routes Length is 0 and the value of Total Path Attribute Length is 0). Rekhter, et al. Standards Track [Page 20] RFC 4271 BGP-4 January 2006 An UPDATE message can advertise, at most, one set of path attributes, but multiple destinations, provided that the...

#### `extract_field_nlri_02`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：17
- matched_terms：all, attribute, attributes, may, multiple, nlri, one, path, prefix, prefixes

> For the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the...

#### `extract_field_nlri_03`

- chunk：`rfc4271_s015_4_3_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4.3`
- section_path：UPDATE Message Format
- match_score：13
- matched_terms：all, attribute, attributes, length, may, multiple, path, reachability, rfc4271, routes

> UPDATE messages are used to transfer routing information between BGP peers. The information in the UPDATE message can be used to construct a graph that describes the relationships of the various Autonomous Systems. By applying rules to be discussed, routing Rekhter, et al. Standards Track [Page 14] RFC 4271 BGP-4 January 2006 information loops and some other anomalies may be detected and removed from inter-AS routing. An UPDATE message is used to advertise feasible routes that share common path attributes to a peer, or to withdraw multiple unfeasible routes from service (see 3.1). An UPDATE message MAY simultaneously advertise a feasible rout...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. origin_attribute

- 实体 ID：`field_origin_attribute`
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

#### `extract_field_origin_attribute_01`

- chunk：`rfc4271_s015_4_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4.3`
- section_path：UPDATE Message Format
- match_score：10
- matched_terms：attribute, attributes, code, indicates, information, not, path, rfc4271, type, update

> A value of 0 indicates that no routes are being withdrawn from service, and that the WITHDRAWN ROUTES field is not present in this UPDATE message. Withdrawn Routes: This is a variable-length field that contains a list of IP address prefixes for the routes that are being withdrawn from service. Each IP address prefix is encoded as a 2-tuple of the form <length, prefix>, whose fields are described below: +---------------------------+ \| Length (1 octet) \| +---------------------------+ \| Prefix (variable) \| +---------------------------+ Rekhter, et al. Standards Track [Page 15] RFC 4271 BGP-4 January 2006 The use and the meaning of these fields a...

#### `extract_field_origin_attribute_02`

- chunk：`rfc4271_s024_6_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#6`
- section_path：Cease Section 6.7
- match_score：10
- matched_terms：as_path, attribute, code, information, not, origin, path, rfc4271, type, update

> Error subcode: This 1-octet unsigned integer provides more specific information about the nature of the reported error. Each Error Code may have one or more Error Subcodes associated with it. If no appropriate Error Subcode is defined, then a zero (Unspecific) value is used for the Error Subcode field. Message Header Error subcodes: 1 - Connection Not Synchronized. 2 - Bad Message Length. 3 - Bad Message Type. Rekhter, et al. Standards Track [Page 22] RFC 4271 BGP-4 January 2006 OPEN Message Error subcodes: 1 - Unsupported Version Number. 2 - Bad Peer AS. 3 - Bad BGP Identifier. 4 - Unsupported Optional Parameter. 5 - [Deprecated - see Append...

#### `extract_field_origin_attribute_03`

- chunk：`rfc4271_s021_2_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#2`
- section_path：AS_SEQUENCE: ordered set of ASes a route in
- match_score：9
- matched_terms：attribute, attributes, code, indicates, information, not, path, rfc4271, update

> AGGREGATOR is an optional transitive attribute of length 6. The attribute contains the last AS number that formed the aggregate route (encoded as 2 octets), followed by the IP address of the BGP speaker that formed the aggregate route (encoded as 4 octets). This SHOULD be the same address as the one used for the BGP Identifier of the speaker. Usage of this attribute is defined in 5.1.7. Rekhter, et al. Standards Track [Page 19] RFC 4271 BGP-4 January 2006 Network Layer Reachability Information: This variable length field contains a list of IP address prefixes. The length, in octets, of the Network Layer Reachability Information is not encoded...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. otc_attribute

- 实体 ID：`field_otc_attribute`
- 实体类型：DataField
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

#### `extract_field_otc_attribute_01`

- chunk：`rfc9234_s018_8_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#8`
- section_path：Security Considerations
- match_score：9
- matched_terms：leak, negotiation, only, otc, path, received, rfc9234, role, update

> ...iderations of BGP (as specified in [RFC4271] and [RFC4272]) apply. This document proposes a mechanism that uses the BGP Role for the prevention and detection of route leaks that are the result of BGP policy misconfiguration. A misconfiguration of the BGP Role may affect prefix propagation. For example, if a downstream (i.e., towards a Customer) peering link were misconfigured with a Provider or Peer Role, it would limit the number of prefixes that can be advertised in this direction. On the other hand, if an upstream provider were misconfigured (by a local AS) with the Customer Role, it may result in propagating routes that are received from...

#### `extract_field_otc_attribute_02`

- chunk：`rfc9234_s009_5_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#5`
- section_path：BGP Only to Customer (OTC) Attribute
- match_score：8
- matched_terms：leak, only, otc, path, procedures, rfc9234, role, update

> The OTC Attribute is an optional transitive Path Attribute of the UPDATE message with Attribute Type Code 35 and a length of 4 octets. The purpose of this attribute is to enforce that once a route is sent to a Customer, a Peer, or an RS-Client (see definitions in Section 3.1), it will subsequently go only to the Customers. The attribute value is an AS number (ASN) determined by the procedures described below. The following ingress procedure applies to the processing of the OTC Attribute on route receipt:

#### `extract_field_otc_attribute_03`

- chunk：`rfc9234_s014_2_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#2`
- section_path：If a route already contains the OTC Attribute, it MUST NOT be
- match_score：8
- matched_terms：leak, only, otc, procedures, received, rfc9234, role, update

> propagated to Providers, Peers, or RSes. The above-described procedures provide both leak prevention for the local AS and leak detection and mitigation multiple hops away. In the case of prevention at the local AS, the presence of an OTC Attribute indicates to the egress router that the route was learned from a Peer, a Provider, or an RS, and it can be advertised only to the Customers. The same OTC Attribute that is set locally also provides a way to detect route leaks by an AS multiple hops away if a route is received from a Customer, a Peer, or an RS-Client. For example, if an AS sets the OTC Attribute on a route sent to a Peer and the rout...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. path_attributes

- 实体 ID：`field_path_attributes`
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

#### `extract_field_path_attributes_01`

- chunk：`rfc4271_s026_4_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4`
- section_path：Optional non-transitive.
- match_score：13
- matched_terms：attribute, attributes, flags, may, nlri, path, rfc4271, set, should, they

> New, transitive optional attributes MAY be attached to the path by the originator or by any other BGP speaker in the path. If they are not attached by the originator, the Partial bit in the Attribute Flags octet is set to 1. The rules for attaching new non-transitive optional attributes will depend on the nature of the specific attribute. The documentation of each new non-transitive optional attribute will be expected to include such rules (the description of the MULTI_EXIT_DISC attribute gives an example). All optional attributes (both transitive and non-transitive), MAY be updated (if appropriate) by BGP speakers in the path. The sender of...

#### `extract_field_path_attributes_02`

- chunk：`rfc4271_s010_3_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#3.1`
- section_path：Routes: Advertisement and Storage
- match_score：10
- matched_terms：associated, attribute, attributes, may, nlri, path, prefixes, rfc4271, set, update

> For the purpose of this protocol, a route is defined as a unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of destinations are systems whose IP addresses are contained in one IP address prefix that is carried in the Network Layer Reachability Information (NLRI) field of an UPDATE message, and the path is the information reported in the path attributes field of the same UPDATE message. Routes are advertised between BGP speakers in UPDATE messages. Multiple routes that have the same path attributes can be advertised in a single UPDATE message by including multiple prefixes in the...

#### `extract_field_path_attributes_03`

- chunk：`rfc4271_s015_4_3_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4.3`
- section_path：UPDATE Message Format
- match_score：10
- matched_terms：attribute, attributes, codes, flags, rfc4271, set, they, transitive, type, update

> Attribute Type is a two-octet field that consists of the Attribute Flags octet, followed by the Attribute Type Code octet. 0 1 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ \| Attr. Flags \|Attr. Type Code\| +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ The high-order bit (bit 0) of the Attribute Flags octet is the Optional bit. It defines whether the attribute is optional (if set to 1) or well-known (if set to 0). Rekhter, et al. Standards Track [Page 16] RFC 4271 BGP-4 January 2006 The second high-order bit (bit 1) of the Attribute Flags octet is the Transitive bit. It defines whether an optional attribute is transitive (if set to 1) o...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. PeeringDB

- 实体 ID：`datasource_peeringdb`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `peeringdb_api_docs`

### cleaned 路径

- `cleaned/data_docs/peeringdb_api_docs.md`

### parsed 路径

- `parsed/data_docs/peeringdb_api_docs.json`

### Top 摘录

#### `extract_datasource_peeringdb_01`

- chunk：`peeringdb_api_docs_s002_paths_033`
- 文档：`peeringdb_api_docs`
- source_ref：`raw/data_docs/peeringdb_api_docs.yaml#paths`
- section_path：paths
- match_score：9
- matched_terms：api, exchange, facility, network, peer, peering, peeringdb, peeringdb_api_docs, prove

> Identified by the `fac` tag. ### Parent relationship: - `org` organization ### Relationship(s): - `ixfac` exchange / facility presence - `netfac` network / facility presence ## Creating objects ### Status `pending` Some object types will be flagged as `pending` until they have been reviewed and approved by peeringdb staff. Currently this is the case for: - `org` organizations (only administrative staff users are currently allowed to create organizations) - `fac` facilities - `net` networks - `ix` exchanges - `ixpfx` prefixes (if part of a new exchange) - `ixlan` exchange networks (if part of a new exchange) ### Permissions To be able to creat...

#### `extract_datasource_peeringdb_02`

- chunk：`peeringdb_api_docs_s002_paths_106`
- 文档：`peeringdb_api_docs`
- source_ref：`raw/data_docs/peeringdb_api_docs.yaml#paths`
- section_path：paths
- match_score：9
- matched_terms：api, exchange, facility, network, peer, peering, peeringdb, peeringdb_api_docs, prove

> ...n: schema: type: object required: - data - meta properties: data: type: array items: $ref: '#/components/schemas/CarrierFacilityList' meta: type: object properties: generated: type: number description: Unix timestamp of when the cached response was generated. Only present for cached responses. pagination: type: object description: Only present when using the ?page= parameter. properties: count: type: integer has_next: type: boolean has_previous: type: boolean next: type: string nullable: true format: uri previous: type: string nullable: true format: uri page: type: integer per_page: type: integer total_pages: type: integer description: '' tag...

#### `extract_datasource_peeringdb_03`

- chunk：`peeringdb_api_docs_s002_paths_170`
- 文档：`peeringdb_api_docs`
- source_ref：`raw/data_docs/peeringdb_api_docs.yaml#paths`
- section_path：paths
- match_score：9
- matched_terms：api, exchange, facility, network, peer, peering, peeringdb, peeringdb_api_docs, prove

> ...: schema: type: object required: - data - meta properties: data: type: array items: $ref: '#/components/schemas/InternetExchangeList' meta: type: object properties: generated: type: number description: Unix timestamp of when the cached response was generated. Only present for cached responses. pagination: type: object description: Only present when using the ?page= parameter. properties: count: type: integer has_next: type: boolean has_previous: type: boolean next: type: string nullable: true format: uri previous: type: string nullable: true format: uri page: type: integer per_page: type: integer total_pages: type: integer description: '' tag...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. RIPEstat Data API

- 实体 ID：`datasource_ripestat`
- 实体类型：DataSource
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `ripestat_api_docs`
- `ripe_ris_docs`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_docs.md`
- `cleaned/data_docs/ripestat_api_docs.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_docs.json`
- `parsed/data_docs/ripestat_api_docs.json`

### Top 摘录

#### `extract_datasource_ripestat_01`

- chunk：`ripestat_api_docs_s001_full_001`
- 文档：`ripestat_api_docs`
- source_ref：`raw/data_docs/ripestat_api_docs.html#full`
- section_path：About the Data API \| RIPE NCC
- match_score：14
- matched_terms：api, asn, data, endpoints, history, peers, prefix, resource, ripe, ripestat

> About the Data API \| RIPE NCC Skip to content RIPE NCC Search Meta K Menu Return to top Sidebar Navigation Getting Started What is RIPEstat? Data Sources Data API About the Data API API Endpoints Abuse Contact Finder Address Space Hierarchy Address Space Usage Allocation History Announced Prefixes AS Overview AS Path Length AS Routing Consistency ASN Neighbours History ASN Neighbours Atlas Probe Deployment Atlas Probes Atlas Targets BGP State BGP Update Activity BGP Updates BGPlay Country ASNs Country Resource List Country Resource Stats DNS Blocklists DNS Chain Example Resources Historical Whois IANA Registry Info Looking Glass MaxMind GeoLi...

#### `extract_datasource_ripestat_02`

- chunk：`ripestat_api_docs_s001_full_003`
- 文档：`ripestat_api_docs`
- source_ref：`raw/data_docs/ripestat_api_docs.html#full`
- section_path：About the Data API \| RIPE NCC
- match_score：8
- matched_terms：api, data, query, resource, ripe, ripestat, ripestat_api_docs, rpki

> If you are using the API on a regular basis you can use the " sourceapp " parameter to provide a unique identifier to every endpoint. This identifier helps us to assist you when you encounter any problems with the system. The identifier can be your project name or your company's. Please drop us a short mail to stat@ripe.net with the identifier and an email address on which we can reach you. (If you include the purpose of the lookups, gold membership support is awaiting you 😃 https://stat.ripe.net/data/<endpoint>/data.json?resource=AS3333&sourceapp=<your-identifier> For the format please just use alphanumeric values with no whitespace and no s...

#### `extract_datasource_ripestat_03`

- chunk：`ripestat_api_docs_s001_full_004`
- 文档：`ripestat_api_docs`
- source_ref：`raw/data_docs/ripestat_api_docs.html#full`
- section_path：About the Data API \| RIPE NCC
- match_score：8
- matched_terms：api, data, endpoints, ripe, ripestat, ripestat_api_docs, rpki, should

> ...ved either by the expiration date or soon. PLEASE CHECK ON THIS FLAG REGULARLY IF YOU WANT TO HAVE A RELIABLE SOURCE OF DATA! * development This endpoint is currently work in progress and to be considered to change or discontinued without notice. This guarantees that we can incorporate user feedback in the most efficient way - so bug reports are highly welcome! data_call_name string Holds the name of the endpoint; this is useful for our team and when only the API output is available in a support request. version string major . minor version of the response layout for this particular endpoint. New minor versions are backwards compatible, new m...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. routeviews_endpoint

- 实体 ID：`field_routeviews_endpoint`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `routeviews_api_doc`

### cleaned 路径

- `cleaned/data_docs/routeviews_api_doc.md`

### parsed 路径

- `parsed/data_docs/routeviews_api_doc.json`

### Top 摘录

#### `extract_field_routeviews_endpoint_01`

- chunk：`routeviews_api_doc_s001_full_011`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：8
- matched_terms：api, collectors, endpoint, parameters, query, routeviews, routeviews_api_doc, time

> This endpoint allows you to retrieve a list of network prefixes learned from a specific BGP peer on a given RouteViews collector, identified by the collector name, the peer's Autonomous System Number (ASN), and IP address. This data is part of our near real-time RIB (Routing Information Base) information. **Path Parameters:** * *`COLLECTOR`*: The name of the RouteViews collector (e.g., `route-views3`, `ix-br2.gru`). Use the `/rib/collectors` endpoint to discover available collectors. * *`PEER-ASN`*: The Autonomous System Number of the BGP peer (e.g., `209`). * *`PEER-IP`*: The IP address of the BGP peer (e.g., `2001:428::205:171:8:123`). **Op...

#### `extract_field_routeviews_endpoint_02`

- chunk：`routeviews_api_doc_s001_full_019`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：8
- matched_terms：api, endpoint, output, query, routeviews, routeviews_api_doc, time, which

> If you are more interested in chasing or monitoring of potential hijacks, we recommend the near real-time data in the /prefix end-point. The output of the /prefix call does contain the RPKI state as well. Note that the RPKI validators are the same for both data sets. It is just a question of where the prefixes are collected and validated. To query the validation state of any single prefix in the RKPI endpoint, use this syntax: ```sh curl -L -s "https://api.routeviews.org/rpki?prefix=43.224.43.0/24" \| jq . ``` which gives this response: ```json { "43.224.43.0/24": { "asn": [ { "45558": "invalid" } ], "timestamp": "2024-07-13T04:07:01.653+00:00...

#### `extract_field_routeviews_endpoint_03`

- chunk：`routeviews_api_doc_s001_full_020`
- 文档：`routeviews_api_doc`
- source_ref：`raw/data_docs/routeviews_api_doc.html#full`
- section_path：RouteViews API Documentation
- match_score：8
- matched_terms：api, collectors, endpoint, output, query, routeviews, routeviews_api_doc, time

> ....0.0/18": "valid" }, { "89.239.192.0/18": "valid" }, { "212.178.160.0/19": "valid" }, { "2a02:17c0::/32": "valid" } ], "timestamp": "2024-07-13T04:07:01.653+00:00" } } ``` ## Endpoints discoverable from API root The following table lists the API Root Options (all discoverable from the API root). \| Term \| Explanation \| \|---\|---\| \| [collector](#collector) \| a list of RouteViews Collectors in operation \| \| [peer](#peer) \| individual peer listings \| \| [peering](#peering) \| peering statistics per peer/collector \| \| [timeseries](#timeseries) \| peering counts over time\| \| [rirtimeseries](#rirtimeseries) \| rir grouped peering counts over time \| These...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. RPKI-to-Router Delivery

- 实体 ID：`mechanism_rpki_to_router_delivery`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc8210`
- `rfc6480`

### cleaned 路径

- `cleaned/standards/rfc6480.md`
- `cleaned/standards/rfc8210.md`

### parsed 路径

- `parsed/standards/rfc6480.json`
- `parsed/standards/rfc8210.json`

### Top 摘录

#### `extract_mechanism_rpki_to_router_delivery_01`

- chunk：`rfc6480_s010_3_1_001`
- 文档：`rfc6480`
- source_ref：`raw/standards/rfc6480.txt#3.1`
- section_path：Role in the Overall Architecture
- match_score：7
- matched_terms：rfc6480, roa, router, routers, rpki, use, validated

> A ROA is an attestation that the holder of a set of prefixes has authorized an autonomous system to originate routes for those prefixes. A ROA is structured according to the format described in [RFC6482]. The validity of this authorization depends on the signer of the ROA being the holder of the prefix(es) in the ROA; this fact is asserted by an end-entity certificate from the PKI, whose corresponding private key is used to sign the ROA. ROAs may be used by relying parties to verify that the AS that originates a route for a given IP address prefix is authorized by the holder of that prefix to originate such a route. For example, an ISP might...

#### `extract_mechanism_rpki_to_router_delivery_02`

- chunk：`rfc6480_s012_4_001`
- 文档：`rfc6480`
- source_ref：`raw/standards/rfc6480.txt#4`
- section_path：Repositories
- match_score：7
- matched_terms：data, protocol, records, rfc6480, roa, rpki, use

> Initially, an LIR/ISP will make use of the resource PKI by acquiring and validating every ROA, to create a table of the prefixes for which each AS is authorized to originate routes. To validate all ROAs, an LIR/ISP needs to acquire all the certificates and CRLs. The primary function of the distributed repository system described here is to store these signed objects and to make them available for download by LIRs/ISPs. Note that this repository system provides a mechanism by which relying parties can pull fresh data at whatever frequency they deem appropriate. However, it does not provide a mechanism for pushing fresh data to relying parties...

#### `extract_mechanism_rpki_to_router_delivery_03`

- chunk：`rfc6480_s002_1_001`
- 文档：`rfc6480`
- source_ref：`raw/standards/rfc6480.txt#1`
- section_path：Introduction
- match_score：5
- matched_terms：data, protocol, rfc6480, rpki, use

> ...RFC4271] for the Internet. The architecture encompasses three principle elements: o Resource Public Key Infrastructure (RPKI) o digitally signed routing objects to support routing security o a distributed repository system to hold the PKI objects and the signed routing objects The architecture described by this document enables an entity to verifiably assert that it is the legitimate holder of a set of IP addresses or a set of Autonomous System (AS) numbers. As an initial application of this architecture, the document describes how a legitimate holder of IP address space can explicitly and verifiably authorize one or more ASes to originate ro...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. rpki_rtr_pdu

- 实体 ID：`field_rpki_rtr_pdu`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc8210`

### cleaned 路径

- `cleaned/standards/rfc8210.md`

### parsed 路径

- `parsed/standards/rfc8210.json`

### Top 摘录

#### `extract_field_rpki_rtr_pdu_01`

- chunk：`rfc8210_s002_1_001`
- 文档：`rfc8210`
- source_ref：`raw/standards/rfc8210.txt#1`
- section_path：Introduction
- match_score：11
- matched_terms：announcement, cache, data, origin, pdu, pdus, protocol, rfc8210, rpki, update

> In order to verifiably validate the origin Autonomous Systems (ASes) and AS paths of BGP announcements, routers need a simple but reliable mechanism to receive cryptographically validated Resource Public Key Infrastructure (RPKI) [RFC6480] prefix origin data and router keys from a trusted cache. This document describes a protocol to deliver them. The design is intentionally constrained to be usable on much of the current generation of ISP router platforms. This document updates [RFC6810]. Section 3 describes the deployment structure, and Section 4 then presents an operational overview. The binary payloads of the protocol are formally describe...

#### `extract_field_rpki_rtr_pdu_02`

- chunk：`rfc8210_s013_5_5_001`
- 文档：`rfc8210`
- source_ref：`raw/standards/rfc8210.txt#5.5`
- section_path：Cache Response
- match_score：10
- matched_terms：announcement, cache, data, not, pdu, pdus, protocol, raw, rfc8210, rpki

> The cache responds to queries with zero or more payload PDUs. When replying to a Serial Query (Section 5.3), the cache sends the set of announcements and withdrawals that have occurred since the Serial Number sent by the client router. When replying to a Reset Query (Section 5.4), the cache sends the set of all data records it has; in this case, the withdraw/announce field in the payload PDUs MUST have the value 1 (announce). In response to a Reset Query, the new value of the Session ID tells the router the instance of the cache session for future confirmation. In response to a Serial Query, the Session ID being the same reassures the router...

#### `extract_field_rpki_rtr_pdu_03`

- chunk：`rfc8210_s038_14_001`
- 文档：`rfc8210`
- source_ref：`raw/standards/rfc8210.txt#14`
- section_path：IANA Considerations
- match_score：10
- matched_terms：cache, data, not, origin, pdu, protocol, rfc8210, rpki, rpki-rtr, update

> This section only discusses updates required in the existing IANA protocol registries to accommodate version 1 of this protocol. See [RFC6810] for IANA considerations from the original (version 0) protocol. All existing entries in the IANA "rpki-rtr-pdu" registry remain valid for protocol version 0. All of the PDU types allowed in protocol version 0 are also allowed in protocol version 1, with the addition of the new Router Key PDU. To reduce the likelihood of confusion, the PDU number used by the Router Key PDU in protocol version 1 is hereby registered as reserved (and unused) in protocol version 0. The policy for adding to the registry is...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. rrc

- 实体 ID：`field_ris_rrc`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `ripe_ris_docs`
- `ripe_ris_route_collectors`
- `ripe_ris_raw_data`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_docs.md`
- `cleaned/data_docs/ripe_ris_raw_data.md`
- `cleaned/data_docs/ripe_ris_route_collectors.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_docs.json`
- `parsed/data_docs/ripe_ris_raw_data.json`
- `parsed/data_docs/ripe_ris_route_collectors.json`

### Top 摘录

#### `extract_field_ris_rrc_01`

- chunk：`ripe_ris_raw_data_s001_full_001`
- 文档：`ripe_ris_raw_data`
- source_ref：`raw/data_docs/ripe_ris_raw_data.html#full`
- section_path：RIPE Atlas docs \| Route Collection Raw Data: MRT Files \| Docs
- match_score：10
- matched_terms：collector, data, have, peering, raw, ripe, ripe_ris_raw_data, ris, rrc, rrcs

> RIPE Atlas docs \| Route Collection Raw Data: MRT Files \| Docs RIPE RIS Docs Centre Route collectors Route Collection Raw Data: MRT Files Name and location Tooling RIS Live RISwhois Routing Beacons Historical List of RIS Routing Beacons Prototypes Legal Information # Route Collection Raw Data: MRT Files Route collector projects (like RIS, Routeviews) store the data they capture in files in the MRT format (opens new window) . This data is useful for looking at the state of the BGP Internet, debugging/post-mortems of events in BGP, and tracking of long term trends in BGP. Typically 2 types of files are collected: dumps and updates . Dump files s...

#### `extract_field_ris_rrc_02`

- chunk：`ripe_ris_route_collectors_s001_full_001`
- 文档：`ripe_ris_route_collectors`
- source_ref：`raw/data_docs/ripe_ris_route_collectors.html#full`
- section_path：RIPE Atlas docs \| Route collectors \| Docs
- match_score：10
- matched_terms：collector, data, have, keep, peering, raw, ripe, ripe_ris_route_collectors, ris, rrc

> RIPE Atlas docs \| Route collectors \| Docs RIPE RIS Docs Centre Route collectors Peer meta-data BGP Timer settings Route Collection Raw Data: MRT Files RIS Live RISwhois Routing Beacons Historical List of RIS Routing Beacons Prototypes Legal Information # Route collectors Route collectors are the (physical or virtual) machines where RIS ingests BGP routing data. We receive this data via BGP peering sessions, where RIPE RIS uses AS12654 (opens new window) . Most route collectors collect data from peers at IXP peering LANs that the route collectors are physically attached to. We also have 'multi-hop' route collectors, which collect BGP data from...

#### `extract_field_ris_rrc_03`

- chunk：`ripe_ris_route_collectors_s001_full_003`
- 文档：`ripe_ris_route_collectors`
- source_ref：`raw/data_docs/ripe_ris_route_collectors.html#full`
- section_path：RIPE Atlas docs \| Route collectors \| Docs
- match_score：10
- matched_terms：collector, data, have, keep, locations, raw, ripe, ripe_ris_route_collectors, ris, rrc

> RRC26 Dubai, AE IXP UAE-IX data (opens new window) Datamena (opens new window) , UAE-IX (opens new window) Historic route collectors are listed in this table: Name Physical Location Type Scope Raw Data RRC02 Paris, FR IXP SFINX data (opens new window) RRC08 San Jose, CA, US IXP MAE-WEST data (opens new window) RRC09 Zurich, CH IXP TIX data (opens new window) Locations are also available in dns LOC records # Peer meta-data RIPEstat has an API (rrc-info) (opens new window) with the current RIS peers and their numbers of routes. Furthermore, there is a prototype with machine-readable metadata for the multihop peers in our peer metadata prototype...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
