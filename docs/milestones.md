# 项目里程碑

## 已完成

- 建立 BGP 标准、论文、数据源、案例和证据的结构化知识体系。
- 完成 Docling 私有离线清洗 v2，并在 GPU 1、断网条件下验收。
- 完成语料质量画像、层级 chunk、BGE-M3 向量索引和混合检索。
- 完成 FastAPI 问答、DeepSeek 回答、reranker、流式进度和证据工作台。
- 完成 JSON-LD、PROV-O、SKOS/Turtle 轻量标准出口。
- 完成前端“技术编辑式网络运维工作台”设计调整。
- 将约 2 GB 运行数据迁出普通 Git，建立不可变 release 与校验清单。
- 完成仓库一级目录、Python 模块化单体边界、权威文档与发布/回滚入口整理。
- 完成 `repository-architecture-consolidation-20260713` 正式发布、远端部署、四档浏览器验收和联合回滚演练。

## 当前阶段

`repository-architecture-consolidation` 已完成首个正式发布与远端部署。当前正在实施 `rag-evidence-pipeline-v2`：已完成本地候选隔离、publish-index 制品闭包和 verify-release 统一门禁；尚未执行生产候选全量重建、canary、成对切换或回滚演练。

## 后续

- 在稳定发布周期后移除旧服务器路径兼容。
- 从冻结 snapshots 执行五阶段生产候选全量重建，并完成真实检索/回答与目标服务器性能门禁。
- 根据使用量再评估从 screen 迁移到 systemd/容器编排；当前不提前引入。
- 继续提升检索评测集、人工复核闭环和增量发布能力。
