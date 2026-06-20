# 01_ready_without_manual_note 复核清单

## 说明

本文件只展开人工复核入口。表内路径和 chunk ID 均来自现有流水线数据，未经过语义扩展。

## 1. aggregator

- 实体 ID：`field_aggregator`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s021_2_001`
  - `rfc4271_s021_2_002`
  - `rfc4271_s026_4_002`
  - `rfc4271_s076_10_003`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s012_4_001`
  - `rfc4271_s013_4_1_001`
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s014_4_2_002`
  - `rfc4271_s015_4_3_001`
  - `rfc4271_s015_4_3_002`

## 2. ASPA

- 实体 ID：`datasource_aspa`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `arin_aspa_doc`
  - `ripe_aspa_doc`
  - `rfc6480`
- cleaned 路径：
  - `cleaned/data_docs/arin_aspa_doc.md`
  - `cleaned/data_docs/ripe_aspa_doc.md`
  - `cleaned/standards/rfc6480.md`
- parsed 路径：
  - `parsed/data_docs/arin_aspa_doc.json`
  - `parsed/data_docs/ripe_aspa_doc.json`
  - `parsed/standards/rfc6480.json`
- chunk 样例：
  - `arin_aspa_doc_s001_full_001`
  - `arin_aspa_doc_s001_full_002`
  - `arin_aspa_doc_s001_full_003`
  - `arin_aspa_doc_s001_full_004`
  - `arin_aspa_doc_s001_full_005`
  - `rfc6480_s002_1_001`
  - `rfc6480_s002_1_002`
  - `rfc6480_s002_1_003`
  - `rfc6480_s003_1_1_001`
  - `rfc6480_s004_2_001`
  - `rfc6480_s004_2_002`
  - `rfc6480_s005_2_1_001`

## 3. ASPA Path Verification

- 实体 ID：`mechanism_aspa_path_verification`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `arin_aspa_doc`
  - `ripe_aspa_doc`
- cleaned 路径：
  - `cleaned/data_docs/arin_aspa_doc.md`
  - `cleaned/data_docs/ripe_aspa_doc.md`
- parsed 路径：
  - `parsed/data_docs/arin_aspa_doc.json`
  - `parsed/data_docs/ripe_aspa_doc.json`
- chunk 样例：
  - `arin_aspa_doc_s001_full_001`
  - `arin_aspa_doc_s001_full_004`
  - `arin_aspa_doc_s001_full_002`
  - `arin_aspa_doc_s001_full_003`
  - `arin_aspa_doc_s001_full_005`
  - `ripe_aspa_doc_s001_full_007`
  - `ripe_aspa_doc_s001_full_008`
  - `ripe_aspa_doc_s001_full_010`
  - `ripe_aspa_doc_s001_full_009`
  - `ripe_aspa_doc_s001_full_001`
  - `ripe_aspa_doc_s001_full_006`
  - `ripe_aspa_doc_s001_full_002`

## 4. asrank_rank

- 实体 ID：`field_asrank_rank`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `caida_asrank_api`
- cleaned 路径：
  - `cleaned/data_docs/caida_asrank_api.md`
- parsed 路径：
  - `parsed/data_docs/caida_asrank_api.json`
- chunk 样例：
  - `caida_asrank_api_s001_full_002`
  - `caida_asrank_api_s001_full_001`
  - `caida_asrank_api_s001_full_005`
  - `caida_asrank_api_s001_full_006`
  - `caida_asrank_api_s001_full_003`
  - `caida_asrank_api_s001_full_004`
  - `caida_asrank_api_s001_full_007`

## 5. asrank_relationship

- 实体 ID：`field_asrank_relationship`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `caida_asrank_api`
  - `caida_as_relationships`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/data_docs/caida_asrank_api.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/data_docs/caida_asrank_api.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_011`
  - `caida_as_relationships_s001_full_013`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_009`
  - `caida_as_relationships_s001_full_010`
  - `caida_as_relationships_s001_full_012`

## 6. atomic_aggregate

- 实体 ID：`field_atomic_aggregate`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s021_2_001`
  - `rfc4271_s026_4_002`
  - `rfc4271_s076_10_003`
  - `rfc4271_s033_5_1_6_001`
  - `rfc4271_s066_9_1_4_002`
  - `rfc4271_s073_9_2_2_2_003`
  - `rfc4271_s076_10_002`
  - `rfc4271_s081_6_008`
  - `rfc4271_s021_2_002`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s012_4_001`

## 7. BGP Decision Process

- 实体 ID：`mechanism_bgp_decision_process`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s060_9_1_001`
  - `rfc4271_s031_5_1_4_001`
  - `rfc4271_s021_2_001`
  - `rfc4271_s062_9_1_2_001`
  - `rfc4271_s073_9_2_2_2_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s061_9_1_1_001`
  - `rfc4271_s063_9_1_2_1_001`
  - `rfc4271_s064_9_1_2_2_003`
  - `rfc4271_s065_9_1_3_001`
  - `rfc4271_s066_9_1_4_001`

