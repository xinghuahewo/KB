# 02_ready_with_manual_note 复核清单

## 说明

本文件只展开人工复核入口。表内路径和 chunk ID 均来自现有流水线数据，未经过语义扩展。

## 35. Announcement

- 实体 ID：`concept_announcement`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s045_8_001`
  - `rfc4271_s060_9_1_001`
  - `rfc4271_s076_10_003`
  - `rfc4271_s004_10_001`

## 36. anomaly_moas

- 实体 ID：`evidence_moas`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s003_2_001`
  - `rfc6811_s010_8_1_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s003_2_002`
  - `rfc6811_s005_3_001`

## 37. anomaly_origin_change

- 实体 ID：`evidence_origin_change`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_route_leak_001`
  - `context_2026_paper_bear_001`
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s010_8_1_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s003_2_001`
  - `rfc6811_s006_4_001`
  - `rfc6811_s007_5_001`
  - `rfc6811_s001_1_003`

## 38. anomaly_path_hijack

- 实体 ID：`evidence_path_hijack`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpshield_2025_s010_page_10_002`
  - `bgpshield_2025_s002_page_2_001`
  - `bgpshield_2025_s007_page_7_002`
  - `bgpshield_2025_s001_page_1_003`
  - `bgpshield_2025_s003_page_3_002`
  - `bgpshield_2025_s004_page_4_002`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s012_page_12_003`
  - `bgpshield_2025_s005_page_5_001`
  - `bgpshield_2025_s008_page_8_001`
  - `bgpshield_2025_s001_page_1_001`
  - `bgpshield_2025_s004_page_4_001`

## 39. anomaly_path_manipulation

- 实体 ID：`evidence_path_manipulation`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpshield_2025_s004_page_4_002`
  - `bgpshield_2025_s010_page_10_002`
  - `bgpshield_2025_s010_page_10_001`
  - `bgpshield_2025_s002_page_2_001`
  - `bgpshield_2025_s005_page_5_001`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s008_page_8_001`
  - `bgpshield_2025_s003_page_3_002`
  - `bgpshield_2025_s007_page_7_002`
  - `bgpshield_2025_s008_page_8_002`
  - `bgpshield_2025_s008_page_8_003`
  - `bgpshield_2025_s009_page_9_002`

## 40. anomaly_prefix_hijack

- 实体 ID：`evidence_prefix_hijack`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `bear_2025_s004_page_4_003`
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s004_page_4_002`
  - `bear_2025_s007_page_7_002`
  - `bear_2025_s001_page_1_003`
  - `bear_2025_s002_page_2_001`
  - `bear_2025_s006_page_6_002`
  - `bear_2025_s007_page_7_003`
  - `bear_2025_s001_page_1_001`
  - `bear_2025_s003_page_3_002`
  - `bear_2025_s008_page_8_002`

## 41. anomaly_prefix_outage

- 实体 ID：`evidence_prefix_outage`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s058_8_2_2_004`
  - `rfc4271_s058_8_2_2_007`
  - `rfc4271_s058_8_2_2_011`
  - `rfc4271_s048_8_1_2_001`
  - `rfc4271_s058_8_2_2_010`
  - `rfc4271_s058_8_2_2_014`

## 42. anomaly_route_leak

- 实体 ID：`evidence_route_leak`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc7908`
  - `rfc9234`
  - `beam_2024`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/beam_2024.md`
  - `cleaned/standards/rfc7908.md`
  - `cleaned/standards/rfc9234.md`
- parsed 路径：
  - `parsed/papers/beam_2024.json`
  - `parsed/standards/rfc7908.json`
  - `parsed/standards/rfc9234.json`
- chunk 样例：
  - `beam_2024_s009_page_9_003`
  - `beam_2024_s009_page_9_001`
  - `beam_2024_s015_page_15_001`
  - `beam_2024_s009_page_9_002`
  - `beam_2024_s010_page_10_003`
  - `beam_2024_s013_page_13_001`
  - `beam_2024_s003_page_3_001`
  - `beam_2024_s010_page_10_002`
  - `beam_2024_s015_page_15_002`
  - `beam_2024_s002_page_2_003`
  - `beam_2024_s003_page_3_002`
  - `beam_2024_s003_page_3_003`

## 43. anomaly_subprefix_hijack

