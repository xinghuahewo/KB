# 阶段 4.5 混合检索评测报告

## 摘要

- 生成时间：2026-06-20T16:51:56
- 问题数：20
- 通过数：20
- 失败数：0
- Recall@5：84.31%
- Recall@8：87.25%
- MRR：0.6882
- 无证据拒答率：100.00%
- 来源类型覆盖：case_report, data_doc, paper, standard, tool_doc
- 当前设备未运行本地模型。
- 评测不写回实体、关系、chunk 或复核状态。

## 逐题结果

| ID | 查询 | 预期 | 结论 | Recall@5 | Recall@8 | RR | 向量状态 |
| --- | --- | --- | --- | ---: | ---: | ---: | --- |
| hybrid_eval_001_bgp_definition | What is BGP? | evidence | pass | 1.00 | 1.00 | 0.2500 | offline_mock |
| hybrid_eval_002_route_leak_definition | What is a BGP route leak? | evidence | pass | 0.50 | 0.50 | 0.2500 | offline_mock |
| hybrid_eval_003_route_leak_cn | 路由泄露是什么？ | evidence | pass | 0.50 | 0.50 | 0.2500 | offline_mock |
| hybrid_eval_004_youtube_case | What happened in the YouTube hijack incident? | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_005_aws_case | AWS Route53 cryptocurrency BGP hijack case | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_006_verizon_case | Cloudflare Verizon route leak 2019 incident | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_007_route_flap | What is route flap in BGP? | evidence | pass | 0.50 | 1.00 | 0.2500 | offline_mock |
| hybrid_eval_008_rpki | What is RPKI validation? | evidence | pass | 0.33 | 0.33 | 1.0000 | offline_mock |
| hybrid_eval_009_roa | What is a ROA in RPKI? | evidence | pass | 0.50 | 0.50 | 0.2000 | offline_mock |
| hybrid_eval_010_aspa | What is ASPA for routing security? | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_011_routeviews | What does RouteViews provide for BGP analysis? | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_012_ripe_ris | What is RIPE RIS raw data used for? | evidence | pass | 1.00 | 1.00 | 0.5000 | offline_mock |
| hybrid_eval_013_bgpstream | How is BGPStream used in BGP event analysis? | evidence | pass | 1.00 | 1.00 | 0.5000 | offline_mock |
| hybrid_eval_014_asrank | What does CAIDA ASRank describe? | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_015_artemis | What does ARTEMIS detect in BGP hijacking? | evidence | pass | 1.00 | 1.00 | 0.5000 | offline_mock |
| hybrid_eval_016_bear | What is BEAR for BGP event analysis? | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_017_beam | What is BEAM semantics-aware routing anomaly detection? | evidence | pass | 1.00 | 1.00 | 1.0000 | offline_mock |
| hybrid_eval_018_no_evidence_random | zzzzqqqxxxx imaginaryobject quuxword | no_evidence | pass | 1.00 | 1.00 | 0.0000 | offline_mock |
| hybrid_eval_019_no_evidence_bread | blorfmuffin xylocake narpcrumb | no_evidence | pass | 1.00 | 1.00 | 0.0000 | offline_mock |
| hybrid_eval_020_no_evidence_fiction | quuxflux zarnoble wibblepath | no_evidence | pass | 1.00 | 1.00 | 0.0000 | offline_mock |

## 失败与人工复核

- 无。