## 8. BGP RIB Model

- 实体 ID：`mechanism_rib_model`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
  - `ripe_ris_raw_data`
  - `routeviews_archive_index`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_raw_data.md`
  - `cleaned/data_docs/routeviews_archive_index.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_raw_data.json`
  - `parsed/data_docs/routeviews_archive_index.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s009_3_003`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s048_8_1_2_001`
  - `rfc4271_s058_8_2_2_010`
  - `rfc4271_s081_6_003`
  - `rfc4271_s081_6_006`
  - `rfc4271_s026_4_002`
  - `rfc4271_s031_5_1_4_001`
  - `rfc4271_s073_9_2_2_2_002`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s006_1_1_002`

## 9. BGP Roles and OTC Route Leak Prevention

- 实体 ID：`mechanism_route_leak_roles_otc`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc9234`
- cleaned 路径：
  - `cleaned/standards/rfc9234.md`
- parsed 路径：
  - `parsed/standards/rfc9234.json`
- chunk 样例：
  - `rfc9234_s018_8_001`
  - `rfc9234_s016_6_001`
  - `rfc9234_s008_4_2_002`
  - `rfc9234_s014_2_001`
  - `rfc9234_s015_4_001`
  - `rfc9234_s002_1_001`
  - `rfc9234_s005_3_1_001`
  - `rfc9234_s005_3_1_002`
  - `rfc9234_s006_4_001`
  - `rfc9234_s008_4_2_001`
  - `rfc9234_s009_5_001`
  - `rfc9234_s002_1_002`

## 10. BGP Update and Withdrawal Propagation

- 实体 ID：`mechanism_update_withdrawal`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
  - `ripe_ris_raw_data`
  - `bgpstream_docs`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
  - `cleaned/data_docs/ripe_ris_raw_data.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
  - `parsed/data_docs/ripe_ris_raw_data.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s059_9_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s009_3_003`
  - `rfc4271_s026_4_002`
  - `rfc4271_s069_9_2_1_1_001`
  - `rfc4271_s031_5_1_4_001`
  - `rfc4271_s022_4_4_001`
  - `rfc4271_s048_8_1_2_001`
  - `rfc4271_s058_8_2_2_010`

## 11. bgp_identifier

- 实体 ID：`field_bgp_identifier`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s014_4_2_002`
  - `rfc4271_s021_2_002`
  - `rfc4271_s024_6_001`
  - `rfc4271_s037_6_2_001`
  - `rfc4271_s081_6_009`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s034_5_1_7_001`
  - `rfc4271_s043_6_8_001`
  - `rfc4271_s043_6_8_002`
  - `rfc4271_s052_8_2_1_001`
  - `rfc4271_s076_10_002`

## 12. bgp_role

- 实体 ID：`field_bgp_role`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc9234`
- cleaned 路径：
  - `cleaned/standards/rfc9234.md`
- parsed 路径：
  - `parsed/standards/rfc9234.json`
- chunk 样例：
  - `rfc9234_s002_1_001`
  - `rfc9234_s005_3_1_001`
  - `rfc9234_s006_4_001`
  - `rfc9234_s007_4_1_001`
  - `rfc9234_s008_4_2_001`
  - `rfc9234_s008_4_2_002`
  - `rfc9234_s015_4_001`
  - `rfc9234_s016_6_001`
  - `rfc9234_s017_7_001`
  - `rfc9234_s018_8_001`
  - `rfc9234_s002_1_002`
  - `rfc9234_s003_2_001`

## 13. BGPsec Path Validation

