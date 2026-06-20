# review_session_002 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：10
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：10

## 1. bgp_identifier

- 实体 ID：`field_bgp_identifier`
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

#### `extract_field_bgp_identifier_01`

- chunk：`rfc4271_s021_2_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#2`
- section_path：AS_SEQUENCE: ordered set of ASes a route in
- match_score：8
- matched_terms：field, identifier, message, not, prefix, reachability, rfc4271, speaker

> ...ontains the last AS number that formed the aggregate route (encoded as 2 octets), followed by the IP address of the BGP speaker that formed the aggregate route (encoded as 4 octets). This SHOULD be the same address as the one used for the BGP Identifier of the speaker. Usage of this attribute is defined in 5.1.7. Rekhter, et al. Standards Track [Page 19] RFC 4271 BGP-4 January 2006 Network Layer Reachability Information: This variable length field contains a list of IP address prefixes. The length, in octets, of the Network Layer Reachability Information is not encoded explicitly, but can be calculated as: UPDATE message Length - 23 - Total P...

#### `extract_field_bgp_identifier_02`

- chunk：`rfc4271_s014_4_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4.2`
- section_path：OPEN Message Format
- match_score：6
- matched_terms：field, identifier, message, open, rfc4271, speaker

> After a TCP connection is established, the first message sent by each side is an OPEN message. If the OPEN message is acceptable, a KEEPALIVE message confirming the OPEN is sent back. In addition to the fixed-size BGP header, the OPEN message contains the following fields: 0 1 2 3 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 +-+-+-+-+-+-+-+-+ \| Version \| +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ \| My Autonomous System \| +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ \| Hold Time \| +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ \| BGP Identifier \| +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ \| Opt Parm Len \|...

#### `extract_field_bgp_identifier_03`

- chunk：`rfc4271_s014_4_2_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4.2`
- section_path：OPEN Message Format
- match_score：6
- matched_terms：field, identifier, message, open, rfc4271, speaker

> This 4-octet unsigned integer indicates the BGP Identifier of the sender. A given BGP speaker sets the value of its BGP Identifier to an IP address that is assigned to that BGP speaker. The value of the BGP Identifier is determined upon startup and is the same for every local interface and BGP peer. Optional Parameters Length: This 1-octet unsigned integer indicates the total length of the Optional Parameters field in octets. If the value of this field is zero, no Optional Parameters are present. Optional Parameters: This field contains a list of optional parameters, in which each parameter is encoded as a <Parameter Type, Parameter Length, P...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. bgp_role

- 实体 ID：`field_bgp_role`
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

#### `extract_field_bgp_role_01`

- chunk：`rfc9234_s006_4_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#4`
- section_path：BGP Role
- match_score：14
- matched_terms：all, are, capability, configured, confirmed, leak, mutually, open, prevention, relationship

> The BGP Role characterizes the relationship between the eBGP speakers forming a session. One of the Roles described below SHOULD be configured at the local AS for each eBGP session (see definitions in Section 3) based on the local AS's knowledge of its Role. The only exception is when the eBGP connection is Complex (see Section 6). BGP Roles are mutually confirmed using the BGP Role Capability (described in Section 4.1) on each eBGP session. Allowed Roles for eBGP sessions are: Provider: the local AS is a transit provider of the remote AS; Customer: the local AS is a transit customer of the remote AS; RS: the local AS is a Route Server (usual...

#### `extract_field_bgp_role_02`

- chunk：`rfc9234_s002_1_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#1`
- section_path：Introduction
- match_score：11
- matched_terms：all, are, capability, configured, leak, open, prevention, relationship, rfc9234, role

> Route leaks are the propagation of BGP prefixes that violate assumptions of BGP topology relationships, e.g., announcing a route learned from one transit provider to another transit provider or a lateral (i.e., non-transit) peer or announcing a route learned from one lateral peer to another lateral peer or a transit provider [RFC7908]. These are usually the result of misconfigured or absent BGP route filtering or lack of coordination between autonomous systems (ASes). Existing approaches to leak prevention rely on marking routes by operator configuration, with no check that the configuration corresponds to that of the eBGP neighbor, or enforc...

#### `extract_field_bgp_role_03`

- chunk：`rfc9234_s007_4_1_001`
- 文档：`rfc9234`
- source_ref：`raw/standards/rfc9234.txt#4.1`
- section_path：BGP Role Capability
- match_score：11
- matched_terms：all, are, capability, configured, leak, open, prevention, relationship, rfc9234, role

