# 查询样例报告

## 范围

本报告运行 `scripts/query_knowledge_base.py` 的固定查询样例，验证 `published/bgp_knowledge_base.sqlite` 可被程序化查询。

该步骤不联网、不下载、不调用 LLM、不做语义判断。

## 摘要

- 查询样例数：24
- 通过数：24
- 失败数：0
- SQLite integrity_check：ok

## 样例结果

| 名称 | 命令 | 状态 | 摘要 |
| --- | --- | --- | --- |
| stats | `python3 scripts/query_knowledge_base.py stats` | 通过 | integrity_check=ok |
| term_route | `python3 scripts/query_knowledge_base.py term route --limit 5` | 通过 | term=route, entities=5, sources=5, chunks=5 |
| entity_route_leak | `python3 scripts/query_knowledge_base.py entity anomaly_route_leak` | 通过 | entity_id=anomaly_route_leak, sources=4 |
| neighbors_as_path | `python3 scripts/query_knowledge_base.py neighbors concept_as_path` | 通过 | entity_id=concept_as_path, incoming=3, outgoing=2 |
| source_rfc4271 | `python3 scripts/query_knowledge_base.py source rfc4271` | 通过 | source_id=rfc4271, entities=43, chunks=20 |
| evidence_route_leak | `python3 scripts/query_knowledge_base.py evidence anomaly_route_leak` | 通过 | entity_id=anomaly_route_leak, records=4 |
| review_packets_ready | `python3 scripts/query_knowledge_base.py review-packets --bucket ready_without_manual_note --limit 5` | 通过 | 5 records |
| workbook_first_batch | `python3 scripts/query_knowledge_base.py workbook --batch 01_ready_without_manual_note --limit 5` | 通过 | 5 records |
| extracts_route_leak | `python3 scripts/query_knowledge_base.py extracts anomaly_route_leak --limit 3` | 通过 | entity_id=anomaly_route_leak, records=3 |
| sessions_first | `python3 scripts/query_knowledge_base.py sessions --session-id review_session_001 --limit 5` | 通过 | 5 records |
| actions_open | `python3 scripts/query_knowledge_base.py actions --status open --limit 5` | 通过 | 5 records |
| actions_llm_skipped | `python3 scripts/query_knowledge_base.py actions --needs-llm true --limit 5` | 通过 | 2 records |
| observations_asn | `python3 scripts/query_knowledge_base.py observations --type asn --limit 5` | 通过 | 5 records |
| glossary_route | `python3 scripts/query_knowledge_base.py glossary route --limit 5` | 通过 | 5 records |
| decision_audit_ready_to_apply | `python3 scripts/query_knowledge_base.py decision-audit --status ready_to_apply --limit 5` | 通过 | 5 records |
| apply_preview_summary | `python3 scripts/query_knowledge_base.py apply-preview --record-type summary --limit 5` | 通过 | 1 records |
| input_validation_pass | `python3 scripts/query_knowledge_base.py input-validation --status pass --limit 5` | 通过 | 5 records |
| progress_overall | `python3 scripts/query_knowledge_base.py progress --scope-type overall --limit 5` | 通过 | 1 records |
| field_checks_first | `python3 scripts/query_knowledge_base.py field-checks --session-id review_session_001 --limit 5` | 通过 | 5 records |
| source_matrix_rfc4271 | `python3 scripts/query_knowledge_base.py source-matrix --source-id rfc4271 --limit 5` | 通过 | 1 records |
| task_board_sessions | `python3 scripts/query_knowledge_base.py task-board --type review_session --limit 5` | 通过 | 5 records |
| handoff_sessions | `python3 scripts/query_knowledge_base.py handoff --type review_session --limit 5` | 通过 | 5 records |
| search_entities_rpki | `python3 scripts/query_knowledge_base.py search-entities RPKI --limit 5` | 通过 | 5 records |
| search_chunks_route_leak | `python3 scripts/query_knowledge_base.py search-chunks "route leak" --limit 5` | 通过 | 5 records |

## 输出节选

### stats

```json
{
  "case_observations": 148,
  "chunk_topics": 4332,
  "chunks": 2037,
  "entities": 112,
  "entity_evidence": 246,
  "entity_sources": 246,
  "entity_types": {
    "AnomalyType": 8,
    "BGPConcept": 31,
    "Case": 5,
    "DataField": 32,
    "DataSource": 9,
    "EvidenceTemplate": 8,
    "FalsePositivePattern": 4,
    "PaperMethod": 3,
    "RoutingMechanism": 12
  },
  "glossary": 112,
  "human_review_decision_apply_preview": 110,
  "human_review_decision_audit": 112,
  "human_review_evidence_extracts": 672,
  "human_review_field_checklist": 834,
  "human_review_handoff": 25,
  "human_review_input_validation": 8,
  "human_review_progress": 14,
  "human_review_session_queue": 112,
  "human_review_session_status": 12,
  "human_review_source_matrix": 31,
  "human_review_task_board": 25,
  "human_review_workbook": 112,
  "integrity_check": "ok",
  "lexical_chunk_refs": 8996,
  "lexical_entity_refs": 685,
  "lexical_source_refs": 524,
  "lexical_terms": 951,
  "next_actions": 114,
  "relationships": 106,
  "review_packets": 112,
  "review_statuses": {
    "approved": 107,
    "pending": 5
  },
  "sources": 54
}
```

### term_route