- 实体 ID：`evidence_subprefix_hijack`
- 实体类型：EvidenceTemplate
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_datasource_001`
  - `context_2026_scope_001`
  - `context_2026_as_path_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s008_6_001`
  - `rfc6811_s003_2_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s006_4_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s003_2_003`

## 44. AS

- 实体 ID：`concept_as`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s009_3_001`
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s015_4_3_001`

## 45. AS Relationship

- 实体 ID：`concept_as_relationship`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `caida_as_relationships`
  - `rfc7908`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/standards/rfc7908.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/standards/rfc7908.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_014`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_009`
  - `caida_as_relationships_s001_full_010`
  - `caida_as_relationships_s001_full_011`

## 46. AS relationship inference error

- 实体 ID：`fp_as_relationship_error`
- 实体类型：FalsePositivePattern
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `caida_as_relationships`
  - `rfc7908`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/standards/rfc7908.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/standards/rfc7908.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_013`
  - `caida_as_relationships_s001_full_014`
  - `caida_as_relationships_s001_full_015`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_009`

## 47. AS_PATH

- 实体 ID：`concept_as_path`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s003_page_3_001`
  - `bear_2025_s003_page_3_002`
  - `bear_2025_s004_page_4_001`
  - `bear_2025_s004_page_4_002`
  - `bear_2025_s004_page_4_003`
  - `bear_2025_s005_page_5_001`
  - `bear_2025_s005_page_5_002`
  - `bear_2025_s006_page_6_001`
  - `bear_2025_s006_page_6_002`
  - `bear_2025_s008_page_8_001`

## 48. as_path

- 实体 ID：`field_as_path`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s003_page_3_001`
  - `bear_2025_s003_page_3_002`
  - `bear_2025_s004_page_4_001`
  - `bear_2025_s004_page_4_002`
  - `bear_2025_s004_page_4_003`
  - `bear_2025_s005_page_5_001`
  - `bear_2025_s005_page_5_002`
  - `bear_2025_s006_page_6_001`
  - `bear_2025_s006_page_6_002`
  - `bear_2025_s001_page_1_001`

## 49. AS_PATH Prepending

- 实体 ID：`mechanism_as_path_prepending`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s009_3_003`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s022_4_4_001`
  - `rfc4271_s026_4_002`
  - `rfc4271_s029_5_1_2_001`

## 50. as_relationship_sequence

- 实体 ID：`field_as_relationship_sequence`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc7908`
  - `caida_as_relationships`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/standards/rfc7908.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/standards/rfc7908.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_009`
  - `caida_as_relationships_s001_full_010`
  - `caida_as_relationships_s001_full_011`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_013`

## 51. ASN

- 实体 ID：`concept_asn`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s021_2_002`
  - `rfc4271_s029_5_1_2_001`
  - `rfc4271_s029_5_1_2_002`
  - `rfc4271_s033_5_1_6_001`
  - `rfc4271_s034_5_1_7_001`
  - `rfc4271_s045_8_001`
  - `rfc4271_s064_9_1_2_2_001`

## 52. BEAR: BGP Event Analysis and Reporting

- 实体 ID：`paper_method_bear`
- 实体类型：PaperMethod
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
- chunk 样例：
  - `bear_2025_s001_page_1_001`
  - `bear_2025_s002_page_2_001`
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s007_page_7_001`
  - `bear_2025_s009_page_9_001`
  - `bear_2025_s001_page_1_003`
  - `bear_2025_s003_page_3_002`
  - `bear_2025_s003_page_3_003`
  - `bear_2025_s005_page_5_001`
  - `bear_2025_s006_page_6_003`
  - `bear_2025_s008_page_8_001`

## 53. Before-after AS path comparison

- 实体 ID：`mechanism_before_after_path_comparison`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
- chunk 样例：
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s004_page_4_003`
  - `bear_2025_s004_page_4_001`
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_001`
  - `bear_2025_s006_page_6_002`
  - `bear_2025_s005_page_5_002`
  - `bear_2025_s004_page_4_002`
  - `bear_2025_s003_page_3_002`
  - `bear_2025_s003_page_3_004`
  - `bear_2025_s003_page_3_001`
  - `bear_2025_s007_page_7_001`

## 54. BGP

- 实体 ID：`concept_bgp`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_001`
  - `rfc4271_s081_6_010`
  - `rfc4271_s009_3_002`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s011_3_2_001`