- 实体 ID：`mechanism_bgpsec_path_validation`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc8205`
  - `rfc6480`
- cleaned 路径：
  - `cleaned/standards/rfc6480.md`
  - `cleaned/standards/rfc8205.md`
- parsed 路径：
  - `parsed/standards/rfc6480.json`
  - `parsed/standards/rfc8205.json`
- chunk 样例：
  - `rfc6480_s007_2_3_001`
  - `rfc6480_s012_4_001`
  - `rfc6480_s002_1_003`
  - `rfc6480_s005_2_1_002`
  - `rfc6480_s008_2_4_001`
  - `rfc6480_s010_3_1_001`
  - `rfc6480_s015_4_3_001`
  - `rfc6480_s016_4_4_001`
  - `rfc6480_s035_8_001`
  - `rfc6480_s039_11_2_001`
  - `rfc6480_s026_7_2_001`
  - `rfc6480_s002_1_001`

## 14. CAIDA ASRank

- 实体 ID：`datasource_caida_asrank`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `caida_asrank_api`
  - `caida_as_relationships`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/data_docs/caida_asrank_api.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/data_docs/caida_asrank_api.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_011`
  - `caida_as_relationships_s001_full_013`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_015`
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_008`

## 15. customer_cone_asns

- 实体 ID：`field_customer_cone_asns`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `caida_asrank_api`
  - `caida_as_relationships`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/data_docs/caida_asrank_api.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/data_docs/caida_asrank_api.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_008`
  - `caida_as_relationships_s001_full_009`
  - `caida_as_relationships_s001_full_010`
  - `caida_as_relationships_s001_full_011`
  - `caida_as_relationships_s001_full_013`
  - `caida_as_relationships_s001_full_014`
  - `caida_as_relationships_s001_full_015`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_001`

## 16. hold_time

- 实体 ID：`field_hold_time`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s024_6_001`
  - `rfc4271_s037_6_2_001`
  - `rfc4271_s040_6_5_001`
  - `rfc4271_s058_8_2_2_009`
  - `rfc4271_s058_8_2_2_010`
  - `rfc4271_s076_10_004`
  - `rfc4271_s081_6_009`
  - `rfc4271_s022_4_4_001`
  - `rfc4271_s058_8_2_2_004`
  - `rfc4271_s058_8_2_2_006`
  - `rfc4271_s058_8_2_2_007`

## 17. local_pref

- 实体 ID：`field_local_pref`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s021_2_001`
  - `rfc4271_s026_4_002`
  - `rfc4271_s076_10_003`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s032_5_1_5_001`
  - `rfc4271_s038_6_3_003`
  - `rfc4271_s059_9_001`
  - `rfc4271_s061_9_1_1_001`
  - `rfc4271_s081_6_001`
  - `rfc4271_s081_6_008`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s014_4_2_002`

## 18. med

- 实体 ID：`field_med`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s021_2_002`
  - `rfc4271_s023_4_5_001`
  - `rfc4271_s024_6_001`
  - `rfc4271_s038_6_3_001`
  - `rfc4271_s038_6_3_002`
  - `rfc4271_s038_6_3_003`
  - `rfc4271_s058_8_2_2_009`
  - `rfc4271_s076_10_003`
  - `rfc4271_s081_6_009`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s008_2_001`
  - `rfc4271_s009_3_003`

## 19. mrt_file_type

- 实体 ID：`field_mrt_file_type`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `ripe_ris_raw_data`
  - `routeviews_archive_index`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_raw_data.md`
  - `cleaned/data_docs/routeviews_archive_index.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_raw_data.json`
  - `parsed/data_docs/routeviews_archive_index.json`
- chunk 样例：
  - `ripe_ris_raw_data_s001_full_001`
  - `ripe_ris_raw_data_s001_full_002`
  - `routeviews_archive_index_s001_full_001`
  - `routeviews_archive_index_s001_full_004`
  - `routeviews_archive_index_s001_full_002`
  - `routeviews_archive_index_s001_full_003`
  - `routeviews_archive_index_s001_full_005`

## 20. next_hop

- 实体 ID：`field_next_hop`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s021_2_001`
  - `rfc4271_s024_6_001`
  - `rfc4271_s026_4_002`
  - `rfc4271_s038_6_3_002`
  - `rfc4271_s076_10_003`
  - `rfc4271_s076_10_004`
  - `rfc4271_s081_6_009`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s011_3_2_002`
  - `rfc4271_s030_5_1_3_001`
  - `rfc4271_s030_5_1_3_002`
  - `rfc4271_s030_5_1_3_003`

## 21. nlri

- 实体 ID：`field_nlri`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s021_2_003`
  - `rfc4271_s026_4_002`
  - `rfc4271_s038_6_3_003`
  - `rfc4271_s059_9_001`
  - `rfc4271_s012_4_001`
  - `rfc4271_s013_4_1_001`
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s014_4_2_002`
  - `rfc4271_s015_4_3_001`
  - `rfc4271_s015_4_3_002`

## 22. origin_attribute

- 实体 ID：`field_origin_attribute`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s024_6_001`
  - `rfc4271_s038_6_3_001`
  - `rfc4271_s081_6_009`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s015_4_3_001`
  - `rfc4271_s015_4_3_002`
  - `rfc4271_s015_4_3_003`
  - `rfc4271_s019_2_001`
  - `rfc4271_s021_2_001`
  - `rfc4271_s021_2_002`
  - `rfc4271_s021_2_003`

## 23. otc_attribute

- 实体 ID：`field_otc_attribute`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc9234`
- cleaned 路径：
  - `cleaned/standards/rfc9234.md`
