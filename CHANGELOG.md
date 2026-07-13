# 变更记录

## 未发布

暂无。

## 2026-07-13

- 建立外置运行制品注册表、完整性校验和隔离 artifact gate。
- 增加 `BGPKB_DATA_DIR` 与可注入检索数据边界。
- 将默认测试与真实制品测试分层，补充无制品 OpenAPI 契约门禁。
- 建立根 Makefile、统一 CI、仓库卫生检查和中文权威文档。
- 将仓库收敛为 `backend/`、`frontend/`、`infra/` 的模块化单体结构。
- 将 Python 在线服务与离线实现迁入 domain、infrastructure、ingestion、indexing、publishing、retrieval、api 和 workflows，保留限期兼容入口。
- 增加独立代码/制品版本状态、原子切换、旧路径映射和联合回滚脚本。
- 通过受保护的 PR #1 完成仓库架构整理，通过 PR #2 修复移动端长回答横向裁切，并部署到 `10.99.8.28`。

正式发布追溯信息：

- Git tag：`repository-architecture-consolidation-20260713`
- 代码提交：`a7762401cc48864cd3da63b887c3251501e14f1c`
- 前端静态构建 SHA-256：`1a21558d6087173b439209383c11ef09acf048f8ed2f191450f8afafd0b1626f`
- 制品 release id：`2026-07-10-93a4c97`
- 制品 `SHA256SUMS` SHA-256：`97400ef06e8ef20c3d363918b79d2540d4e513e6fe5be4ea9e84e9c870f9a04b`
- 首次部署时间：`2026-07-13T11:24:34Z`
- 验收结果：前端、FastAPI、embedding、reranker 健康；真实问答为 `answered / complete / complete / local_http / degraded=false`；390×844、768×1024、1024×720、1280×720 浏览器验收无横向溢出。
- 回滚点：代码 `e621280ac14960028b4e66b2ee896032fcf4595b`，制品仍为 `2026-07-10-93a4c97`。联合回滚与恢复于 `2026-07-13T11:47:05Z` 开始，3 秒回滚、3 秒恢复，总计 6 秒；恢复后代码为 `a7762401cc48864cd3da63b887c3251501e14f1c`，无需重建制品。

## 2026-07-10

- 完成阶段 B 层级检索、BGE-M3 混合检索与 FastAPI 真实问答验收。
- 完成对话前端证据工作台设计调整。
- 将知识库运行数据迁出普通 Git，服务器 release `2026-07-10-93a4c97` 成为当前制品。

## 2026-07-04

- 完成 Docling 私有离线清洗 v2 镜像、模型哈希、SBOM、许可证和 GPU 1 断网验收。
