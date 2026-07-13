# 变更记录

## 未发布

- 建立外置运行制品注册表、完整性校验和隔离 artifact gate。
- 增加 `BGPKB_DATA_DIR` 与可注入检索数据边界。
- 将默认测试与真实制品测试分层，补充无制品 OpenAPI 契约门禁。
- 建立根 Makefile、统一 CI、仓库卫生检查和中文权威文档。
- 将仓库收敛为 `backend/`、`frontend/`、`infra/` 的模块化单体结构。
- 将 Python 在线服务与离线实现迁入 domain、infrastructure、ingestion、indexing、publishing、retrieval、api 和 workflows，保留限期兼容入口。
- 增加独立代码/制品版本状态、原子切换、旧路径映射和联合回滚脚本。

## 2026-07-10

- 完成阶段 B 层级检索、BGE-M3 混合检索与 FastAPI 真实问答验收。
- 完成对话前端证据工作台设计调整。
- 将知识库运行数据迁出普通 Git，服务器 release `2026-07-10-93a4c97` 成为当前制品。

## 2026-07-04

- 完成 Docling 私有离线清洗 v2 镜像、模型哈希、SBOM、许可证和 GPU 1 断网验收。