- parsed 路径：
  - `parsed/standards/rfc9234.json`
- chunk 样例：
  - `rfc9234_s005_3_1_002`
  - `rfc9234_s009_5_001`
  - `rfc9234_s014_2_001`
  - `rfc9234_s015_4_001`
  - `rfc9234_s016_6_001`
  - `rfc9234_s018_8_001`
  - `rfc9234_s018_8_002`
  - `rfc9234_s002_1_002`
  - `rfc9234_s008_4_2_002`
  - `rfc9234_s021_9_2_001`
  - `rfc9234_s002_1_001`
  - `rfc9234_s003_2_001`

## 24. path_attributes

- 实体 ID：`field_path_attributes`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s015_4_3_001`
  - `rfc4271_s015_4_3_002`
  - `rfc4271_s021_2_002`
  - `rfc4271_s021_2_003`
  - `rfc4271_s026_4_002`
  - `rfc4271_s038_6_3_003`
  - `rfc4271_s081_6_001`
  - `rfc4271_s015_4_3_003`
  - `rfc4271_s038_6_3_001`
  - `rfc4271_s047_8_1_1_004`

## 25. PeeringDB

- 实体 ID：`datasource_peeringdb`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `peeringdb_api_docs`
- cleaned 路径：
  - `cleaned/data_docs/peeringdb_api_docs.md`
- parsed 路径：
  - `parsed/data_docs/peeringdb_api_docs.json`
- chunk 样例：
  - `peeringdb_api_docs_s002_paths_004`
  - `peeringdb_api_docs_s002_paths_011`
  - `peeringdb_api_docs_s002_paths_012`
  - `peeringdb_api_docs_s002_paths_018`
  - `peeringdb_api_docs_s002_paths_033`
  - `peeringdb_api_docs_s002_paths_072`
  - `peeringdb_api_docs_s002_paths_080`
  - `peeringdb_api_docs_s002_paths_096`
  - `peeringdb_api_docs_s002_paths_106`
  - `peeringdb_api_docs_s002_paths_153`
  - `peeringdb_api_docs_s002_paths_170`
  - `peeringdb_api_docs_s002_paths_197`

## 26. RIPEstat Data API

- 实体 ID：`datasource_ripestat`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `ripestat_api_docs`
  - `ripe_ris_docs`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/ripestat_api_docs.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/ripestat_api_docs.json`
- chunk 样例：
  - `ripe_ris_docs_s001_full_001`
  - `ripestat_api_docs_s001_full_001`
  - `ripestat_api_docs_s001_full_006`
  - `ripestat_api_docs_s001_full_002`
  - `ripestat_api_docs_s001_full_003`
  - `ripestat_api_docs_s001_full_004`
  - `ripestat_api_docs_s001_full_005`

## 27. routeviews_endpoint

- 实体 ID：`field_routeviews_endpoint`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `routeviews_api_doc`
- cleaned 路径：
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `routeviews_api_doc_s001_full_020`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_004`
  - `routeviews_api_doc_s001_full_011`
  - `routeviews_api_doc_s001_full_016`
  - `routeviews_api_doc_s001_full_017`
  - `routeviews_api_doc_s001_full_019`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_002`
  - `routeviews_api_doc_s001_full_005`
  - `routeviews_api_doc_s001_full_006`
  - `routeviews_api_doc_s001_full_007`

## 28. RPKI-to-Router Delivery