## 55. BGP Session

- 实体 ID：`concept_bgp_session`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s045_8_001`
  - `rfc4271_s081_6_009`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s046_10_001`
  - `rfc4271_s047_8_1_1_001`

## 56. BGP Speaker

- 实体 ID：`concept_bgp_speaker`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s009_3_001`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s021_2_001`
  - `rfc4271_s030_5_1_3_001`
  - `rfc4271_s030_5_1_3_002`

## 57. BGP Update

- 实体 ID：`concept_bgp_update`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bgpstream_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s076_10_003`
  - `rfc4271_s081_6_007`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`

## 58. BGPShield

- 实体 ID：`paper_method_bgpshield`
- 实体类型：PaperMethod
- 当前决策：`unreviewed`
- 当前状态：`pending`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
- chunk 样例：
  - `bgpshield_2025_s001_page_1_001`
  - `bgpshield_2025_s001_page_1_003`
  - `bgpshield_2025_s003_page_3_001`
  - `bgpshield_2025_s003_page_3_002`
  - `bgpshield_2025_s003_page_3_003`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s008_page_8_003`
  - `bgpshield_2025_s010_page_10_001`
  - `bgpshield_2025_s012_page_12_001`
  - `bgpshield_2025_s013_page_13_002`
  - `bgpshield_2025_s013_page_13_003`
  - `bgpshield_2025_s014_page_14_001`

## 59. BGPStream

- 实体 ID：`concept_bgpstream`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bgpstream_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`

## 60. BGPStream

- 实体 ID：`datasource_bgpstream`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bgpstream_docs`
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
  - `cleaned/papers/bear_2025.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
  - `parsed/papers/bear_2025.json`
- chunk 样例：
  - `bear_2025_s004_page_4_001`
  - `bear_2025_s006_page_6_001`
  - `bear_2025_s010_page_10_004`
  - `bear_2025_s001_page_1_001`
  - `bear_2025_s001_page_1_002`
  - `bear_2025_s001_page_1_003`
  - `bear_2025_s002_page_2_001`
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s003_page_3_001`
  - `bear_2025_s003_page_3_002`
  - `bear_2025_s003_page_3_003`

## 61. CAIDA AS Relationships

- 实体 ID：`datasource_caida_as_relationships`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `caida_as_relationships`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_013`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_011`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_015`
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_010`
  - `caida_as_relationships_s001_full_014`
  - `caida_as_relationships_s001_full_006`

## 62. CelerBridge BGP Hijack

- 实体 ID：`case_celerbridge_bgp_hijack`
- 实体类型：Case
- 当前决策：`unreviewed`
- 当前状态：`pending`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
- chunk 样例：
  - `bgpshield_2025_s002_page_2_001`
  - `bgpshield_2025_s011_page_11_002`
  - `bgpshield_2025_s004_page_4_002`
  - `bgpshield_2025_s008_page_8_003`
  - `bgpshield_2025_s010_page_10_001`
  - `bgpshield_2025_s010_page_10_002`
  - `bgpshield_2025_s003_page_3_002`
  - `bgpshield_2025_s004_page_4_001`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s005_page_5_001`
  - `bgpshield_2025_s007_page_7_002`
  - `bgpshield_2025_s008_page_8_002`

## 63. collector

- 实体 ID：`field_collector`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `ripe_ris_docs`
  - `bgpstream_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`
  - `routeviews_api_doc_s001_full_020`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_002`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_004`

## 64. Customer Cone

- 实体 ID：`concept_customer_cone`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `caida_as_relationships`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_008`
  - `caida_as_relationships_s001_full_014`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_009`
  - `caida_as_relationships_s001_full_010`
  - `caida_as_relationships_s001_full_011`
  - `caida_as_relationships_s001_full_013`
  - `caida_as_relationships_s001_full_015`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_012`

## 65. eBGP

- 实体 ID：`concept_ebgp`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s009_3_003`
  - `rfc4271_s030_5_1_3_002`
  - `rfc4271_s031_5_1_4_001`
  - `rfc4271_s038_6_3_002`
  - `rfc4271_s045_8_001`
  - `rfc4271_s060_9_1_001`

## 66. Facebook 2021 Outage