> The BGP Role Capability is defined as follows: Code: 9 Length: 1 (octet) Value: integer corresponding to the speaker's BGP Role (see Table 1) +=======+==============================+ \| Value \| Role name (for the local AS) \| +=======+==============================+ \| 0 \| Provider \| +-------+------------------------------+ \| 1 \| RS \| +-------+------------------------------+ \| 2 \| RS-Client \| +-------+------------------------------+ \| 3 \| Customer \| +-------+------------------------------+ \| 4 \| Peer (i.e., Lateral Peer) \| +-------+------------------------------+ \| 5-255 \| Unassigned \| +-------+------------------------------+ Table 1: Predefined...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 3. BGPsec Path Validation

- 实体 ID：`mechanism_bgpsec_path_validation`
- 实体类型：RoutingMechanism
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc8205`
- `rfc6480`

### cleaned 路径

- `cleaned/standards/rfc6480.md`
- `cleaned/standards/rfc8205.md`

### parsed 路径

- `parsed/standards/rfc6480.json`
- `parsed/standards/rfc8205.json`

### Top 摘录

#### `extract_mechanism_bgpsec_path_validation_01`

- chunk：`rfc6480_s002_1_003`
- 文档：`rfc6480`
- source_ref：`raw/standards/rfc6480.txt#1`
- section_path：Introduction
- match_score：7
- matched_terms：certificates, not, rfc6480, rpki, security, signed, validation

> As noted above, the architecture is comprised of three main components: an X.509 PKI in which certificates attest to holdings of IP address space and AS numbers; non-certificate signed objects (including route origination authorizations and manifests) used by the infrastructure; and a distributed repository system that makes all of these signed objects available for use by ISPs in making routing decisions. These three basic components enable several security functions; most notably the cryptographic validation that an autonomous system is authorized to originate routes to a given prefix [RFC6483].

#### `extract_mechanism_bgpsec_path_validation_02`

- chunk：`rfc6480_s007_2_3_001`
- 文档：`rfc6480`
- source_ref：`raw/standards/rfc6480.txt#2.3`
- section_path：End-Entity (EE) Certificates
- match_score：7
- matched_terms：certificates, keys, not, protect, rfc6480, rpki, signed

> The private key corresponding to a public key contained in an EE certificate is not used to sign other certificates in a PKI. The primary function of end-entity certificates in this PKI is the verification of signed objects that relate to the usage of the resources described in the certificate, e.g., ROAs and manifests. For ROAs and manifests, there will be a one-to-one correspondence between end-entity certificates and signed objects, i.e., the private key corresponding to each end-entity certificate is used to sign exactly one object, and each object is signed with only one key. This property allows the PKI to be used to revoke these signed...

#### `extract_mechanism_bgpsec_path_validation_03`

- chunk：`rfc6480_s008_2_4_001`
- 文档：`rfc6480`
- source_ref：`raw/standards/rfc6480.txt#2.4`
- section_path：Trust Anchors
- match_score：7
- matched_terms：certificates, not, path, rfc6480, rpki, signed, validation

> ...es to be default TAs here. Nonetheless, each RP ultimately chooses the set of trust anchors it will use for certificate validation. For example, an RP (e.g., an LIR/ISP) could create a trust anchor to which all address space and/or all AS numbers are assigned, and for which the RP knows the corresponding private key. The RP could then issue certificates under this trust anchor to whatever entities in the PKI it wishes, with the result that the certification paths terminating at this locally installed trust anchor will satisfy the validation requirements specified in RFC 3779. A large ISP that uses private IP address space (i.e., RFC 1918) and...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 4. CAIDA ASRank

- 实体 ID：`datasource_caida_asrank`
- 实体类型：DataSource
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

#### `extract_datasource_caida_asrank_01`

- chunk：`caida_as_relationships_s001_full_011`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：12
- matched_terms：caida, caida_as_relationships, cone, customer, data, links, not, provides, rank, ranking

> AS relationships are more complex than allowed for in our approach. The semantics of routing relationships between the same two ASes can differ by peering location or even by prefix; our model oversimplifies these cases by assigning a single relationship to each pair of ASes. A truly accurate picture of the Internet topology would require collection of data from every AS, while our automated ranking procedure is limited to the measurement points publicly available at Route Views. As in all analyses of massive datasets, our heuristics have a number of associated external parameters. We fine tune the values of these parameters based on our pre-...

