## Why

BGP 知识库已完成主要开发阶段，但仓库仍混有阶段性脚本、重复文档、失效 CI 路径和隐式运行数据依赖，维护入口不清晰。现在需要在功能冻结窗口内完成一次可追溯、分批实施的架构整理，为后续维护、发布、回滚和再次开发建立稳定基线。

## What Changes

- **BREAKING**：将仓库一级目录统一为 `backend/`、`frontend/`、`infra/`、`artifacts/`、`scripts/`、`docs/` 和 `openspec/`，并为旧部署路径提供限期兼容映射。
- 将 Python 工程整理为模块化单体，明确 domain、ingestion、indexing、retrieval、publishing、workflows、api 和 infrastructure 的单向依赖边界。
- 将离线数据生产与在线只读服务分离；运行数据通过显式制品版本和 `BGPKB_DATA_DIR` 提供，不再隐式依赖仓库内完整 `data/`。
- 建立统一的 bootstrap、test、build、artifact verification、release 和 deploy 入口，修复 CI 的失效路径并覆盖前后端与制品门禁。
- 将长期文档收敛为架构、数据与制品、运维、治理、里程碑和少量 ADR；阶段文档在信息提炼后从活动文档树移除。
- 归档已完成的 OpenSpec change，并通过 Git tag、提交号、制品版本与 SHA-256 保留追溯链。
- 不改变现有 FastAPI 对外 API 契约、前端问答语义、知识库发布规则或当前 screen 部署方式。

## Capabilities

### New Capabilities

- `project-structure`: 定义仓库一级目录、Python 模块边界、依赖方向和旧路径兼容期要求。
- `artifact-runtime-contract`: 定义外置制品版本、校验、挂载、运行数据根目录和无制品开发环境行为。
- `documentation-traceability`: 定义活动文档集合、ADR、里程碑、OpenSpec 归档和历史追溯规则。
- `project-workflows`: 定义统一命令入口、测试分层、CI 门禁、发布与部署/回滚工作流。

### Modified Capabilities

无。现有功能行为与对外契约不在本次变更中调整。

## Impact

- 影响仓库内大多数文件路径、导入边界、测试发现路径、CI 配置、部署脚本和文档链接。
- Python 包名 `bgpkb`、FastAPI API 契约、Next.js 页面行为和制品内容保持兼容。
- 远端运行目录在迁移期通过符号链接或部署映射继续支持 `/home/wbt/DB/bgp_knowledge_base` 与 `/home/wbt/DB/chat_frontend`。
- 服务器制品库继续使用 `/srv/bgpkb/artifacts/releases/<release-id>/`，制品本体不重新进入普通 Git 历史。
- 实施必须拆分为可独立验证和回滚的多个 PR，不允许一次性提交不可审查的目录重排与逻辑重构。