- 实体 ID：`case_facebook_2021_outage`
- 实体类型：Case
- 当前决策：`unreviewed`
- 当前状态：`pending`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `facebook_outage_cloudflare_2021`
  - `facebook_outage_meta_2021`
  - `context_2026`
- cleaned 路径：
  - `cleaned/cases/facebook_outage_cloudflare_2021.md`
  - `cleaned/cases/facebook_outage_meta_2021.md`
- parsed 路径：
  - `parsed/cases/facebook_outage_cloudflare_2021.json`
  - `parsed/cases/facebook_outage_meta_2021.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `context_2026_route_leak_001`
  - `facebook_outage_cloudflare_2021_s001_full_001`
  - `facebook_outage_cloudflare_2021_s001_full_007`
  - `facebook_outage_cloudflare_2021_s001_full_006`
  - `facebook_outage_cloudflare_2021_s001_full_008`
  - `facebook_outage_cloudflare_2021_s001_full_004`
  - `facebook_outage_cloudflare_2021_s001_full_005`
  - `facebook_outage_cloudflare_2021_s001_full_003`

## 67. FIB

- 实体 ID：`concept_fib`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s060_9_1_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`

## 68. iBGP

- 实体 ID：`concept_ibgp`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s009_3_003`
  - `rfc4271_s061_9_1_1_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s009_3_004`
  - `rfc4271_s011_3_2_001`

## 69. Indosat Route Leak

- 实体 ID：`case_indosat_route_leak`
- 实体类型：Case
- 当前决策：`unreviewed`
- 当前状态：`pending`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `indosat_route_leak_2014`
  - `context_2026`
- cleaned 路径：
  - `cleaned/cases/indosat_route_leak_2014.md`
- parsed 路径：
  - `parsed/cases/indosat_route_leak_2014.json`
- chunk 样例：
  - `context_2026_route_leak_001`
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `indosat_route_leak_2014_s001_full_001`
  - `indosat_route_leak_2014_s001_full_002`
  - `indosat_route_leak_2014_s001_full_005`
  - `indosat_route_leak_2014_s001_full_003`
  - `indosat_route_leak_2014_s001_full_004`
  - `indosat_route_leak_2014_s001_full_006`

## 70. IRR

- 实体 ID：`concept_irr`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc2622`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc2622.md`
- parsed 路径：
  - `parsed/standards/rfc2622.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc2622_s014_1_002`
  - `rfc2622_s038_12_001`
  - `rfc2622_s038_12_002`
  - `rfc2622_s015_2_004`
  - `rfc2622_s014_1_001`
  - `rfc2622_s016_3_001`
  - `rfc2622_s016_3_002`

## 71. Learning with Semantics / BEAM

- 实体 ID：`paper_method_beam`
- 实体类型：PaperMethod
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `beam_2024`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/beam_2024.md`
- parsed 路径：
  - `parsed/papers/beam_2024.json`
- chunk 样例：
  - `beam_2024_s002_page_2_001`
  - `beam_2024_s015_page_15_003`
  - `beam_2024_s011_page_11_004`
  - `beam_2024_s001_page_1_001`
  - `beam_2024_s003_page_3_001`
  - `beam_2024_s003_page_3_003`
  - `beam_2024_s005_page_5_001`
  - `beam_2024_s015_page_15_002`
  - `beam_2024_s002_page_2_003`
  - `beam_2024_s004_page_4_002`
  - `beam_2024_s004_page_4_003`
  - `beam_2024_s005_page_5_002`

## 72. Legitimate MOAS

- 实体 ID：`fp_legitimate_moas`
- 实体类型：FalsePositivePattern
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s003_2_001`
  - `rfc6811_s003_2_002`
  - `rfc6811_s003_2_003`

## 73. MOAS

- 实体 ID：`anomaly_moas`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s003_2_001`
  - `rfc6811_s010_8_1_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s003_2_002`
  - `rfc6811_s005_3_001`

## 74. MOAS

- 实体 ID：`concept_moas`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s003_2_001`
  - `rfc6811_s003_2_002`
  - `rfc6811_s003_2_003`

## 75. MRT

- 实体 ID：`concept_mrt`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `ripe_ris_docs`
  - `bgpstream_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
  - `cleaned/data_docs/ripe_ris_docs.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
  - `parsed/data_docs/ripe_ris_docs.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`

## 76. Origin AS

- 实体 ID：`concept_origin_as`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s045_8_001`
  - `rfc4271_s060_9_1_001`
  - `rfc4271_s076_10_003`
  - `rfc4271_s004_10_001`