```json
{
  "chunks": [
    {
      "chunk_id": "artemis_2018_s003_page_3_002",
      "content_chars": 1614,
      "content_preview": "Example Hijack Scenarios & Motivations The following examples illustrate different hijack scenar ios, their underlying motivation, and how they are classiﬁed according to the presented taxonomy. Human Error. The hijack is the result of a ro",
      "doc_id": "artemis_2018",
      "source_type": "paper",
      "title": "ARTEMIS: Neutralizing BGP Hijacking within a Minute"
    },
    {
      "chunk_id": "artemis_2018_s015_page_15_002",
      "content_chars": 1781,
      "content_preview": "[4] www.wired.com/2014/08/isp-bitcoin-theft/. [5] A. Ramachandran and N. Feamster, “Understanding the net work-level behavior of spammers,” ACM SIGCOMM CCR , vol. 36, no. 4, pp. 291– 302, 2006. [6] P .-A. V ervier, O. Thonnard, and M. Dacie",
      "doc_id": "artemis_2018",
      "source_type": "paper",
      "title": "ARTEMIS: Neutralizing BGP Hijacking within a Minute"
    },
    {
      "chunk_id": "aws_route53_crypto_hijack_2018_s001_full_001",
      "content_chars": 1466,
      "content_preview": "BGP leaks and cryptocurrencies Get Started Free | Contact Sales | ▼ The Cloudflare Blog Subscribe to receive notifications of new posts: Subscribe AI Developers Radar Product News Security Policy & Legal Zero Trust Speed & Reliability Life ",
      "doc_id": "aws_route53_crypto_hijack_2018",
      "source_type": "case_report",
      "title": "BGP leaks and cryptocurrencies"
    },
    {
      "chunk_id": "aws_route53_crypto_hijack_2018_s001_full_002",
      "content_chars": 1532,
      "content_preview": "The broad definition of a BGP leak would be IP space that is announced by somebody not allowed by the owner of the space. When a transit provider picks up Cloudflare's announcement of 1.1.1.0/24 and announces it to the Internet, we allow th",
      "doc_id": "aws_route53_crypto_hijack_2018",
      "source_type": "case_report",
      "title": "BGP leaks and cr
```

### entity_route_leak

```json
{
  "actions": [
    {
      "action_id": "action_entity_review_anomaly_route_leak",
      "action_order": 95,
      "action_type": "entity_human_review",
      "needs_llm": 0,
      "priority": 4,
      "status": "open",
      "suggested_action": "人工核验非 manual_note 来源；context_2026 只作为范围提示，不作为单独批准依据。"
    }
  ],
  "case_observation_count": 0,
  "category": "Policy Violation",
  "chunk_count": 101,
  "entity_file": "entities/anomaly_types.jsonl",
  "entity_id": "anomaly_route_leak",
  "entity_type": "AnomalyType",
  "evidence": [
    {
      "case_observation_count": 0,
      "chunk_count": 62,
      "chunk_sample_ids_json": "[\"beam_2024_s009_page_9_003\", \"beam_2024_s013_page_13_001\", \"beam_2024_s002_page_2_003\", \"beam_2024_s003_page_3_003\", \"beam_2024_s011_page_11_003\", \"beam_2024_s009_page_9_001\", \"beam_2024_s014_page_14_002\", \"beam_2024_s015_page_15_001\", \"beam_2024_s004_page_4_002\", \"beam_2024_s009_page_9_002\", \"beam_2024_s010_page_10_003\", \"beam_2024_s003_page_3_001\", \"beam_2024_s004_page_4_001\", \"beam_2024_s010_page_10_002\", \"beam_2024_s013_page_13_002\", \"beam_2024_s014_page_14_001\", \"beam_2024_s015_page_15_002\", \"beam_2024_s003_page_3_002\", \"beam_2024_s007_page_7_004\", \"beam_2024_s008_page_8_002\"]",
      "cleaned_path": "cleaned/papers/beam_2024.md",
      "evidence_id": "anomaly_route_leak__beam_2024",
      "parsed_path": "parsed/papers/beam_2024.json",
      "source_id": "beam_2024",
      "source_path": "raw/papers/beam_2024.pdf",
      "source_status": "complete_deterministic",
      "source_type": "paper"
    },
    {
      "case_observation_count": 0,
      "chunk_count": 15,
      "chunk_sample_ids_json": "[\"rfc7908_s005_2_001\", \"rfc7908_s015_6_001\", \"rfc7908_s008_3_2_001\", \"rfc7908_s013_4_001\", \"rfc7908_s007_3_1_001\", \"rfc7908_s004_1_001\", \"rfc7908_s006_3_001\", \"rfc7908_s009_3_3_001\", \"rfc7908_s010_3_4_001\", \"rfc7908_s012_3_6_001\", \"rfc7908_s017_2013_001\", \"rfc7908_s003_6_001\", \"rfc7908
```

### neighbors_as_path

```json
{
  "entity_id": "concept_as_path",
  "incoming": [
    {
      "confidence": 0.85,
      "peer_id": "concept_origin_as",
      "peer_type": "BGPConcept",
      "relation": "derived_from",
      "source_refs_json": "[\"rfc4271\", \"context_2026\"]"
    },
    {
      "confidence": 0.85,
      "peer_id": "concept_rpki",
      "peer_type": "BGPConcept",
      "relation": "does_not_validate_full",
      "source_refs_json": "[\"rfc6811\", \"context_2026\"]"
    },
    {
      "confidence": 0.8,
      "peer_id": "mechanism_bgpsec_path_validation",
      "peer_type": "RoutingMechanism",
      "relation": "secures",
      "source_refs_json": "[\"rfc8205\"]"
    }
  ],
  "outgoing": [
    {
      "confidence": 0.95,
      "peer_id": "concept_bgp_update",
      "peer_type": "BGPConcept",
      "relation": "belongs_to",
      "source_refs_json": "[\"rfc4271\"]"
    },
    {
      "confidence": 0.9,
      "peer_id": "concept_rib",
      "peer_type": "BGPConcept",
      "relation": "belongs_to",
      "source_refs_json": "[\"rfc4271\", \"bgpstream_docs\"]"
    }
  ]
}
```

### source_rfc4271