#### `extract_datasource_caida_asrank_02`

- chunk：`caida_as_relationships_s001_full_013`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：11
- matched_terms：access, caida, caida_as_relationships, cone, customer, data, links, rank, ranking, relationship

> Links discovered in this way are assumed to be peering links, since customer provider links are normally visible in the Routeviews BGP tables. The general serial-2 procedure for creating a file is as follows: Collect BGP communites from IX looking glass servers. Infer peering links between pairs of AS which accept routes from each other. Collect archived BGP data from Routeviews and RIPE RIS. Infer peering links at points in the observed AS paths that cross an known IX. Collect traceroutes from ark monitors. Convert the IP path to AS path using inferred ownership and keep the first AS link in the path. Merge all newly inferred links to the se...

#### `extract_datasource_caida_asrank_03`

- chunk：`caida_as_relationships_s001_full_008`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：10
- matched_terms：caida, caida_as_relationships, cone, customer, data, links, not, provides, rank, relationship

> Looking specifically at the AS customer cone , we define an AS A 's AS customer cone as the AS A itself plus all the ASes that can be reached from A following only p2c links in BGP paths we observed . In other words, A 's customer cone contains A , plus A 's customers, plus its customers' customers, and so on. Each AS announces a set of IPv4 prefixes. Each IPv4 prefix represents a set of contiguous IPv4 addresses which are routed as a unit. Prefixes can be nested, with the most specific prefix used for routing over less specific prefixes. To find the set of prefixes which are reachable in AS A 's IPv4 prefix customer cone create the union of...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 5. customer_cone_asns

- 实体 ID：`field_customer_cone_asns`
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

#### `extract_field_customer_cone_asns_01`

- chunk：`caida_as_relationships_s001_full_007`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：caida, caida_as_relationships, cone, customer, data, ground, inferred, relationships, truth

> ..., like the random breaking of ties which can yield obviously incorrect inferences, e.g., well-known large providers are inferred as customers of small ASes. In the first paper 6 we handled this issue with multiobjective optimization techniques that incorporated AS degree into the inference. In a subsequent paper 7 we introduced improved algorithms that determine not only c2p but also p2p links (for those we can detect from BGP data). These improvements achieved more accurate AS relationship inferences, which we demonstrate against ground truth for a set of ASes. Benjamin Hummel and Sven Kosub 8 introduced the idea that the resulting graph sho...

#### `extract_field_customer_cone_asns_02`

- chunk：`caida_as_relationships_s001_full_009`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：because, caida, caida_as_relationships, changes, cone, customer, data, over, relationships

> ASes with large customer cones play an important role in the Internet's capital and governance structure. At the top of this hierarchy are ISPs commonly known as Tier-1 ISPs, which do not pay for transit to upstream providers at all; instead they peer with each other to provide connectivity to all destinations in the Internet. At the bottom of the hierarchy are customer ASes who do not have their own customers and pay providers to reach all destinations in the Internet. We define peering cone size ratio as the ratio in customer cone sizes of a pair of ASes if they (hypothetically) peered. Similar customer cone sizes will have this ratio close...

#### `extract_field_customer_cone_asns_03`

- chunk：`caida_as_relationships_s001_full_011`
- 文档：`caida_as_relationships`
- source_ref：`raw/data_docs/caida_as_relationships.html#full`
- section_path：AS Relationships - CAIDA
- match_score：9
- matched_terms：caida, caida_as_relationships, cone, customer, data, inferred, over, relationships, source

> AS relationships are more complex than allowed for in our approach. The semantics of routing relationships between the same two ASes can differ by peering location or even by prefix; our model oversimplifies these cases by assigning a single relationship to each pair of ASes. A truly accurate picture of the Internet topology would require collection of data from every AS, while our automated ranking procedure is limited to the measurement points publicly available at Route Views. As in all analyses of massive datasets, our heuristics have a number of associated external parameters. We fine tune the values of these parameters based on our pre-...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 6. hold_time

- 实体 ID：`field_hold_time`
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

#### `extract_field_hold_time_01`

- chunk：`rfc4271_s024_6_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#6`
- section_path：Cease Section 6.7
- match_score：6
- matched_terms：can, hold, missing, open, rfc4271, time

