# 历史文档映射

下表记录本次文档收敛前的主要内容去向。删除的文件仍可通过冻结 tag `archive/pre-repository-consolidation-20260713` 和 Git 历史追溯。

| 原内容 | 权威去向 |
| --- | --- |
| `bgp_knowledge_base/README.md`、`目录介绍.md`、根 `context.md` | 根 README、架构、数据与制品、里程碑 |
| `docs/governance/*`、`docs/rules/*` | 工程治理、数据与制品、ADR |
| `docs/operations/remote_server_operations_v1.md` | 运维与部署 |
| `docs/operations/docling_private_runtime_v1.md` | 运维与部署、数据与制品 |
| `docs/operations/cleaning_v2_gold_annotation_guide.md` | 归档 OpenSpec `docling-private-cleaning-v2` |
| `docs/projects/chat_frontend_*` | 里程碑、CHANGELOG、Git 历史 |
| `docs/roadmap/industry_alignment_improvement_plan_v1.md` | 架构、里程碑、活动 OpenSpec |
| `docs/stages/docling_private_cleaning_v2.md` | 归档 OpenSpec `docling-private-cleaning-v2` |
| `docs/stages/phase_a_corpus_profiling_v1.md` | 归档 OpenSpec `phase-a-corpus-profiling` |
| `docs/stages/phase_5_standard_exports_v1.md` | 归档 OpenSpec `phase-5-standard-exports` |
| 其他阶段 3.5/4.x/阶段 B 文档 | 架构、里程碑、CHANGELOG、对应代码测试与 Git 历史 |

## 退役远端分支归档

2026-07-13 将含旧语料、索引和生成数据的远端分支迁出普通 Git 引用。完整历史保存在服务器制品库：

- 路径：`/srv/bgpkb/artifacts/git-archives/bgpkb-retired-git-refs-20260713.bundle`
- SHA-256：`2c35a83dcb6d0816e7f19ca77718eb4d7f957251e78200ade289f74e048910c5`
- 校验：`git bundle verify bgpkb-retired-git-refs-20260713.bundle`

| 原远端分支 | 最后提交 |
| --- | --- |
| `archive/pre-artifact-main-20260710` | `f1033dd8edccd7780a31d43b8da6eaf25d095bb6` |
| `backup/main-before-93a4c97` | `f1033dd8edccd7780a31d43b8da6eaf25d095bb6` |
| `backup/main-f1033dd` | `f1033dd8edccd7780a31d43b8da6eaf25d095bb6` |
| `codex/phase-4-1-rag-api` | `dc1fa85d88ff64c85b1df8180ab96c7e09841019` |
| `codex/phase-4-2-deepseek-smoke` | `5a88dfbdc6d990ae6d2319f1d506c085978f0a7a` |
| `codex/phase-4-3-rag-eval` | `43be4f1782fc7cf2cac2631c631e97b8dfdf6244` |
| `codex/phase-4-4-deepseek-eval-analysis` | `558cd19c1274b9017f14f91fbeb20600e187492c` |
| `codex/phase-4-5-bge-m3-hybrid` | `5f9e65900514202ddf549da48b424541b8fc15d1` |
| `codex/phase-4-5-docs` | `a01d5d2c98f1dde3345b42eababc02b44348260c` |
| `rag-progress-streaming` | `41339e299731786006bc3eee062a211bc91e6388` |

需要追溯时，先在服务器核对 SHA-256，再用 `git clone bgpkb-retired-git-refs-20260713.bundle <目录>` 建立隔离副本；不得把其中的大文件历史重新推回产品仓库。