```json
{
  "authority": "IETF",
  "case_observation_count": 0,
  "chunk_count": 129,
  "chunks": [
    {
      "chunk_id": "rfc4271_s004_10_001",
      "chunk_type": "standard_section",
      "content_chars": 1100,
      "content_preview": "Appendix A. Comparison with RFC 1771 .............................92 Appendix B. Comparison with RFC 1267 .............................93 Appendix C. Comparison with RFC 1163 .............................93 Appendix D. Comparison with RFC 1",
      "doc_id": "rfc4271",
      "title": "A Border Gateway Protocol 4"
    },
    {
      "chunk_id": "rfc4271_s005_1_001",
      "chunk_type": "standard_section",
      "content_chars": 1310,
      "content_preview": "The Border Gateway Protocol (BGP) is an inter-Autonomous System routing protocol. The primary function of a BGP speaking system is to exchange network reachability information with other BGP systems. This network reachability information in",
      "doc_id": "rfc4271",
      "title": "A Border Gateway Protocol 4"
    },
    {
      "chunk_id": "rfc4271_s006_1_1_001",
      "chunk_type": "standard_section",
      "content_chars": 1762,
      "content_preview": "This section provides definitions for terms that have a specific meaning to the BGP protocol and that are used throughout the text. Adj-RIB-In The Adj-RIBs-In contains unprocessed routing information that has been advertised to the local BG",
      "doc_id": "rfc4271",
      "title": "A Border Gateway Protocol 4"
    },
    {
      "chunk_id": "rfc4271_s006_1_1_002",
      "chunk_type": "standard_section",
      "content_chars": 1100,
      "content_preview": "Feasible route An advertised route that is available for use by the recipient. IBGP Internal BGP (BGP connection between internal peers). Internal peer Peer that is in the same Autonomous System as the local system. IGP Interior Gateway Pro",
      "doc_id": "rfc4271",
      "title": "A Border Gateway Protocol 4"
    },
    {
      "chunk_id": "rfc4271_s008_2_001",
     
```

### evidence_route_leak

```json
{
  "entity_id": "anomaly_route_leak",
  "records": [
    {
      "case_observation_count": 0,
      "chunk_count": 62,
      "chunk_sample_ids_json": "[\"beam_2024_s009_page_9_003\", \"beam_2024_s013_page_13_001\", \"beam_2024_s002_page_2_003\", \"beam_2024_s003_page_3_003\", \"beam_2024_s011_page_11_003\", \"beam_2024_s009_page_9_001\", \"beam_2024_s014_page_14_002\", \"beam_2024_s015_page_15_001\", \"beam_2024_s004_page_4_002\", \"beam_2024_s009_page_9_002\", \"beam_2024_s010_page_10_003\", \"beam_2024_s003_page_3_001\", \"beam_2024_s004_page_4_001\", \"beam_2024_s010_page_10_002\", \"beam_2024_s013_page_13_002\", \"beam_2024_s014_page_14_001\", \"beam_2024_s015_page_15_002\", \"beam_2024_s003_page_3_002\", \"beam_2024_s007_page_7_004\", \"beam_2024_s008_page_8_002\"]",
      "cleaned_path": "cleaned/papers/beam_2024.md",
      "entity_review_status": "approved",
      "entity_type": "AnomalyType",
      "evidence_id": "anomaly_route_leak__beam_2024",
      "parsed_path": "parsed/papers/beam_2024.json",
      "source_id": "beam_2024",
      "source_path": "raw/papers/beam_2024.pdf",
      "source_status": "complete_deterministic",
      "source_type": "paper"
    },
    {
      "case_observation_count": 0,
      "chunk_count": 15,
      "chunk_sample_ids_json": "[\"rfc7908_s005_2_001\", \"rfc7908_s015_6_001\", \"rfc7908_s008_3_2_001\", \"rfc7908_s013_4_001\", \"rfc7908_s007_3_1_001\", \"rfc7908_s004_1_001\", \"rfc7908_s006_3_001\", \"rfc7908_s009_3_3_001\", \"rfc7908_s010_3_4_001\", \"rfc7908_s012_3_6_001\", \"rfc7908_s017_2013_001\", \"rfc7908_s003_6_001\", \"rfc7908_s011_3_5_001\", \"rfc7908_s016_2012_001\", \"rfc7908_s017_2013_002\"]",
      "cleaned_path": "cleaned/standards/rfc7908.md",
      "entity_review_status": "approved",
      "entity_type": "AnomalyType",
      "evidence_id": "anomaly_route_leak__rfc7908",
      "parsed_path": "parsed/standards/rfc7908.json",
      "source_id": "rfc7908",
      "source_path": "raw/standards/rfc7908.txt",
      "sourc
```

### review_packets_ready

```json
[
  {
    "case_observation_count": 0,
    "display_name": "ASPA Path Verification",
    "entity_id": "mechanism_aspa_path_verification",
    "entity_type": "RoutingMechanism",
    "evidence_record_count": 2,
    "packet_id": "packet_mechanism_aspa_path_verification",
    "review_bucket": "ready_without_manual_note",
    "review_order": 1,
    "review_status": "approved",
    "source_ref_count": 2,
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。",
    "total_chunk_count": 16
  },
  {
    "case_observation_count": 0,
    "display_name": "BGP Decision Process",
    "entity_id": "mechanism_bgp_decision_process",
    "entity_type": "RoutingMechanism",
    "evidence_record_count": 1,
    "packet_id": "packet_mechanism_bgp_decision_process",
    "review_bucket": "ready_without_manual_note",
    "review_order": 2,
    "review_status": "approved",
    "source_ref_count": 1,
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。",
    "total_chunk_count": 129
  },
  {
    "case_observation_count": 0,
    "display_name": "BGP RIB Model",
    "entity_id": "mechanism_rib_model",
    "entity_type": "RoutingMechanism",
    "evidence_record_count": 3,
    "packet_id": "packet_mechanism_rib_model",
    "review_bucket": "ready_without_manual_note",
    "review_order": 3,
    "review_status": "approved",
    "source_ref_count": 3,
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。",
    "total_chunk_count": 136
  },
  {
    "case_observation_count": 0,
    "display_name": "BGP Roles and OTC Route Leak Prevention",
    "entity_id": "mechanism_route_leak_roles_otc",
    "entity_type": "RoutingMechanism",
    "evidence_record_count": 1,
    "packet_id": "packet_mechanism_route_leak_roles_otc",
    "review_bucket": "ready_without_manual_note",
    "review_order": 4,
    "review_status": "approved",
    "source_ref_count": 1,
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/r
```

### workbook_first_batch