## 77. Origin Change

- 实体 ID：`anomaly_origin_change`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `bgpshield_2025_s010_page_10_002`
  - `bgpshield_2025_s004_page_4_002`
  - `bgpshield_2025_s010_page_10_001`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s007_page_7_001`
  - `bgpshield_2025_s008_page_8_001`
  - `bgpshield_2025_s009_page_9_003`
  - `bgpshield_2025_s001_page_1_003`
  - `bgpshield_2025_s003_page_3_004`
  - `bgpshield_2025_s009_page_9_002`
  - `bgpshield_2025_s012_page_12_003`
  - `bgpshield_2025_s013_page_13_002`

## 78. origin_as

- 实体 ID：`field_origin_as`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s012_4_001`
  - `rfc4271_s013_4_1_001`
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s014_4_2_002`
  - `rfc4271_s015_4_3_001`

## 79. Pakistan Telecom / YouTube Hijack

- 实体 ID：`case_pakistan_youtube_2008`
- 实体类型：Case
- 当前决策：`unreviewed`
- 当前状态：`pending`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `youtube_hijack_google_2008`
  - `context_2026`
- cleaned 路径：
  - `cleaned/cases/youtube_hijack_google_2008.md`
- parsed 路径：
  - `parsed/cases/youtube_hijack_google_2008.json`
- chunk 样例：
  - `context_2026_route_leak_001`
  - `context_2026_datasource_001`
  - `context_2026_scope_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `youtube_hijack_google_2008_s001_full_003`
  - `youtube_hijack_google_2008_s001_full_001`
  - `youtube_hijack_google_2008_s001_full_002`

## 80. Path Hijack

- 实体 ID：`anomaly_path_hijack`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpshield_2025_s010_page_10_002`
  - `bgpshield_2025_s002_page_2_001`
  - `bgpshield_2025_s007_page_7_002`
  - `bgpshield_2025_s001_page_1_003`
  - `bgpshield_2025_s003_page_3_002`
  - `bgpshield_2025_s004_page_4_002`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s012_page_12_003`
  - `bgpshield_2025_s005_page_5_001`
  - `bgpshield_2025_s008_page_8_001`
  - `bgpshield_2025_s001_page_1_001`
  - `bgpshield_2025_s004_page_4_001`

## 81. Path Manipulation

- 实体 ID：`anomaly_path_manipulation`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpshield_2025_s004_page_4_002`
  - `bgpshield_2025_s010_page_10_002`
  - `bgpshield_2025_s010_page_10_001`
  - `bgpshield_2025_s011_page_11_002`
  - `bgpshield_2025_s002_page_2_001`
  - `bgpshield_2025_s005_page_5_001`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s008_page_8_001`
  - `bgpshield_2025_s003_page_3_002`
  - `bgpshield_2025_s007_page_7_002`
  - `bgpshield_2025_s008_page_8_002`
  - `bgpshield_2025_s008_page_8_003`

## 82. Path-vector routing

- 实体 ID：`mechanism_path_vector`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s026_4_002`
  - `rfc4271_s009_3_003`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s022_4_4_001`
  - `rfc4271_s031_5_1_4_001`

## 83. Peer

- 实体 ID：`concept_peer`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`
  - `routeviews_api_doc_s001_full_011`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_007`
  - `routeviews_api_doc_s001_full_008`
  - `routeviews_api_doc_s001_full_009`

## 84. peer_asn

- 实体 ID：`field_peer_asn`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`
  - `routeviews_api_doc_s001_full_007`
  - `routeviews_api_doc_s001_full_008`
  - `routeviews_api_doc_s001_full_010`
  - `routeviews_api_doc_s001_full_011`
  - `routeviews_api_doc_s001_full_016`
  - `routeviews_api_doc_s001_full_017`

## 85. Prefix

- 实体 ID：`concept_prefix`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s076_10_003`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s021_2_003`
  - `rfc4271_s045_8_001`

## 86. prefix

- 实体 ID：`field_prefix`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s012_4_001`
  - `rfc4271_s013_4_1_001`
  - `rfc4271_s014_4_2_001`
  - `rfc4271_s014_4_2_002`
  - `rfc4271_s015_4_3_001`

