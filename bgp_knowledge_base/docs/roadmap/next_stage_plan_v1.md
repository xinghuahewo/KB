---
title: "BGP KB 下一阶段建设计划 v1"
document_type: "路线图"
purpose: "记录当前阶段状态、下一步建设目标和不可突破的边界约束。"
scope: "BGP KB 阶段四到阶段五"
status: "现行参考"
last_reviewed: "2026-06-20"
---
# BGP KB 下一阶段建设计划 v1

## 当前基线

BGP KB 已经具备结构化知识库、只读服务、RAG Answer API、DeepSeek 调用、固定评测集和真实批量评测能力。

| 能力 | 当前状态 | 证据位置 |
| --- | --- | --- |
| 清洗文本、chunk、实体、关系、术语表 | 已完成 | `cleaned/`、`chunks/`、`entities/`、`relationships/`、`datasets/glossary.jsonl` |
| 发布包 | 已完成 | `published/` |
| 只读服务 | 已完成 | `service/` |
| RAG context pack | 已完成初版 | `service/retrieval_framework.py` |
| RAG Answer API | 已完成 | `service/rag_answer.py`、`POST /api/v1/rag/answer` |
| DeepSeek smoke 与批量评测 | 已完成 | `reports/deepseek_rag_answer_eval_report.md` |
| 答案质量评测集 | 已完成，20 题 | `datasets/rag_answer_eval_questions.jsonl` |
| 本地模型运行 | 禁用 | 配置和阶段边界 |

## 下一阶段终极目标

阶段 4.5 的终极目标：

> 在当前设备不运行模型的前提下，接入阿里云 BGE-M3 远程 embedding，建立向量检索、BM25/关键词检索、元数据过滤与排序融合的混合检索框架，并让 RAG Answer API 能基于更稳定的 context pack 回答。

该阶段不追求一次性上 Milvus 集群，也不在本机部署 Qwen/BGE-M3。目标是先把工业界常见的混合检索链路变成可复跑、可评测、可回滚的本地框架。

## 推荐执行顺序

```text
1. 合并阶段 4.4 到 main
2. 新建阶段 4.5 分支
3. 配置阿里云 BGE-M3 远程 embedding provider
4. 构建可复跑 embedding index 与 manifest
5. 实现 BM25/关键词 + 向量 + 元数据过滤 + RRF 融合
6. 接入 retrieval/context-pack 与 RAG Answer
7. 建立混合检索评测报告
8. 跑阶段验收、质量检查和密钥扫描
```

## 阶段边界

- DeepSeek key、阿里云 endpoint 和 token 只从环境变量读取。
- 当前设备不运行本地模型。
- 不下载 BGE-M3、Qwen 或其它大模型权重。
- 阶段 4.5 默认不引入 Milvus 服务；先用文件化向量索引跑通小规模闭环。
- 不自动写回实体、关系、chunk、术语表或人工复核状态。
- 无阿里云 key 时，脚本必须能用 fake client 跑结构测试。
- 所有检索结果必须保留 `source_ref`、`chunk_id`、`review_status` 和排序解释。

## 阶段四剩余差距

| 差距 | 4.5 处理方式 |
| --- | --- |
| 只有关键词/规则排序，缺少真实向量召回 | 接入阿里云 BGE-M3 dense embedding |
| 中文同义查询依赖手写扩展 | 保留 query expansion，同时用跨语言 embedding 补召回 |
| 检索排序解释不足 | 输出 lexical/vector/metadata/fusion score |
| 评测更偏答案质量，检索指标不足 | 新增 recall@k、MRR、source coverage、citation hit rate |
| 没有 embedding manifest | 生成 index manifest，记录模型、维度、输入 hash 和构建时间 |

## 后续阶段关系

- 阶段 4.5 完成后，阶段四可视为“RAG 就绪与混合检索较优解 v1”。
- 阶段五再做 JSON-LD、SKOS、PROV-O 等标准出口，不反向改动阶段四主流程。
- 阶段六再扩展知识覆盖，避免在检索质量未稳定前扩大治理压力。