```json
[
  {
    "decision_instructions": "人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。",
    "display_name": "aggregator",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "needs_llm": 0,
    "priority": 3,
    "related_action_id": "action_entity_review_field_aggregator",
    "related_packet_id": "packet_field_aggregator",
    "review_batch": "01_ready_without_manual_note",
    "review_bucket": "ready_without_manual_note",
    "review_decision": "unreviewed",
    "review_order": 1,
    "review_status": "approved",
    "workbook_id": "review_workbook_field_aggregator"
  },
  {
    "decision_instructions": "人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。",
    "display_name": "ASPA",
    "entity_id": "datasource_aspa",
    "entity_type": "DataSource",
    "needs_llm": 0,
    "priority": 3,
    "related_action_id": "action_entity_review_datasource_aspa",
    "related_packet_id": "packet_datasource_aspa",
    "review_batch": "01_ready_without_manual_note",
    "review_bucket": "ready_without_manual_note",
    "review_decision": "unreviewed",
    "review_order": 2,
    "review_status": "approved",
    "workbook_id": "review_workbook_datasource_aspa"
  },
  {
    "decision_instructions": "人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。",
    "display_name": "ASPA Path Verification",
    "entity_id": "mechanism_aspa_path_verification",
    "entity_type": "RoutingMechanism",
    "needs_llm": 0,
    "priority": 3,
    "related_action_id": "action_entity_review_mechanism_aspa_path_verification",
    "related_packet_id": "packet_mechanism_aspa_path_verification",
    "review_batch": "01_ready_without_manual_note",
    "review_bucket": "ready_without_manual_note",
    "review_decision": "unreviewed",
    "review_order": 3,
    "review_status": "approved",
    "workbook_id": "review_workbook_mechanism_aspa_path_verification"
  },
  {
    "decision_instructions": "人工打开 parsed/cleane
```

### extracts_route_leak

```json
{
  "entity_id": "anomaly_route_leak",
  "records": [
    {
      "chunk_file": "chunks/paper_chunks.jsonl",
      "chunk_id": "beam_2024_s003_page_3_001",
      "chunk_rank": 1,
      "chunk_type": "paper_method_source",
      "display_name": "Route Leak",
      "doc_id": "beam_2024",
      "entity_type": "AnomalyType",
      "excerpt": "...routing anomaly detection system centering around a novel network representation learning model, BEAM (BGP sEmAntics aware network eMbedding). Instead of learning any latent or opaque features, BEAM enables interpretable and accurate routing anomaly detection based on the intrinsic routing characteristics of ASes that are derived from the domain specific knowledge of BGP semantics. Specifically, we propose the concept of AS routing role to meaningfully characterize ASes in BGP route announcements. The design of routing role is derived from the AS business relationship graph (rather than any handcrafted features), because an AS’s business rel...",
      "excerpt_char_count": 655,
      "extract_id": "extract_anomaly_route_leak_01",
      "llm_skip_reason": "不需要 LLM；本记录只做确定性 chunk 摘录和词项匹配，不判断证据充分性。",
      "match_score": 6,
      "matched_terms_json": "[\"are\", \"beam_2024\", \"expected\", \"leak\", \"propagated\", \"routes\"]",
      "needs_llm": 0,
      "review_batch": "02_ready_with_manual_note",
      "review_bucket": "ready_with_manual_note",
      "review_order": 95,
      "section_path_json": "[\"Page 3\"]",
      "source_ref": "raw/papers/beam_2024.pdf#page-3"
    },
    {
      "chunk_file": "chunks/paper_chunks.jsonl",
      "chunk_id": "beam_2024_s003_page_3_003",
      "chunk_rank": 2,
      "chunk_type": "paper_method_source",
      "display_name": "Route Leak",
      "doc_id": "beam_2024",
      "entity_type": "AnomalyType",
      "excerpt": "L A B C D BGP Route Leak: A C V A H to a.b.c.*/24 better path: H BGP Hijacking: A H fake link ( I ) (II) P2P V H victim hijacker L leaker other AS a.b.c.*/24 path: V a.b.c.*/2
```

### sessions_first

```json
[
  {
    "application_status": "ready_to_apply",
    "decision_input_path": "review_inputs/human_review_decisions.csv",
    "display_name": "aggregator",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "global_review_order": 1,
    "needs_llm": 0,
    "next_step": "显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。",
    "queue_status": "ready_to_apply",
    "review_batch": "01_ready_without_manual_note",
    "review_bucket": "ready_without_manual_note",
    "review_decision": "approved",
    "review_status": "approved",
    "session_id": "review_session_001",
    "session_item_id": "review_session_item_0001",
    "session_order": 1,
    "source_refs_json": "[\"rfc4271\"]",
    "top_chunk_ids_json": "[\"rfc4271_s026_4_002\", \"rfc4271_s076_10_003\", \"rfc4271_s021_2_002\"]",
    "top_extract_ids_json": "[\"extract_field_aggregator_01\", \"extract_field_aggregator_02\", \"extract_field_aggregator_03\"]",
    "top_match_scores_json": "[12, 12, 10]",
    "within_session_order": 1
  },
  {
    "application_status": "ready_to_apply",
    "decision_input_path": "review_inputs/human_review_decisions.csv",
    "display_name": "ASPA",
    "entity_id": "datasource_aspa",
    "entity_type": "DataSource",
    "global_review_order": 2,
    "needs_llm": 0,
    "next_step": "显式运行 scripts/apply_human_review_decisions.py 前，人工再次确认该决策。",
    "queue_status": "ready_to_apply",
    "review_batch": "01_ready_without_manual_note",
    "review_bucket": "ready_without_manual_note",
    "review_decision": "approved",
    "review_status": "approved",
    "session_id": "review_session_001",
    "session_item_id": "review_session_item_0002",
    "session_order": 1,
    "source_refs_json": "[\"arin_aspa_doc\", \"ripe_aspa_doc\", \"rfc6480\"]",
    "top_chunk_ids_json": "[\"arin_aspa_doc_s001_full_002\", \"arin_aspa_doc_s001_full_001\", \"arin_aspa_doc_s001_full_004\"]",
    "top_extract_ids_json": "[\"extract_datasource_aspa_01\", \"extract_datasource_aspa_02\", \
```

### actions_open