> ...ed. 2 - Bad Message Length. 3 - Bad Message Type. Rekhter, et al. Standards Track [Page 22] RFC 4271 BGP-4 January 2006 OPEN Message Error subcodes: 1 - Unsupported Version Number. 2 - Bad Peer AS. 3 - Bad BGP Identifier. 4 - Unsupported Optional Parameter. 5 - [Deprecated - see Appendix A]. 6 - Unacceptable Hold Time. UPDATE Message Error subcodes: 1 - Malformed Attribute List. 2 - Unrecognized Well-known Attribute. 3 - Missing Well-known Attribute. 4 - Attribute Flags Error. 5 - Attribute Length Error. 6 - Invalid ORIGIN Attribute. 7 - [Deprecated - see Appendix A]. 8 - Invalid NEXT_HOP Attribute. 9 - Optional Attribute Error. 10 - Invalid...

#### `extract_field_hold_time_02`

- chunk：`rfc4271_s081_6_009`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#6`
- section_path：The Marker field has been expanded and its role broadened to
- match_score：6
- matched_terms：hold, missing, open, rfc4271, session, time

> ...Section 6.1 Bad Message Length 2 See Section 6.1 Bad Message Type 3 See Section 6.1 This document defines the following OPEN Message Error subcodes: Name Value Definition -------------------- ----- ---------- Unsupported Version Number 1 See Section 6.2 Bad Peer AS 2 See Section 6.2 Bad BGP Identifier 3 See Section 6.2 Unsupported Optional Parameter 4 See Section 6.2 [Deprecated] 5 See Appendix A Unacceptable Hold Time 6 See Section 6.2 This document defines the following UPDATE Message Error subcodes: Name Value Definition -------------------- --- ---------- Malformed Attribute List 1 See Section 6.3 Unrecognized Well-known Attribute 2 See S...

#### `extract_field_hold_time_03`

- chunk：`rfc4271_s040_6_5_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#6.5`
- section_path：Hold Timer Expired Error Handling
- match_score：5
- matched_terms：hold, open, rfc4271, time, within

> If a system does not receive successive KEEPALIVE, UPDATE, and/or NOTIFICATION messages within the period specified in the Hold Time field of the OPEN message, then the NOTIFICATION message with the Hold Timer Expired Error Code is sent and the BGP connection is closed. Rekhter, et al. Standards Track [Page 34] RFC 4271 BGP-4 January 2006

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 7. local_pref

- 实体 ID：`field_local_pref`
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

#### `extract_field_local_pref_01`

- chunk：`rfc4271_s021_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#2`
- section_path：AS_SEQUENCE: ordered set of ASes a route in
- match_score：8
- matched_terms：ases, local, local_pref, not, path, preference, rfc4271, update

> the UPDATE message has traversed The path segment length is a 1-octet length field, containing the number of ASes (not the number of octets) in the path segment value field. The path segment value field contains one or more AS numbers, each encoded as a 2-octet length field. Rekhter, et al. Standards Track [Page 18] RFC 4271 BGP-4 January 2006 Usage of this attribute is defined in 5.1.2. c) NEXT_HOP (Type Code 3): This is a well-known mandatory attribute that defines the (unicast) IP address of the router that SHOULD be used as the next hop to the destinations listed in the Network Layer Reachability Information field of the UPDATE message. U...

#### `extract_field_local_pref_02`

- chunk：`rfc4271_s026_4_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4`
- section_path：Optional non-transitive.
- match_score：7
- matched_terms：attributes, local, local_pref, not, path, rfc4271, update

> New, transitive optional attributes MAY be attached to the path by the originator or by any other BGP speaker in the path. If they are not attached by the originator, the Partial bit in the Attribute Flags octet is set to 1. The rules for attaching new non-transitive optional attributes will depend on the nature of the specific attribute. The documentation of each new non-transitive optional attribute will be expected to include such rules (the description of the MULTI_EXIT_DISC attribute gives an example). All optional attributes (both transitive and non-transitive), MAY be updated (if appropriate) by BGP speakers in the path. The sender of...

#### `extract_field_local_pref_03`

- chunk：`rfc4271_s032_5_1_5_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#5.1.5`
- section_path：LOCAL_PREF
- match_score：7
- matched_terms：local, local_pref, not, policy, preference, rfc4271, update

> LOCAL_PREF is a well-known attribute that SHALL be included in all UPDATE messages that a given BGP speaker sends to other internal peers. A BGP speaker SHALL calculate the degree of preference for each external route based on the locally-configured policy, and include the degree of preference when advertising a route to its internal peers. The higher degree of preference MUST be preferred. A BGP speaker uses the degree of preference learned via LOCAL_PREF in its Decision Process (see Section 9.1.1). A BGP speaker MUST NOT include this attribute in UPDATE messages it sends to external peers, except in the case of BGP Confederations [RFC3065]....

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 8. med

