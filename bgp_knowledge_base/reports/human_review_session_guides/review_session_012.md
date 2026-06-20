# review_session_012 人工复核指南

## 范围

本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。

## 摘要

- 条目数：2
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- ready_to_apply：2

## 1. WHOIS / RDAP

- 实体 ID：`concept_whois_rdap`
- 实体类型：BGPConcept
- 队列状态：`ready_to_apply`
- 当前实体状态：`approved`
- 当前人工决策：`approved`
- 人工决策输入：`review_inputs/human_review_decisions.csv`
- 下一步：显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。

### 来源引用

- `rfc3912`
- `rfc9082`
- `rfc9083`
- `context_2026`

### cleaned 路径

- `cleaned/standards/rfc3912.md`
- `cleaned/standards/rfc9082.md`
- `cleaned/standards/rfc9083.md`

### parsed 路径

- `parsed/standards/rfc3912.json`
- `parsed/standards/rfc9082.json`
- `parsed/standards/rfc9083.json`

### Top 摘录

#### `extract_concept_whois_rdap_01`

- chunk：`rfc3912_s008_21355_001`
- 文档：`rfc3912`
- source_ref：`raw/standards/rfc3912.txt#21355`
- section_path：Ridgetop Circle
- match_score：6
- matched_terms：can, information, not, provide, rfc3912, whois

> Dulles, VA 20166 US EMail: leslie@verisignlabs.com; leslie@thinkingcat.com Daigle Standards Track [Page 3] RFC 3912 WHOIS Protocol Specification September 2004 Full Copyright Statement Copyright (C) The Internet Society (2004). This document is subject to the rights, licenses and restrictions contained in BCP 78, and at www.rfc-editor.org, and except as set forth therein, the authors retain all their rights. This document and the information contained herein are provided on an "AS IS" basis and THE CONTRIBUTOR, THE ORGANIZATION HE/S HE REPRESENTS OR IS SPONSORED BY (IF ANY), THE INTERNET SOCIETY AND THE INTERNET ENGINEERING TASK FORCE DISCLAI...

#### `extract_concept_whois_rdap_02`

- chunk：`rfc3912_s001_1_001`
- 文档：`rfc3912`
- source_ref：`raw/standards/rfc3912.txt#1`
- section_path：Introduction
- match_score：5
- matched_terms：information, not, provide, rfc3912, whois

> WHOIS is a TCP-based transaction-oriented query/response protocol that is widely used to provide information services to Internet users. While originally used to provide "white pages" services and information about registered domain names, current deployments cover a much broader range of information services. The protocol delivers its content in a human-readable format. This document updates the specification of the WHOIS protocol, thereby obsoleting RFC 954 [1]. For historic reasons, WHOIS lacks many of the protocol design attributes, for example internationalisation and strong security, that would be expected from any recently-designed IET...

#### `extract_concept_whois_rdap_03`

- chunk：`rfc3912_s008_21355_002`
- 文档：`rfc3912`
- source_ref：`raw/standards/rfc3912.txt#21355`
- section_path：Ridgetop Circle
- match_score：5
- matched_terms：information, may, provide, rfc3912, whois

> ...rested party to bring to its attention any copyrights, patents or patent applications, or other proprietary rights that may cover technology that may be required to implement this standard. Please address the information to the IETF at ietf- ipr@ietf.org. Acknowledgement Funding for the RFC Editor function is currently provided by the Internet Society. Daigle Standards Track [Page 4]

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。

## 2. Withdrawal

- 实体 ID：`concept_withdrawal`
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

#### `extract_concept_withdrawal_01`

- chunk：`rfc4271_s069_9_2_1_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.2.1.1`
- section_path：Frequency of Route Advertisement
- match_score：7
- matched_terms：does, not, outage, peer, rfc4271, update, withdrawal

> ...nRouteAdvertisementIntervalTimer determines the minimum amount of time that must elapse between an advertisement and/or withdrawal of routes to a particular destination by a BGP speaker to a peer. This rate limiting procedure applies on a per- destination basis, although the value of MinRouteAdvertisementIntervalTimer is set on a per BGP peer basis. Two UPDATE messages sent by a BGP speaker to a peer that advertise feasible routes and/or withdrawal of unfeasible routes to some common set of destinations MUST be separated by at least MinRouteAdvertisementIntervalTimer. This can only be achieved by keeping a separate timer for each common set o...

#### `extract_concept_withdrawal_02`

- chunk：`rfc4271_s060_9_1_001`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#9.1`
- section_path：Decision Process
- match_score：5
- matched_terms：does, not, one, peer, rfc4271

> ...he routes stored in its Adj-RIBs-In. The output of the Decision Process is the set of routes that will be advertised to peers; the selected routes will be stored in the local speaker's Adj-RIBs-Out, according to policy. The BGP Decision Process described here is conceptual, and does not have to be implemented precisely as described, as long as the implementations support the described functionality and they exhibit the same externally visible behavior. The selection process is formalized by defining a function that takes the attribute of a given route as an argument and returns either (a) a non-negative integer denoting the degree of preferen...

#### `extract_concept_withdrawal_03`

- chunk：`rfc4271_s076_10_003`
- 文档：`rfc4271`
- source_ref：`raw/standards/rfc4271.txt#10`
- section_path：BGP Timers
- match_score：5
- matched_terms：not, prefix, prefixes, rfc4271, update

> ...n of the frequency of route advertisements. Optional Parameter Type 1 (Authentication Information) has been deprecated. UPDATE Message Error subcode 7 (AS Routing Loop) has been deprecated. OPEN Message Error subcode 5 (Authentication Failure) has been deprecated. Use of the Marker field for authentication has been deprecated. Implementations MUST support TCP MD5 [RFC2385] for authentication. Clarification of BGP FSM. Rekhter, et al. Standards Track [Page 92] RFC 4271 BGP-4 January 2006 Appendix B. Comparison with RFC 1267 All the changes listed in Appendix A, plus the following. BGP-4 is capable of operating in an environment where a set of...

### 复核边界

- 只根据人工打开的来源和摘录做核验。
- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。
- 本指南不自动产生 approved/rejected 决策。