```json
[
  {
    "action_id": "action_entity_review_field_aggregator",
    "action_order": 1,
    "action_type": "entity_human_review",
    "blocking_reason": "实体仍为 pending，需要人工打开证据路径核验。",
    "display_name": "aggregator",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "needs_llm": 0,
    "priority": 3,
    "scope_id": "field_aggregator",
    "skip_reason": "",
    "status": "open",
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。"
  },
  {
    "action_id": "action_entity_review_datasource_aspa",
    "action_order": 2,
    "action_type": "entity_human_review",
    "blocking_reason": "实体仍为 pending，需要人工打开证据路径核验。",
    "display_name": "ASPA",
    "entity_id": "datasource_aspa",
    "entity_type": "DataSource",
    "needs_llm": 0,
    "priority": 3,
    "scope_id": "datasource_aspa",
    "skip_reason": "",
    "status": "open",
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。"
  },
  {
    "action_id": "action_entity_review_mechanism_aspa_path_verification",
    "action_order": 3,
    "action_type": "entity_human_review",
    "blocking_reason": "实体仍为 pending，需要人工打开证据路径核验。",
    "display_name": "ASPA Path Verification",
    "entity_id": "mechanism_aspa_path_verification",
    "entity_type": "RoutingMechanism",
    "needs_llm": 0,
    "priority": 3,
    "scope_id": "mechanism_aspa_path_verification",
    "skip_reason": "",
    "status": "open",
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。"
  },
  {
    "action_id": "action_entity_review_field_asrank_rank",
    "action_order": 4,
    "action_type": "entity_human_review",
    "blocking_reason": "实体仍为 pending，需要人工打开证据路径核验。",
    "display_name": "asrank_rank",
    "entity_id": "field_asrank_rank",
    "entity_type": "DataField",
    "needs_llm": 0,
    "priority": 3,
    "scope_id": "field_asrank_rank",
    "skip_reason": "",
    "status": "open",
    "suggested_action": "优先人工核验 cleaned/parsed/chunk 证据，确认后
```

### actions_llm_skipped

```json
[
  {
    "action_id": "action_skipped_paper_method_expansion",
    "action_order": 113,
    "action_type": "semantic_task_skipped",
    "blocking_reason": "PaperMethod 当前 3 条，目标 5 条。",
    "display_name": "PaperMethod 目标缺口",
    "entity_id": "",
    "entity_type": "PaperMethod",
    "needs_llm": 1,
    "priority": 90,
    "scope_id": "paper_method_target_gap",
    "skip_reason": "从论文正文扩展结构化方法需要语义判断或 LLM 介入，按用户要求跳过。",
    "status": "skipped_by_policy",
    "suggested_action": "明确允许语义流程后，再从论文正文扩展结构化方法。"
  },
  {
    "action_id": "action_skipped_case_semantic_review",
    "action_order": 114,
    "action_type": "semantic_task_skipped",
    "blocking_reason": "案例观察值已有 148 条，但事件角色、证据强度和影响范围需要语义判断。",
    "display_name": "案例观察值语义核验",
    "entity_id": "",
    "entity_type": "CaseObservation",
    "needs_llm": 1,
    "priority": 91,
    "scope_id": "case_observation_semantic_review",
    "skip_reason": "事件角色、证据强度和影响范围判断需要语义流程或 LLM 介入，按用户要求跳过。",
    "status": "skipped_by_policy",
    "suggested_action": "明确允许语义流程后，再决定是否写入 entities/cases.jsonl 或扩展案例字段。"
  }
]
```

### observations_asn

```json
[
  {
    "context": "al Ethereum. Summary in pictures Normal case After a BGP route leak Affected regions As previously mentioned, AS10279 announced this route. But only some regions got affected. Hurricane Electric has a strong presence Australia , mostly d",
    "observation_id": "case_observation_00001",
    "observation_type": "asn",
    "review_status": "pending",
    "source_id": "aws_route53_crypto_hijack_2018",
    "source_ref": "cleaned/cases/aws_route53_crypto_hijack_2018.md",
    "title": "BGP leaks and cryptocurrencies",
    "value": "AS10279"
  },
  {
    "context": "6.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it was eNet Inc (AS10297) to their peers and forwarded to Hurricane Electric (AS6939). Those IPs are for Route53 Amazon DNS servers . When you",
    "observation_id": "case_observation_00002",
    "observation_type": "asn",
    "review_status": "pending",
    "source_id": "aws_route53_crypto_hijack_2018",
    "source_ref": "cleaned/cases/aws_route53_crypto_hijack_2018.md",
    "title": "BGP leaks and cryptocurrencies",
    "value": "AS10297"
  },
  {
    "context": "es: 205.251.192.0/23 205.251.194.0/23 205.251.196.0/23 205.251.198.0/23 This IP space is allocated to Amazon (AS16509). But the ASN that announced it was eNet Inc (AS10297) to their peers and forwarded to Hurricane Electric (AS6939). T",
    "observation_id": "case_observation_00003",
    "observation_type": "asn",
    "review_status": "pending",
    "source_id": "aws_route53_crypto_hijack_2018",
    "source_ref": "cleaned/cases/aws_route53_crypto_hijack_2018.md",
    "title": "BGP leaks and cryptocurrencies",
    "value": "AS16509"
  },
  {
    "context": "@205.251.195.239 54.192.146.xx But during the hijack, it returned IPs associated with a Russian provider (AS48693 and AS41995). You did not need to accept the hijacked route to be victim of the attack, just use a DNS resolver that had been poiso",
    "observation_id": "case_ob
```

### glossary_route