- 实体 ID：`field_med`
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

#### `extract_field_med_01`

- chunk：`rfc4271_s038_6_3_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#6.3`
- section_path：UPDATE Message Error Handling
- match_score：8
- matched_terms：attributes, handling, local, med, path, rfc4271, treat, update

> ...or. The Data field MUST contain the attribute (type, length, and value). If any attribute appears more than once in the UPDATE message, then the Error Subcode MUST be set to Malformed Attribute List. The NLRI field in the UPDATE message is checked for syntactic validity. If the field is syntactically incorrect, then the Error Subcode MUST be set to Invalid Network Field. If a prefix in the NLRI field is semantically incorrect (e.g., an unexpected multicast IP address), an error SHOULD be logged locally, and the prefix SHOULD be ignored. An UPDATE message that contains correct path attributes, but no NLRI, SHALL be treated as a valid UPDATE me...

#### `extract_field_med_02`

- chunk：`rfc4271_s006_1_1_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#1.1`
- section_path：Definition of Commonly Used Terms
- match_score：7
- matched_terms：attributes, between, local, path, rfc4271, update, within

> Feasible route An advertised route that is available for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Protocol - a routing protocol used to exchange routing information among routers within a single Autonomous System. Loc-RIB The Loc-RIB contains the routes that have been selected by the local BGP speaker's Decision Process. NLRI Network Layer Reachability Information. Route A unit of information that pairs a set of destinations with the attributes of a path to those destinations. The set of Rekhter, et al. St...

#### `extract_field_med_03`

- chunk：`rfc4271_s076_10_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#10`
- section_path：BGP Timers
- match_score：7
- matched_terms：between, local, med, path, rfc4271, update, within

> The relationship between the immediate next hop, and the next hop as specified in the NEXT_HOP path attribute. Clarification of the tie-breaking procedures. Clarification of the frequency of route advertisements. Optional Parameter Type 1 (Authentication Information) has been deprecated. UPDATE Message Error subcode 7 (AS Routing Loop) has been deprecated. OPEN Message Error subcode 5 (Authentication Failure) has been deprecated. Use of the Marker field for authentication has been deprecated. Implementations MUST support TCP MD5 [RFC2385] for authentication. Clarification of BGP FSM. Rekhter, et al. Standards Track [Page 92] RFC 4271 BGP-4 Ja...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 9. mrt_file_type

- 实体 ID：`field_mrt_file_type`
- 实体类型：DataField
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `ripe_ris_raw_data`
- `routeviews_archive_index`

### cleaned 路径

- `cleaned/data_docs/ripe_ris_raw_data.md`
- `cleaned/data_docs/routeviews_archive_index.md`

### parsed 路径

- `parsed/data_docs/ripe_ris_raw_data.json`
- `parsed/data_docs/routeviews_archive_index.json`

### Top 摘录

#### `extract_field_mrt_file_type_01`

- chunk：`ripe_ris_raw_data_s001_full_001`
- 文档：`ripe_ris_raw_data`
- source_ref：`raw/data_docs/ripe_ris_raw_data.html#full`
- section_path：RIPE Atlas docs \| Route Collection Raw Data: MRT Files \| Docs
- match_score：11
- matched_terms：data, file, files, raw, ripe, ripe_ris_raw_data, ris, routeviews, state, update

> RIPE Atlas docs \| Route Collection Raw Data: MRT Files \| Docs RIPE RIS Docs Centre Route collectors Route Collection Raw Data: MRT Files Name and location Tooling RIS Live RISwhois Routing Beacons Historical List of RIS Routing Beacons Prototypes Legal Information # Route Collection Raw Data: MRT Files Route collector projects (like RIS, Routeviews) store the data they capture in files in the MRT format (opens new window) . This data is useful for looking at the state of the BGP Internet, debugging/post-mortems of events in BGP, and tracking of long term trends in BGP. Typically 2 types of files are collected: dumps and updates . Dump files s...

#### `extract_field_mrt_file_type_02`

- chunk：`routeviews_archive_index_s001_full_001`
- 文档：`routeviews_archive_index`
- source_ref：`raw/data_docs/routeviews_archive_index.html#full`
- section_path：RouteViews Archive Project Page
- match_score：9
- matched_terms：archive, data, file, files, rib, routeviews, routeviews_archive_index, update, updates