- 实体 ID：`mechanism_rpki_to_router_delivery`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc8210`
  - `rfc6480`
- cleaned 路径：
  - `cleaned/standards/rfc6480.md`
  - `cleaned/standards/rfc8210.md`
- parsed 路径：
  - `parsed/standards/rfc6480.json`
  - `parsed/standards/rfc8210.json`
- chunk 样例：
  - `rfc6480_s012_4_001`
  - `rfc6480_s007_2_3_001`
  - `rfc6480_s010_3_1_001`
  - `rfc6480_s002_1_001`
  - `rfc6480_s015_4_3_002`
  - `rfc6480_s026_7_2_001`
  - `rfc6480_s004_2_001`
  - `rfc6480_s014_4_2_001`
  - `rfc6480_s023_4_001`
  - `rfc6480_s038_11_1_001`
  - `rfc6480_s039_11_2_001`
  - `rfc6480_s002_1_002`

## 29. rpki_rtr_pdu

- 实体 ID：`field_rpki_rtr_pdu`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc8210`
- cleaned 路径：
  - `cleaned/standards/rfc8210.md`
- parsed 路径：
  - `parsed/standards/rfc8210.json`
- chunk 样例：
  - `rfc8210_s038_14_001`
  - `rfc8210_s013_5_5_001`
  - `rfc8210_s014_5_6_001`
  - `rfc8210_s018_5_10_001`
  - `rfc8210_s019_5_11_001`
  - `rfc8210_s023_2_001`
  - `rfc8210_s029_9_001`
  - `rfc8210_s031_9_2_002`
  - `rfc8210_s002_1_001`
  - `rfc8210_s004_1_2_001`
  - `rfc8210_s007_4_001`
  - `rfc8210_s008_5_001`

## 30. rrc

- 实体 ID：`field_ris_rrc`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `ripe_ris_docs`
  - `ripe_ris_route_collectors`
  - `ripe_ris_raw_data`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/ripe_ris_raw_data.md`
  - `cleaned/data_docs/ripe_ris_route_collectors.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/ripe_ris_raw_data.json`
  - `parsed/data_docs/ripe_ris_route_collectors.json`
- chunk 样例：
  - `ripe_ris_docs_s001_full_001`
  - `ripe_ris_raw_data_s001_full_001`
  - `ripe_ris_raw_data_s001_full_002`
  - `ripe_ris_route_collectors_s001_full_001`
  - `ripe_ris_route_collectors_s001_full_002`
  - `ripe_ris_route_collectors_s001_full_003`

## 31. vrp_asn

- 实体 ID：`field_vrp_asn`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc6811`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `rfc6811_s003_2_001`
  - `rfc6811_s003_2_002`
  - `rfc6811_s003_2_003`
  - `rfc6811_s004_2_1_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s005_3_001`
  - `rfc6811_s006_4_001`
  - `rfc6811_s007_5_001`
  - `rfc6811_s008_6_001`

## 32. vrp_max_length

- 实体 ID：`field_vrp_max_length`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc6811`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `rfc6811_s003_2_001`
  - `rfc6811_s003_2_002`
  - `rfc6811_s004_2_1_001`
  - `rfc6811_s003_2_003`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s005_3_001`
  - `rfc6811_s006_4_001`
  - `rfc6811_s007_5_001`
  - `rfc6811_s008_6_001`

## 33. vrp_prefix

- 实体 ID：`field_vrp_prefix`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc6811`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `rfc6811_s003_2_001`
  - `rfc6811_s003_2_002`
  - `rfc6811_s003_2_003`
  - `rfc6811_s004_2_1_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s005_3_001`
  - `rfc6811_s006_4_001`
  - `rfc6811_s007_5_001`
  - `rfc6811_s008_6_001`

## 34. withdrawn_routes

- 实体 ID：`field_withdrawn_routes`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工打开 parsed/cleaned/chunk 证据；若实体字段被来源直接支持，可把 review_decision 改为 approved。
- 来源：
  - `rfc4271`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s015_4_3_001`
  - `rfc4271_s015_4_3_002`
  - `rfc4271_s021_2_002`
  - `rfc4271_s021_2_003`
  - `rfc4271_s038_6_3_001`
  - `rfc4271_s059_9_001`
  - `rfc4271_s061_9_1_1_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s035_6_001`
  - `rfc4271_s065_9_1_3_001`
  - `rfc4271_s066_9_1_4_001`