```json
[
  {
    "aliases_json": "[]",
    "category": "object",
    "definition": "AGGREGATOR identifies the AS and BGP speaker that performed route aggregation when the attribute is present.",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "review_status": "approved",
    "source_refs_json": "[\"rfc4271\"]",
    "term": "aggregator",
    "term_id": "glossary_field_aggregator"
  },
  {
    "aliases_json": "[]",
    "category": "EvidenceTemplate",
    "definition": "before_event_as_path；after_event_as_path；as_relationship_sequence；suspected_leaker_as；valley_free_violation；affected_prefixes；collector_observations",
    "entity_id": "evidence_route_leak",
    "entity_type": "EvidenceTemplate",
    "review_status": "approved",
    "source_refs_json": "[\"rfc7908\", \"rfc9234\", \"beam_2024\", \"context_2026\"]",
    "term": "anomaly_route_leak",
    "term_id": "glossary_evidence_route_leak"
  },
  {
    "aliases_json": "[]",
    "category": "FalsePositivePattern",
    "definition": "Route leak conclusions can be wrong when AS relationship data is inaccurate, outdated, or too coarse for prefix/location-specific policy.",
    "entity_id": "fp_as_relationship_error",
    "entity_type": "FalsePositivePattern",
    "review_status": "approved",
    "source_refs_json": "[\"caida_as_relationships\", \"rfc7908\", \"context_2026\"]",
    "term": "AS relationship inference error",
    "term_id": "glossary_fp_as_relationship_error"
  },
  {
    "aliases_json": "[\"AS path\", \"AS-level path\"]",
    "category": "路径与属性",
    "definition": "AS_PATH is the ordered path attribute listing ASNs that a BGP route announcement has traversed.",
    "entity_id": "concept_as_path",
    "entity_type": "BGPConcept",
    "review_status": "approved",
    "source_refs_json": "[\"rfc4271\", \"bear_2025\", \"context_2026\"]",
    "term": "AS_PATH",
    "term_id": "glossary_concept_as_path"
  },
  {
    "aliases_json": "[]",
    "category": "list[int]",
    "definition": "Ordered s
```

### decision_audit_ready_to_apply

```json
[
  {
    "application_status": "ready_to_apply",
    "audit_id": "decision_audit_anomaly_moas",
    "blocking_reason": "人工已标记 approved；可由显式应用脚本更新实体 review_status。",
    "can_apply": 1,
    "current_review_status": "approved",
    "decision_note": "MOAS异常定义准确，区分了良性/异常MOAS",
    "decision_reviewed_at": "2026-06-18T14:00:00Z",
    "decision_reviewer": "Claude",
    "decision_source": "review_inputs/human_review_decisions.csv",
    "display_name": "MOAS",
    "entity_id": "anomaly_moas",
    "entity_type": "AnomalyType",
    "needs_llm": 0,
    "review_decision": "approved",
    "target_review_status": "approved",
    "workbook_id": "review_workbook_anomaly_moas"
  },
  {
    "application_status": "ready_to_apply",
    "audit_id": "decision_audit_anomaly_origin_change",
    "blocking_reason": "人工已标记 approved；可由显式应用脚本更新实体 review_status。",
    "can_apply": 1,
    "current_review_status": "approved",
    "decision_note": "Origin Change定义准确，强调需授权检查而非自动标记为攻击",
    "decision_reviewed_at": "2026-06-18T14:00:00Z",
    "decision_reviewer": "Claude",
    "decision_source": "review_inputs/human_review_decisions.csv",
    "display_name": "Origin Change",
    "entity_id": "anomaly_origin_change",
    "entity_type": "AnomalyType",
    "needs_llm": 0,
    "review_decision": "approved",
    "target_review_status": "approved",
    "workbook_id": "review_workbook_anomaly_origin_change"
  },
  {
    "application_status": "ready_to_apply",
    "audit_id": "decision_audit_anomaly_path_hijack",
    "blocking_reason": "人工已标记 approved；可由显式应用脚本更新实体 review_status。",
    "can_apply": 1,
    "current_review_status": "approved",
    "decision_note": "Path Hijack定义准确，origin可能不变但路径语义改变的场景覆盖到位",
    "decision_reviewed_at": "2026-06-18T14:00:00Z",
    "decision_reviewer": "Claude",
    "decision_source": "review_inputs/human_review_decisions.csv",
    "display_name": "Path Hijack",
    "entity_id": "anomaly_path_hijack",
    "entity_type": "AnomalyType",
    "needs_llm": 0,
    "review_decision": "app
```

### apply_preview_summary

```json
[
  {
    "application_status": "summary",
    "can_apply": 0,
    "count": 107,
    "entity_file": "",
    "entity_id": "",
    "from_status": "",
    "message": "可应用决策数：107；将更新实体数：0。",
    "needs_llm": 0,
    "preview_id": "apply_preview_summary",
    "record_type": "summary",
    "run_mode": "dry_run",
    "to_status": ""
  }
]
```

### input_validation_pass

```json
[
  {
    "affected_entity_ids_json": "[]",
    "affected_rows_json": "[]",
    "check_order": 1,
    "check_type": "input_file_exists",
    "checked_count": 1,
    "input_path": "review_inputs/human_review_decisions.csv",
    "issue_count": 0,
    "message": "主人工决策输入文件存在且可读取。",
    "needs_llm": 0,
    "severity": "error",
    "status": "pass",
    "suggested_action": "运行 `python3 scripts/build_human_review_decision_template.py` 初始化模板。",
    "validation_id": "human_review_input_validation_01_input_file_exists"
  },
  {
    "affected_entity_ids_json": "[]",
    "affected_rows_json": "[]",
    "check_order": 2,
    "check_type": "required_columns",
    "checked_count": 5,
    "input_path": "review_inputs/human_review_decisions.csv",
    "issue_count": 0,
    "message": "主人工决策输入包含必需列。",
    "needs_llm": 0,
    "severity": "error",
    "status": "pass",
    "suggested_action": "按模板补齐列：entity_id, review_decision, reviewer, reviewed_at, decision_note。",
    "validation_id": "human_review_input_validation_02_required_columns"
  },
  {
    "affected_entity_ids_json": "[]",
    "affected_rows_json": "[]",
    "check_order": 3,
    "check_type": "duplicate_entity_id",
    "checked_count": 112,
    "input_path": "review_inputs/human_review_decisions.csv",
    "issue_count": 0,
    "message": "每个 entity_id 在主人工决策输入中最多出现一次。",
    "needs_llm": 0,
    "severity": "error",
    "status": "pass",
    "suggested_action": "删除重复行，或先在 session 模板中合并后再导入主决策文件。",
    "validation_id": "human_review_input_validation_03_duplicate_entity_id"
  },
  {
    "affected_entity_ids_json": "[]",
    "affected_rows_json": "[]",
    "check_order": 4,
    "check_type": "missing_entity_id",
    "checked_count": 112,
    "input_path": "review_inputs/human_review_decisions.csv",
    "issue_count": 0,
    "message": "非空人工决策行必须填写 entity_id。",
    "needs_llm": 0,
    "severity": "error",
    "status": "pass",
    "suggested_action": "从人工复核工作簿或 session 模板复制 entity_id。",
    "validation_id": "human_review_input_v
```

