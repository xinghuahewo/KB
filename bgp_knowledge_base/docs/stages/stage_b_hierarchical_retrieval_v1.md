---
title: "阶段 B 层级检索 v1"
document_type: "阶段交付说明"
purpose: "记录阶段 B 的交付范围、验收结果、模型服务、运行命令、降级边界和后续维护注意事项。"
scope: "阶段 B：层级 chunk、混合召回、reranker、query type、context pack 和远端模型服务"
status: "已交付并通过验收"
last_reviewed: "2026-07-08"
---
# 阶段 B 层级检索 v1

## 1. 交付结论

阶段 B 已于 2026-07-08 交付并合入主分支：

- 提交：`f6bb22b feat: 交付阶段 B 层级检索并完成验收`
- 阶段验收：`python -m bgpkb.pipeline.run_stage_acceptance --stage stage_b_hierarchical_retrieval_v1`，exit 0
- 全量测试复核：418 passed，1 个 Starlette/httpx deprecation warning
- 阶段 B 专项测试复核：31 passed

本阶段让 v2 chunk 从“扁平可检索文本”升级为“可追溯父 section、可回扩邻接上下文、可按查询类型预算组包”的层级检索单元，并接入私有 BGE-M3 embedding 与 BGE reranker 服务。

## 2. 核心能力

| 能力 | 当前状态 |
| --- | --- |
| section catalog | `data/derived/datasets/section_catalog.jsonl`，447 个 section |
| v2 chunk 层级字段 | `parent_section_id`、`chunk_order`、`previous_chunk_id`、`next_chunk_id`、`hierarchy_status` |
| 层级门禁 | 58,560/58,560 resolved，覆盖率 100% |
| 父 section 可追溯 | 100% |
| 相邻上下文正确率 | 100% |
| context unit 引用完整率 | 100% |
| 混合召回 | BM25 top 50 + BGE-M3 dense top 50，经 RRF(k=60) 融合保留 20 |
| reranker | `BAAI/bge-reranker-v2-m3`，`top_n` 合法范围 5–8，默认 5 |
| query type | `fact / procedure / policy / global / auto` |
| context pack 预算 | 默认 6000 tokens，硬上限 8000 tokens |
| v1/v2 隔离 | 自动化测试覆盖；本阶段不重复完整 v2→v1→v2 回滚演练 |

## 3. BGE-M3 向量索引

当前真实向量索引：

- 文件：`data/published/bge_m3_vector_index.jsonl`
- manifest：`data/published/bge_m3_embedding_manifest.json`
- provider：`local_http`
- 模型：`BAAI/bge-m3`
- revision：`5617a9f61b028005a4858fdac845db406aefb181`
- 输入数量：58,792
- 向量维度：1024
- 输入构成：
  - chunk：58,560
  - entity：112
  - glossary：112
  - evidence template：8

注意：58,792 不是 “58,560 chunks + 8 templates”，还包含 112 个 entity 和 112 个 glossary。

## 4. 远端模型服务

模型服务常驻在 `root@10.99.8.28`，通过 Docker Compose project `bgpkb-retrieval-models` 运行两个独立容器。

| 服务 | 端口 | 模型 | revision | GPU |
| --- | ---: | --- | --- | --- |
| embedding | 8011 | `BAAI/bge-m3` | `5617a9f61b028005a4858fdac845db406aefb181` | GPU 2 |
| reranker | 8012 | `BAAI/bge-reranker-v2-m3` | `953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e` | GPU 3 |

当前 release：

```text
d7f62ed1ccf6f7a0fa52142a0c39328b73ed76c92cc258dad78923f32804d8b0
```

镜像 digest：

```text
sha256:ffb0ca178759b35e74384343a596e779901d3c4abd7e1e5c51cfa5c0a7258d23
```

live symlink：

```text
/srv/bgpkb/retrieval-models
/srv/bgpkb/retrieval-models-models
```

release 根目录：

```text
/srv/bgpkb/retrieval-releases/d7f62ed1ccf6f7a0fa52142a0c39328b73ed76c92cc258dad78923f32804d8b0
```

## 5. 常用复核命令

远端服务器、端口、screen、FastAPI 后端和静态前端部署的统一操作入口见 [远端服务器与前端部署操作手册 v1](../operations/remote_server_operations_v1.md)。本节只保留阶段 B 模型服务和验收相关的最小复核命令。

SSH 时显式禁用本地代理配置：

```bash
ssh -F /dev/null \
  -o ProxyCommand=none \
  -o ProxyJump=none \
  root@10.99.8.28 'hostname'
```

检查容器和 GPU：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "retrieval|8011|8012"; \
   nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader,nounits'
```

检查 health：

```bash
curl --fail http://10.99.8.28:8011/health
curl --fail http://10.99.8.28:8012/health
```

检查 release manifest：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'python3 - <<'"'"'PY'"'"'
from pathlib import Path
import hashlib, json
release = "d7f62ed1ccf6f7a0fa52142a0c39328b73ed76c92cc258dad78923f32804d8b0"
manifest = Path(f"/srv/bgpkb/retrieval-releases/{release}/app/release_manifest.json")
content = manifest.read_bytes()
payload = json.loads(content)
print("manifest_sha256", hashlib.sha256(content).hexdigest())
print("image_digest", payload["image_digest"])
print("model_lock_sha256", payload["model_lock_sha256"])
PY'
```

## 6. 本地验收命令

阶段 B 专项测试：

```bash
uv run pytest \
  tests/test_retrievers.py \
  tests/test_reranking_pipeline.py \
  tests/test_query_type_resolver.py \
  tests/test_token_budget.py \
  tests/test_chunk_store.py \
  tests/test_context_assembler.py \
  tests/test_chunking_evaluation.py -v
```

全量测试：

```bash
uv run pytest
```

阶段验收：

```bash
uv run python -m bgpkb.pipeline.run_stage_acceptance --stage stage_b_hierarchical_retrieval_v1
```

注意：阶段验收脚本会刷新 `data/reports/gates/stage_acceptance_report.md` 和 `data/derived/datasets/stage_acceptance_results.jsonl`；只做复核时，运行后需检查是否产生预期外 diff。

## 7. 降级边界

- embedding 私有服务不可用时，可按 `metadata/config/rag_retrieval.yaml` 显式切换到外部 API provider。
- reranker 私有服务不可用时，可按配置使用 API fallback；若调用方声明必须使用模型，则失败直接报错。
- `auto` query type 的 DeepSeek 分类失败时，回退到可审计规则，最终兜底 `fact`。
- `global` 摘要失败时，不生成模型摘要，改用多 section 原文片段。
- CI 和结构门禁不依赖 GPU、DeepSeek 或外部 API。

## 8. 已知维护注意事项

- 当前 release 的 `release_manifest.json` 与 release ID 哈希一致，但 app 文件清单包含 `__pycache__/*.pyc`。这不影响运行；后续发布卫生应排除 `__pycache__`，让不可变 manifest 只覆盖源码、配置、模型 lock 和镜像 digest。
- `src/bgpkb.egg-info/` 是本地 `uv`/editable install 生成物，不属于源码交付物；若出现未跟踪状态，应删除或加入 `.gitignore`。
- GPU 2/3 是当前 retrieval 服务使用卡；每次重新部署前仍需用 `nvidia-smi` 实时检查，不得把历史空闲状态写成永久假设。
- GPU 0 当前可能被其他任务占用；GPU 1 是 Docling 默认计算路由，不由 retrieval 自动使用。
