# 阶段 4.3 RAG 答案评测报告

## 摘要

- 生成时间：2026-06-20T17:27:53
- DeepSeek API key 配置：否
- 密钥记录：未写入报告、数据集或仓库。
- 问题数：20
- 通过数：20
- 失败数：0
- 引用覆盖率：100.00%
- 无证据拒答率：100.00%
- citations 全部来自 context_pack：是

## 边界确认

- 当前设备不运行本地模型。
- 评测只调用 RAG Answer 编排，不写回实体、关系、chunk 或发布包。
- 无证据问题必须拒答。
- `DEEPSEEK_API_KEY` 只从环境变量读取。

## 逐题结果

| ID | 查询 | 预期 | 实际 | 结论 | 引用数 | 失败检查 |
| --- | --- | --- | --- | --- | ---: | --- |
| rag_eval_001_bgp_definition | What is BGP? | answered | answered | pass | 5 |  |
| rag_eval_002_route_leak_definition | What is a BGP route leak? | answered | answered | pass | 5 |  |
| rag_eval_003_route_leak_cn | 路由泄露是什么？ | answered | answered | pass | 5 |  |
| rag_eval_004_youtube_hijack_case | What happened in the YouTube hijack incident? | answered | answered | pass | 3 |  |
| rag_eval_005_aws_route53_case | AWS Route53 cryptocurrency BGP hijack case | answered | answered | pass | 1 |  |
| rag_eval_006_cloudflare_verizon_case | Cloudflare Verizon route leak 2019 incident | answered | answered | pass | 2 |  |
| rag_eval_007_route_flap | What is route flap in BGP? | answered | answered | pass | 5 |  |
| rag_eval_008_rpki_validation | What is RPKI validation? | answered | answered | pass | 5 |  |
| rag_eval_009_roa | What is a ROA in RPKI? | answered | answered | pass | 5 |  |
| rag_eval_010_aspa | What is ASPA for routing security? | answered | answered | pass | 2 |  |
| rag_eval_011_routeviews | What does RouteViews provide for BGP analysis? | answered | answered | pass | 2 |  |
| rag_eval_012_ripe_ris | What is RIPE RIS raw data used for? | answered | answered | pass | 3 |  |
| rag_eval_013_bgpstream | How is BGPStream used in BGP event analysis? | answered | answered | pass | 4 |  |
| rag_eval_014_asrank | What does CAIDA ASRank describe? | answered | answered | pass | 1 |  |
| rag_eval_015_artemis | What does ARTEMIS detect in BGP hijacking? | answered | answered | pass | 4 |  |
| rag_eval_016_bear | What is BEAR for BGP event analysis? | answered | answered | pass | 3 |  |
| rag_eval_017_beam | What is BEAM semantics-aware routing anomaly detection? | answered | answered | pass | 4 |  |
| rag_eval_018_no_evidence_random | zzzzqqqxxxx imaginaryobject quuxword | no_evidence | no_evidence | pass | 0 |  |
| rag_eval_019_no_evidence_bread | blorfmuffin xylocake narpcrumb | no_evidence | no_evidence | pass | 0 |  |
| rag_eval_020_no_evidence_fiction | quuxflux zarnoble wibblepath | no_evidence | no_evidence | pass | 0 |  |

## 需人工复核

- 无。