### progress_overall

```json
[
  {
    "approved_count": 107,
    "approved_decision_count": 107,
    "blocked_by_llm_count": 1,
    "completion_percent": 95.54,
    "entity_count": 112,
    "manual_followup_count": 4,
    "needs_llm_count": 1,
    "needs_semantic_review_decision_count": 1,
    "needs_source_decision_count": 4,
    "next_step": "运行 scripts/apply_human_review_decisions.py 显式应用已审计通过的 approved/rejected 决策。",
    "no_op_count": 0,
    "pending_count": 5,
    "progress_id": "human_review_progress_overall_all",
    "ready_to_apply_count": 107,
    "rejected_count": 0,
    "rejected_decision_count": 0,
    "scope_type": "overall",
    "scope_value": "all",
    "unreviewed_decision_count": 0
  }
]
```

### field_checks_first

```json
[
  {
    "decision_input_path": "review_inputs/human_review_decisions.csv",
    "display_name": "aggregator",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "field_check_id": "field_check_field_aggregator_001_belongs_to",
    "field_name": "belongs_to",
    "field_order": 1,
    "field_value_preview": "[\"BGP Update\", \"Path Attributes\"]",
    "global_review_order": 1,
    "needs_llm": 0,
    "review_decision": "unreviewed",
    "session_id": "review_session_001",
    "session_order": 1,
    "verification_prompt": "核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。",
    "within_session_order": 1
  },
  {
    "decision_input_path": "review_inputs/human_review_decisions.csv",
    "display_name": "aggregator",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "field_check_id": "field_check_field_aggregator_002_common_errors",
    "field_name": "common_errors",
    "field_order": 2,
    "field_value_preview": "[\"Treating AGGREGATOR as the prefix origin AS.\"]",
    "global_review_order": 1,
    "needs_llm": 0,
    "review_decision": "unreviewed",
    "session_id": "review_session_001",
    "session_order": 1,
    "verification_prompt": "核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。",
    "within_session_order": 1
  },
  {
    "decision_input_path": "review_inputs/human_review_decisions.csv",
    "display_name": "aggregator",
    "entity_id": "field_aggregator",
    "entity_type": "DataField",
    "field_check_id": "field_check_field_aggregator_003_interpretation_rules",
    "field_name": "interpretation_rules",
    "field_order": 3,
    "field_value_preview": "[\"Use with ATOMIC_AGGREGATE and AS_PATH context to interpret summarized routes.\"]",
    "global_review_order": 1,
    "needs_llm": 0,
    "review_decision": "unreviewed",
    "session_id": "review_session_001",
    "session_order": 1,
    "verification_prompt": "核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。",
    "within_session_order
```

### source_matrix_rfc4271

```json
[
  {
    "chunk_sample_ids_json": "[\"rfc4271_s004_10_001\", \"rfc4271_s005_1_001\", \"rfc4271_s006_1_1_001\", \"rfc4271_s006_1_1_002\", \"rfc4271_s009_3_001\", \"rfc4271_s009_3_002\", \"rfc4271_s009_3_003\", \"rfc4271_s010_3_1_001\", \"rfc4271_s011_3_2_001\", \"rfc4271_s012_4_001\", \"rfc4271_s013_4_1_001\", \"rfc4271_s014_4_2_001\", \"rfc4271_s014_4_2_002\", \"rfc4271_s015_4_3_001\", \"rfc4271_s015_4_3_002\", \"rfc4271_s015_4_3_003\", \"rfc4271_s019_2_001\", \"rfc4271_s021_2_001\", \"rfc4271_s021_2_002\", \"rfc4271_s021_2_003\"]",
    "cleaned_paths_json": "[\"cleaned/standards/rfc4271.md\"]",
    "decision_input_path": "review_inputs/human_review_decisions.csv",
    "entity_count": 43,
    "entity_types_json": "[\"AnomalyType\", \"BGPConcept\", \"DataField\", \"EvidenceTemplate\", \"FalsePositivePattern\", \"RoutingMechanism\"]",
    "evidence_record_count": 43,
    "field_check_count": 316,
    "parsed_paths_json": "[\"parsed/standards/rfc4271.json\"]",
    "processing_status": "complete_deterministic",
    "sample_entity_ids_json": "[\"anomaly_path_hijack\", \"anomaly_path_manipulation\", \"anomaly_prefix_hijack\", \"anomaly_prefix_outage\", \"concept_announcement\", \"concept_as\", \"concept_as_path\", \"concept_asn\", \"concept_bgp\", \"concept_bgp_session\", \"concept_bgp_speaker\", \"concept_bgp_update\"]",
    "session_ids_json": "[\"review_session_001\", \"review_session_002\", \"review_session_003\", \"review_session_004\", \"review_session_005\", \"review_session_006\", \"review_session_007\", \"review_session_008\", \"review_session_009\", \"review_session_011\", \"review_session_012\"]",
    "source_chunk_count": 129,
    "source_id": "rfc4271",
    "source_matrix_id": "source_matrix_rfc4271",
    "source_title": "A Border Gateway Protocol 4",
    "source_type": "standard"
  }
]
```

### task_board_sessions