## 87. Prefix Hijack

- 实体 ID：`anomaly_prefix_hijack`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `rfc6811`
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
  - `cleaned/standards/rfc4271.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
  - `parsed/standards/rfc4271.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `bear_2025_s006_page_6_002`
  - `bear_2025_s007_page_7_001`
  - `bear_2025_s004_page_4_003`
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s004_page_4_002`
  - `bear_2025_s010_page_10_004`
  - `bear_2025_s007_page_7_002`
  - `bear_2025_s001_page_1_003`
  - `bear_2025_s002_page_2_001`
  - `bear_2025_s007_page_7_003`
  - `bear_2025_s001_page_1_001`

## 88. Prefix Outage

- 实体 ID：`anomaly_prefix_outage`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_scope_001`
  - `rfc4271_s006_1_1_001`
  - `rfc4271_s058_8_2_2_004`
  - `rfc4271_s058_8_2_2_007`
  - `rfc4271_s058_8_2_2_011`
  - `rfc4271_s048_8_1_2_001`
  - `rfc4271_s058_8_2_2_010`
  - `rfc4271_s058_8_2_2_014`

## 89. RIB

- 实体 ID：`concept_rib`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `routeviews_api_doc`
  - `bgpstream_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
  - `cleaned/data_docs/routeviews_api_doc.md`
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
  - `parsed/data_docs/routeviews_api_doc.json`
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `context_2026_paper_bear_001`
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s006_1_1_002`
  - `rfc4271_s010_3_1_001`
  - `rfc4271_s060_9_1_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_001`

## 90. RIPE RIS

- 实体 ID：`concept_ripe_ris`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`

## 91. RIPE RIS

- 实体 ID：`datasource_ripe_ris`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`

## 92. ROA

- 实体 ID：`concept_roa`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s010_8_1_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s003_2_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s003_2_002`

## 93. roa_status

- 实体 ID：`field_roa_status`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s003_2_001`
  - `rfc6811_s010_8_1_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s003_2_002`

## 94. Route Collector

- 实体 ID：`concept_route_collector`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_002`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_004`
  - `routeviews_api_doc_s001_full_005`
  - `routeviews_api_doc_s001_full_007`

## 95. Route Leak

- 实体 ID：`anomaly_route_leak`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc7908`
  - `rfc9234`
  - `beam_2024`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/beam_2024.md`
  - `cleaned/standards/rfc7908.md`
  - `cleaned/standards/rfc9234.md`
- parsed 路径：
  - `parsed/papers/beam_2024.json`
  - `parsed/standards/rfc7908.json`
  - `parsed/standards/rfc9234.json`
- chunk 样例：
  - `beam_2024_s009_page_9_003`
  - `beam_2024_s013_page_13_001`
  - `beam_2024_s002_page_2_003`
  - `beam_2024_s003_page_3_003`
  - `beam_2024_s011_page_11_003`
  - `beam_2024_s009_page_9_001`
  - `beam_2024_s014_page_14_002`
  - `beam_2024_s015_page_15_001`
  - `beam_2024_s004_page_4_002`
  - `beam_2024_s009_page_9_002`
  - `beam_2024_s010_page_10_003`
  - `beam_2024_s003_page_3_001`

## 96. Route Origin Validation

- 实体 ID：`mechanism_route_origin_validation`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s006_4_001`
  - `rfc6811_s008_6_001`
  - `rfc6811_s003_2_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s003_2_002`

## 97. RouteViews

- 实体 ID：`concept_routeviews`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `routeviews_api_doc_s001_full_018`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_002`
  - `routeviews_api_doc_s001_full_004`
  - `routeviews_api_doc_s001_full_005`
  - `routeviews_api_doc_s001_full_006`

## 98. RouteViews

- 实体 ID：`datasource_routeviews`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_002`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_004`
  - `routeviews_api_doc_s001_full_005`
  - `routeviews_api_doc_s001_full_006`
  - `routeviews_api_doc_s001_full_007`

## 99. ROV

- 实体 ID：`concept_rov`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s003_2_002`
  - `rfc6811_s005_3_001`
  - `rfc6811_s008_6_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s003_2_001`

## 100. RPKI

- 实体 ID：`concept_rpki`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s011_8_2_001`
  - `rfc6811_s001_1_003`
  - `rfc6811_s002_1_1_001`
  - `rfc6811_s006_4_001`
  - `rfc6811_s008_6_001`

