# RAG 证据链五阶段流水线

本文是数据候选构建、验证、迁移和故障诊断的长期权威入口。细粒度脚本继续保留用于阶段内部实现和诊断，但不得再作为生产主流程逐个手工串联。

## 五阶段入口

五阶段依赖固定且线性：

```text
source-ingest → canonicalize → semantic-build → publish-index → verify-release
```

| 阶段 | 稳定入口 | 权威输出 |
| --- | --- | --- |
| 来源采集 | `make source-ingest CANDIDATE_DIR=<候选目录>` | 来源注册表终态、不可变 source snapshots |
| 规范化 | `make canonicalize CANDIDATE_DIR=<候选目录>` | Canonical Document v2、资产和解析诊断 |
| 语义构建 | `make semantic-build CANDIDATE_DIR=<候选目录>` | SemanticChunk v3、治理状态、Retrieval Document v1 |
| 发布索引 | `make publish-index CANDIDATE_DIR=<候选目录>` | catalog、数据库、FTS、embedding 和快索引闭包 |
| 发布验证 | `make verify-release CANDIDATE_DIR=<候选目录>` | 统一门禁报告和可供 canary 使用的已验证候选 |

执行某一阶段时，编排器会检查并复用它之前的有效 checkpoint；不得跳过依赖或直接把细粒度脚本的零散输出拼成 release。查看计划可追加 `PIPELINE_ARGS=--plan-only`。本流程不自动提交、部署或切换线上制品。

## 候选目录边界

候选目录必须与 `current`、`previous` 及其 release 目录完全分离，不能是指向它们的符号链接，也不能包含或被受保护路径包含。候选目录 basename 同时作为五阶段统一的 `BGPKB_RELEASE_ID`，应使用稳定且唯一的候选 ID。推荐布局：

```text
<candidate>/
  .pipeline/
    candidate.json
    checkpoints/<stage>.json
    manifests/<stage>.json
    logs/<stage>/<subtask>.*.log
    invalidations.json
    tmp/
    cache/
  source-store/
  data/
    manifests/
    corpus/
    derived/datasets/
    generated/reports/
    published/
```

所有子任务必须声明候选内写根。`BGPKB_DATA_DIR`、`BGPKB_SOURCE_STORE_DIR`、临时目录和缓存目录都由编排器重定向到候选目录；阶段不得写 current release。候选构建期间 `candidate.json` 的 `reader_selectable=false`，失败后状态为 `failed`，在线 reader 会失败关闭，避免把临时文件或半成品误当成完整制品。只有整个 `verify-release` 成功后，候选才标记为 `verified`，用于后续显式 canary；仍不得自动切换 `current` 或 `previous`。

## Checkpoint 与恢复

每个阶段 checkpoint 同时绑定：

- 声明的输入 manifest 与外部输入指纹；
- 版本化配置指纹；
- 编排器及阶段内部脚本的代码指纹；
- 上游阶段 manifest 指纹；
- 本阶段必需输出的 SHA-256。

相同指纹重跑会复用已校验阶段；输入、配置、代码或上游 manifest 变化时，从首个受影响阶段开始失效全部下游 checkpoint。失效原因记录在 `.pipeline/invalidations.json`。恢复时重新执行原命令即可，不要复制旧 checkpoint、改写 manifest 或手工伪造成功状态。embedding 自身的批次 checkpoint 仍由 embedding 构建器管理，并受 retrieval text、模型 revision、归一化和 provider contract 指纹约束。

## publish-index 制品闭包

`publish-index` 只有在以下候选制品全部存在且闭合时才成功：

- `data/published/source_catalog.jsonl`；
- `data/published/chunk_catalog.jsonl`；
- `data/published/retrieval_documents_v1.jsonl`；
- `data/published/serving.sqlite`，其中 FTS5 必须索引同一 retrieval input；
- `data/published/governance.sqlite`；
- `data/published/bge_m3_vector_index.jsonl`；
- `data/published/bge_m3_embedding_manifest.json`；
- `data/published/bge_m3_vector_matrix.npy`；
- `data/published/bge_m3_vector_metadata.jsonl`；
- `data/published/bge_m3_vector_fast_manifest.json`；
- `data/derived/datasets/artifact_manifest.jsonl`；
- `data/published/publish_index_manifest_v1.json`。

`publish_index_manifest_v1.json` 为每个逻辑角色绑定 release ID、候选内相对路径、SHA-256、记录数、适用的模型 revision 和 retrieval input manifest hash。Retrieval Document、serving/FTS、embedding JSONL 和 fast metadata 的 ID 集必须闭合；fast manifest 必须绑定 embedding JSONL 的 SHA-256。任一缺失、跨 release、hash 不匹配、模型 revision 缺失或 ID 集不闭合都会非零失败，且原子写入不会覆盖上一份完整 manifest。