> RouteViews Archive Project Page University of Oregon RouteViews Archive Project Please see www.routeviews.org for a description of the RouteViews project, bibliography, and additional information. For asn.routeviews.org zone files click here or ftp from: ftp.routeviews.org/dnszones/ Data Archives MRT format RIBs and UPDATEs (FRR bgpd, from route-views2.oregon-ix.net) MRT format RIBs and UPDATEs (FRR bgpd, from route-views3.routeviews.org) MRT format RIBs and UPDATEs (FRR bgpd, from route-views4.routeviews.org) MRT format RIBs and UPDATEs (FRR bgpd, from route-views5.routeviews.org) v6 MRT format RIBs and UPDATEs (FRR bgpd, from route-views6.o...

#### `extract_field_mrt_file_type_03`

- chunk：`routeviews_archive_index_s001_full_004`
- 文档：`routeviews_archive_index`
- source_ref：`raw/data_docs/routeviews_archive_index.html#full`
- section_path：RouteViews Archive Project Page
- match_score：9
- matched_terms：archive, data, file, files, rib, routeviews, routeviews_archive_index, update, updates

> MRT format RIBs and UPDATEs from DE-CIX (NY) (FRR bgpd, from route-views.ny.routeviews.org) MRT format RIBs and UPDATEs from DE-CIX JHB (FRR bgpd, from decix.jhb.routeviews.org) ipv6 data split out from the above files (multiple collectors) 'sh ip bgp' format RIBs from route-views.route-views.org ( to now ) route dampening data from route-views.route-views.org ( to March 2008 ) 'sh ip bgp' format RIBs from route-views3.routeviews.org ( to May 2012 ) route dampening data from route-views3.route-views.org ( to August 2012 ) The collector script that gathers the Cisco data was writted by Sean Mccreary. Note: MRT RIB and UPDATE files have interna...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 10. next_hop

- 实体 ID：`field_next_hop`
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

#### `extract_field_next_hop_01`

- chunk：`rfc4271_s026_4_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#4`
- section_path：Optional non-transitive.
- match_score：12
- matched_terms：as_path, attribute, attributes, context, field, hop, next_hop, not, path, rfc4271

> New, transitive optional attributes MAY be attached to the path by the originator or by any other BGP speaker in the path. If they are not attached by the originator, the Partial bit in the Attribute Flags octet is set to 1. The rules for attaching new non-transitive optional attributes will depend on the nature of the specific attribute. The documentation of each new non-transitive optional attribute will be expected to include such rules (the description of the MULTI_EXIT_DISC attribute gives an example). All optional attributes (both transitive and non-transitive), MAY be updated (if appropriate) by BGP speakers in the path. The sender of...

#### `extract_field_next_hop_02`

- chunk：`rfc4271_s038_6_3_002`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#6.3`
- section_path：UPDATE Message Error Handling
- match_score：11
- matched_terms：as_path, attribute, field, hop, next_hop, not, path, relationship, rfc4271, should

> If the NEXT_HOP attribute field is syntactically incorrect, then the Error Subcode MUST be set to Invalid NEXT_HOP Attribute. The Data field MUST contain the incorrect attribute (type, length, and value). Syntactic correctness means that the NEXT_HOP attribute represents a valid IP host address. The IP address in the NEXT_HOP MUST meet the following criteria to be considered semantically correct: a) It MUST NOT be the IP address of the receiving speaker. b) In the case of an EBGP, where the sender and receiver are one IP hop away from each other, either the IP address in the NEXT_HOP MUST be the sender's IP address that is used to establish t...

#### `extract_field_next_hop_03`

- chunk：`rfc4271_s021_2_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#2`
- section_path：AS_SEQUENCE: ordered set of ASes a route in
- match_score：10
- matched_terms：attribute, field, hop, next_hop, not, path, relationship, rfc4271, should, update

> the UPDATE message has traversed The path segment length is a 1-octet length field, containing the number of ASes (not the number of octets) in the path segment value field. The path segment value field contains one or more AS numbers, each encoded as a 2-octet length field. Rekhter, et al. Standards Track [Page 18] RFC 4271 BGP-4 January 2006 Usage of this attribute is defined in 5.1.2. c) NEXT_HOP (Type Code 3): This is a well-known mandatory attribute that defines the (unicast) IP address of the router that SHOULD be used as the next hop to the destinations listed in the Network Layer Reachability Information field of the UPDATE message. U...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