## 101. RPKI / ROA

- 实体 ID：`datasource_rpki_roa`
- 实体类型：DataSource
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `routeviews_api_doc`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/routeviews_api_doc.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/data_docs/routeviews_api_doc.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc6811_s001_1_001`
  - `rfc6811_s001_1_002`
  - `rfc6811_s001_1_003`
  - `rfc6811_s003_2_001`
  - `rfc6811_s006_4_001`
  - `rfc6811_s008_6_001`
  - `rfc6811_s010_8_1_001`

## 102. Short route flap

- 实体 ID：`fp_short_route_flap`
- 实体类型：FalsePositivePattern
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `rfc4271_s004_10_001`
  - `rfc4271_s030_5_1_3_003`
  - `rfc4271_s046_10_001`
  - `rfc4271_s058_8_2_2_001`
  - `rfc4271_s066_9_1_4_001`
  - `rfc4271_s069_9_2_1_1_001`
  - `rfc4271_s081_6_003`

## 103. Single collector bias

- 实体 ID：`fp_single_collector_bias`
- 实体类型：FalsePositivePattern
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `routeviews_api_doc`
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
  - `cleaned/data_docs/routeviews_api_doc.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
  - `parsed/data_docs/routeviews_api_doc.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`
  - `routeviews_api_doc_s001_full_007`
  - `routeviews_api_doc_s001_full_001`
  - `routeviews_api_doc_s001_full_002`
  - `routeviews_api_doc_s001_full_003`
  - `routeviews_api_doc_s001_full_004`
  - `routeviews_api_doc_s001_full_005`

## 104. Subprefix Hijack

- 实体 ID：`anomaly_subprefix_hijack`
- 实体类型：AnomalyType
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc6811`
  - `bear_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bear_2025.md`
  - `cleaned/standards/rfc6811.md`
- parsed 路径：
  - `parsed/papers/bear_2025.json`
  - `parsed/standards/rfc6811.json`
- chunk 样例：
  - `bear_2025_s004_page_4_003`
  - `bear_2025_s002_page_2_002`
  - `bear_2025_s002_page_2_003`
  - `bear_2025_s004_page_4_002`
  - `bear_2025_s003_page_3_003`
  - `bear_2025_s006_page_6_001`
  - `bear_2025_s006_page_6_002`
  - `bear_2025_s007_page_7_002`
  - `bear_2025_s001_page_1_001`
  - `bear_2025_s002_page_2_001`
  - `bear_2025_s007_page_7_001`
  - `bear_2025_s008_page_8_002`

## 105. timestamp

- 实体 ID：`field_timestamp`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bgpstream_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/bgpstream_docs.md`
- parsed 路径：
  - `parsed/data_docs/bgpstream_docs.json`
- chunk 样例：
  - `bgpstream_docs_s001_full_001`
  - `context_2026_datasource_001`
  - `context_2026_as_path_001`
  - `context_2026_paper_bear_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`

## 106. update_type

- 实体 ID：`field_update_type`
- 实体类型：DataField
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_datasource_001`
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s013_4_1_001`
  - `rfc4271_s014_4_2_002`
  - `rfc4271_s015_4_3_002`
  - `rfc4271_s015_4_3_003`
  - `rfc4271_s019_2_001`
  - `rfc4271_s021_2_001`
  - `rfc4271_s023_4_5_001`

## 107. Valley-free

- 实体 ID：`concept_valley_free`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc7908`
  - `caida_as_relationships`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/standards/rfc7908.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/standards/rfc7908.json`
- chunk 样例：
  - `caida_as_relationships_s001_full_014`
  - `caida_as_relationships_s001_full_007`
  - `caida_as_relationships_s001_full_005`
  - `caida_as_relationships_s001_full_006`
  - `caida_as_relationships_s001_full_012`
  - `caida_as_relationships_s001_full_001`
  - `caida_as_relationships_s001_full_002`
  - `caida_as_relationships_s001_full_003`
  - `caida_as_relationships_s001_full_004`
  - `caida_as_relationships_s001_full_008`
  - `caida_as_relationships_s001_full_009`
  - `caida_as_relationships_s001_full_010`