## 迁移与完整重建

当 chunk、retrieval contract 或 serving schema 不兼容时，必须从冻结 snapshots 在新候选目录全量派生，不能原地修改旧 release：

1. 冻结 source registry、snapshots、代码提交、当前 release 和 `SHA256SUMS`。
2. 运行 `source-ingest`，只导入或引用不可变 raw objects。
3. 运行 `canonicalize`；只有 Schema/闭包失败或受新策略影响的文档才重新走 Docling。
4. 运行 `semantic-build`，复核语义切块、治理状态、隔离清单和 chunk ID 迁移。
5. 运行 `publish-index`，按 Retrieval Document → serving/governance DB/FTS → embedding JSONL → fast index → manifest 的顺序形成闭包。
6. 运行 `verify-release`；失败只修复候选并从首个失效阶段恢复。
7. 生成新的不可变 release、`SHA256SUMS`、迁移证据和成对回滚命令，不修改历史 release。

v1 parsed/chunks 和 legacy reader 只保留为受控只读迁移入口，不得进入新 serving、embedding、真实评测或治理决定；正式退役必须等待一个稳定发布周期和零生产引用证明。

## verify-release 统一门禁

最终 `data/published/release_verification_report_v1.json` 必须覆盖以下矩阵：

| 门禁 | 失败关闭条件 |
| --- | --- |
| 候选 manifest | 缺失、hash/ID/release 闭包不成立 |
| 黄金集 owner | owner、reviewer 或 PR 变更控制未登记 |
| 制品完整性 | Schema、追溯、数据库或索引完整性失败 |
| 生产数据质量 | 空 retrieval text、非法短块、重复或 ID 闭包越界 |
| 真实检索黄金集 | 非候选输入、结构 mock、硬失败或 `skipped_blocking` |
| 结构化回答黄金集 | claim/citation、拒答、注入防护或真实模型执行失败 |
| 真实模型配置 | embedding、reranker、LLM 任一 model/revision 或 prompt version 缺失/不匹配 |
| 性能 | 非 `fast_numpy`、degraded 或 p95 超过版本阈值 |
| 报告新鲜度 | release、候选 manifest、代码提交、模型、prompt 或时间不匹配 |
| 版本化阈值 | 任一硬指标低于 `rag_quality_gates_v1.yaml` |

阶段内部报告任务即使返回非零，也会先保留各自报告并继续到最终统一门禁；编排器记录所有非零，最终报告生成成功不得掩盖失败。任一 `fail` 或 `skipped_blocking` 都使 `verify-release` 返回非零。结构 mock、旧报告和当前线上旧 release 的结果不能替代本次候选真实评测。

## 成对发布与回滚

通过 `verify-release` 只表示候选可进入隔离 canary，不代表已发布。发布必须绑定代码 generation、前端构建标识、artifact release ID 和 `SHA256SUMS`，并另行获得人工批准；流水线不得自动切换任何指针。

canary 通过后，运维流程才可用 `make deploy ARGS="<code-release-dir> <artifact-release-dir>"` 原子切换代码/制品对。回滚使用 `make rollback` 同时恢复上一代码 generation 与 `previous` artifact，不重建或改写历史 release。不得把新代码与旧 serving bundle、或旧代码与新制品交叉组合。

## 故障诊断

1. 查看 `<candidate>/.pipeline/candidate.json`，确认 `status`、失败阶段和 reader 可选状态。
2. 查看 `.pipeline/manifests/<stage>.json` 的 `diagnostics` 和子任务返回码。
3. 查看 `.pipeline/logs/<stage>/` 的 stdout/stderr；不要只凭终端最后一行判断。
4. 查看 `.pipeline/invalidations.json`，确认首次失效阶段及输入、配置、代码或上游指纹变化。
5. `publish-index` 失败时运行候选内的闭包校验，重点检查 release ID、artifact manifest、model revision、retrieval input hash 和 ID 集。
6. `verify-release` 失败时读取统一门禁矩阵；`skipped_blocking` 是发布失败，不是可忽略跳过。
7. 任何失败都先保留候选证据并修复，再按 checkpoint 恢复；不得修改 current/previous、手工补写成功 manifest 或让 reader 指向失败候选。

现有细粒度脚本和 legacy reader 仍可用于只读诊断与兼容迁移。它们的存在不改变五阶段是唯一产品入口这一约束。