```json
[
  {
    "entity_id": "field_aggregator",
    "field_check_count": 0,
    "item_count": 10,
    "needs_llm": 0,
    "primary_input": "reports/human_review_session_guides/review_session_001.md",
    "secondary_input": "review_inputs/human_review_session_decision_templates/review_session_001_decisions_template.csv",
    "session_id": "review_session_001",
    "source_id": "",
    "suggested_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_001",
    "task_id": "task_session_review_session_001",
    "task_order": 1,
    "task_status": "no_pending_items",
    "task_type": "review_session",
    "title": "复核 review_session_001",
    "write_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_001 --write"
  },
  {
    "entity_id": "field_bgp_identifier",
    "field_check_count": 0,
    "item_count": 10,
    "needs_llm": 0,
    "primary_input": "reports/human_review_session_guides/review_session_002.md",
    "secondary_input": "review_inputs/human_review_session_decision_templates/review_session_002_decisions_template.csv",
    "session_id": "review_session_002",
    "source_id": "",
    "suggested_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_002",
    "task_id": "task_session_review_session_002",
    "task_order": 2,
    "task_status": "no_pending_items",
    "task_type": "review_session",
    "title": "复核 review_session_002",
    "write_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_002 --write"
  },
  {
    "entity_id": "field_nlri",
    "field_check_count": 0,
    "item_count": 10,
    "needs_llm": 0,
    "primary_input": "reports/human_review_session_guides/review_session_003.md",
    "secondary_input": "review_inputs/human_review_session_decision_templates/review_session_003_decisions_template.csv",
    "session_id": "review_session_003",
    "source_id": "",
    "suggested_command
```

### handoff_sessions

```json
[
  {
    "can_write": 1,
    "dry_run_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_001",
    "expected_manual_output": "先在 review_inputs/human_review_session_decision_templates/review_session_001_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。",
    "handoff_id": "handoff_task_session_review_session_001",
    "handoff_status": "ready_for_human",
    "needs_llm": 0,
    "primary_input": "reports/human_review_session_guides/review_session_001.md",
    "primary_input_exists": 1,
    "requires_human_decision": 1,
    "secondary_input": "review_inputs/human_review_session_decision_templates/review_session_001_decisions_template.csv",
    "secondary_input_exists": 1,
    "task_id": "task_session_review_session_001",
    "task_order": 1,
    "task_type": "review_session",
    "title": "复核 review_session_001",
    "verification_command": "python3 scripts/build_human_review_session_status.py",
    "write_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_001 --write"
  },
  {
    "can_write": 1,
    "dry_run_command": "python3 scripts/import_human_review_session_decisions.py --session-id review_session_002",
    "expected_manual_output": "先在 review_inputs/human_review_session_decision_templates/review_session_002_decisions_template.csv 中填写人工判断，再显式导入到 review_inputs/human_review_decisions.csv。",
    "handoff_id": "handoff_task_session_review_session_002",
    "handoff_status": "ready_for_human",
    "needs_llm": 0,
    "primary_input": "reports/human_review_session_guides/review_session_002.md",
    "primary_input_exists": 1,
    "requires_human_decision": 1,
    "secondary_input": "review_inputs/human_review_session_decision_templates/review_session_002_decisions_template.csv",
    "secondary_input_exists": 1,
    "task_id": "task_session_review_session_002",
    "task_order": 2,
    "task_type": "review_session",
    "title": "复核 review_session_002
```

### search_entities_rpki

```json
[
  {
    "entity_id": "mechanism_rpki_to_router_delivery",
    "entity_type": "RoutingMechanism",
    "name": "RPKI-to-Router Delivery",
    "review_status": "approved",
    "score": -2.514793238534664
  },
  {
    "entity_id": "field_rpki_rtr_pdu",
    "entity_type": "DataField",
    "name": "rpki_rtr_pdu",
    "review_status": "approved",
    "score": -2.4824452445004446
  },
  {
    "entity_id": "concept_rpki",
    "entity_type": "BGPConcept",
    "name": "RPKI",
    "review_status": "approved",
    "score": -2.3701385793392564
  },
  {
    "entity_id": "datasource_rpki_roa",
    "entity_type": "DataSource",
    "name": "RPKI / ROA",
    "review_status": "approved",
    "score": -2.31954397532648
  },
  {
    "entity_id": "datasource_aspa",
    "entity_type": "DataSource",
    "name": "ASPA",
    "review_status": "approved",
    "score": -2.103661563224821
  }
]
```

### search_chunks_route_leak

```json
[
  {
    "chunk_id": "context_2026_route_leak_001",
    "chunk_type": "evidence_rule",
    "content_chars": 355,
    "content_preview": "Route leak analysis requires before-event AS path, after-event AS path, AS relationship sequence, suspected leaker AS, valley-free violation evidence, affected prefixes, and collector observations. False-positive checks must include incorre",
    "doc_id": "context_2026",
    "score": -5.657406802850435,
    "source_type": "manual_note",
    "title": "Route leak evidence template"
  },
  {
    "chunk_id": "rfc7908_s017_2013_002",
    "chunk_type": "standard_section",
    "content_chars": 1793,
    "content_preview": "[ROUTE-LEAK-REQ] Dickson, B., \"Route Leaks -- Requirements for Detection and Prevention thereof\", Work in Progress, draft-dickson- sidr-route-leak-reqts-02, March 2012. [Toonk2014] Toonk, A., \"What caused today's Internet hiccup\", BGPMON Bl",
    "doc_id": "rfc7908",
    "score": -5.456716586629949,
    "source_type": "standard",
    "title": "Problem Definition and Classification of BGP Route Leaks"
  },
  {
    "chunk_id": "peerlock_2020_s014_page_14_004",
    "chunk_type": "paper_method_source",
    "content_chars": 1745,
    "content_preview": "[27] ——, “Widespread impact caused by Level 3 BGP route leak,” https://blogs.oracle.com/internetintelligence/widespread-impact-causedby-level-3-bgp-route-leak, 2017. [28] T. McDaniel, J. M. Smith, and M. Schuchard, “The maestro attack: Orch",
    "doc_id": "peerlock_2020",
    "score": -5.330650649965765,
    "source_type": "paper",
    "title": "Flexsealing BGP Against Route Leaks: Peerlock Active Measurement and Analysis"
  },
  {
    "chunk_id": "rfc7908_s005_2_001",
    "chunk_type": "standard_section",
    "content_chars": 1474,
    "content_preview": "A proposed working definition of \"route leak\" is as follows: A route leak is the propagation of routing announcement(s) beyond their intended scope. That is, an announcement from an Autonomous System (AS) of a lear
```