## 108. Valley-free Routing

- 实体 ID：`mechanism_valley_free`
- 实体类型：RoutingMechanism
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc7908`
  - `caida_as_relationships`
  - `beam_2024`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/caida_as_relationships.md`
  - `cleaned/papers/beam_2024.md`
  - `cleaned/standards/rfc7908.md`
- parsed 路径：
  - `parsed/data_docs/caida_as_relationships.json`
  - `parsed/papers/beam_2024.json`
  - `parsed/standards/rfc7908.json`
- chunk 样例：
  - `beam_2024_s004_page_4_002`
  - `beam_2024_s011_page_11_003`
  - `beam_2024_s013_page_13_004`
  - `beam_2024_s004_page_4_001`
  - `beam_2024_s003_page_3_002`
  - `beam_2024_s012_page_12_003`
  - `beam_2024_s002_page_2_002`
  - `beam_2024_s013_page_13_001`
  - `beam_2024_s003_page_3_001`
  - `beam_2024_s004_page_4_003`
  - `beam_2024_s005_page_5_001`
  - `beam_2024_s005_page_5_002`

## 109. Vantage Point

- 实体 ID：`concept_vantage_point`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `ripe_ris_docs`
  - `context_2026`
- cleaned 路径：
  - `cleaned/data_docs/ripe_ris_docs.md`
- parsed 路径：
  - `parsed/data_docs/ripe_ris_docs.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `ripe_ris_docs_s001_full_001`

## 110. Vodafone Idea AS55410 Route Leak

- 实体 ID：`case_vodafone_2021_route_leak`
- 实体类型：Case
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `bgpshield_2025`
  - `context_2026`
- cleaned 路径：
  - `cleaned/papers/bgpshield_2025.md`
- parsed 路径：
  - `parsed/papers/bgpshield_2025.json`
- chunk 样例：
  - `bgpshield_2025_s012_page_12_002`
  - `bgpshield_2025_s012_page_12_003`
  - `bgpshield_2025_s015_page_15_003`
  - `bgpshield_2025_s013_page_13_001`
  - `bgpshield_2025_s011_page_11_002`
  - `bgpshield_2025_s004_page_4_003`
  - `bgpshield_2025_s007_page_7_002`
  - `bgpshield_2025_s014_page_14_001`
  - `bgpshield_2025_s001_page_1_002`
  - `bgpshield_2025_s003_page_3_004`
  - `bgpshield_2025_s011_page_11_004`
  - `bgpshield_2025_s014_page_14_002`

## 111. WHOIS / RDAP

- 实体 ID：`concept_whois_rdap`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc3912`
  - `rfc9082`
  - `rfc9083`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc3912.md`
  - `cleaned/standards/rfc9082.md`
  - `cleaned/standards/rfc9083.md`
- parsed 路径：
  - `parsed/standards/rfc3912.json`
  - `parsed/standards/rfc9082.json`
  - `parsed/standards/rfc9083.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc3912_s001_1_001`
  - `rfc3912_s002_2_001`
  - `rfc3912_s003_3_001`
  - `rfc3912_s004_4_001`
  - `rfc3912_s005_5_001`
  - `rfc3912_s008_21355_001`
  - `rfc3912_s008_21355_002`

## 112. Withdrawal

- 实体 ID：`concept_withdrawal`
- 实体类型：BGPConcept
- 当前决策：`unreviewed`
- 当前状态：`approved`
- 复核指令：人工优先核验非 manual_note 来源；context_2026 只作范围提示，不能单独作为批准依据。
- 来源：
  - `rfc4271`
  - `context_2026`
- cleaned 路径：
  - `cleaned/standards/rfc4271.md`
- parsed 路径：
  - `parsed/standards/rfc4271.json`
- chunk 样例：
  - `context_2026_paper_bear_001`
  - `context_2026_as_path_001`
  - `context_2026_datasource_001`
  - `context_2026_route_leak_001`
  - `context_2026_scope_001`
  - `rfc4271_s005_1_001`
  - `rfc4271_s009_3_002`
  - `rfc4271_s011_3_2_001`
  - `rfc4271_s045_8_001`
  - `rfc4271_s060_9_1_001`
  - `rfc4271_s069_9_2_1_1_001`
  - `rfc4271_s076_10_003`

