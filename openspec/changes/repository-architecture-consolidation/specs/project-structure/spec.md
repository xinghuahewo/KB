## ADDED Requirements

### Requirement: 仓库采用稳定的一级目录
仓库 MUST 使用 `backend/`、`frontend/`、`infra/`、`artifacts/`、`scripts/`、`docs/` 和 `openspec/` 表达长期职责，并 MUST 不在根目录保留重复应用入口或运行构建产物。

#### Scenario: 干净克隆展示唯一项目入口
- **WHEN** 维护者克隆并列出仓库一级目录
- **THEN** 后端、前端、基础设施、制品元数据、脚本、文档和规格各自只有一个明确入口

### Requirement: Python 工程保持模块化单体
后端 MUST 保持 `bgpkb` Python 包名，并 MUST 按 domain、ingestion、indexing、retrieval、publishing、workflows、api 和 infrastructure 划分职责。

#### Scenario: 现有调用方升级目录后继续导入
- **WHEN** 目录迁移完成且调用方执行 `import bgpkb`
- **THEN** 包名和公共导入入口保持可用，不要求调用方改用新的分发包名

### Requirement: 模块依赖方向可自动验证
系统 MUST 自动验证 domain 不依赖 I/O 或 Web 框架，api 不直接读取散落制品文件，workflows 只负责编排，并 MUST 在发现反向依赖时使 CI 失败。

#### Scenario: 非法反向依赖进入提交
- **WHEN** api 模块直接导入数据目录遍历实现或 domain 导入 FastAPI
- **THEN** 导入边界测试失败并指出违规模块关系

### Requirement: 目录迁移提供限期兼容
部署迁移 MUST 为旧后端和前端绝对路径提供显式兼容映射，并 MUST 记录移除条件，不得永久维护两套真实源码目录。

#### Scenario: 新目录首次部署
- **WHEN** 服务器切换到新的仓库目录结构
- **THEN** 现有 screen 启动命令可通过兼容映射继续运行，且只有新目录保存真实文件
