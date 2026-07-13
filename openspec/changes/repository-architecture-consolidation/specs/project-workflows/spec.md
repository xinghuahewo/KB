## ADDED Requirements

### Requirement: 根目录提供统一工作流入口
项目 MUST 提供 bootstrap、test、test-artifacts、build、verify-artifacts、release、deploy 和 rollback 的稳定根命令，并 MUST 将具体逻辑放在可测试脚本中。

#### Scenario: 新维护者建立开发环境
- **WHEN** 维护者在干净克隆中运行统一 bootstrap 与 test 入口
- **THEN** 后端和前端依赖按锁文件安装，且无制品测试可重复执行

### Requirement: CI 覆盖前后端和仓库卫生
CI MUST 验证后端单元/契约测试、前端测试与生产构建、路径有效性、API 契约、大文件门禁和文档/OpenSpec 一致性，并 MUST 不引用不存在的脚本路径。

#### Scenario: CI 配置引用失效入口
- **WHEN** 工作流调用仓库中不存在的脚本或目录
- **THEN** CI 配置验证失败并阻止合并

### Requirement: 制品门禁独立于普通 PR 测试
项目 MUST 提供可显式选择 release id 的制品集成测试入口，并 MUST 在发布或部署前执行该入口。

#### Scenario: 发布候选进入部署
- **WHEN** 发布流程准备部署代码与制品版本
- **THEN** 制品哈希、数据库完整性、检索索引和服务契约门禁全部通过后才允许切换

### Requirement: 默认 PR 测试不依赖真实运行制品
项目 MUST 将真实语料、生产 SQLite、向量索引和发布数据断言与无制品 unit/contract 测试分离；默认 PR 测试 MUST 在干净克隆中可重复通过。

#### Scenario: 新贡献者运行默认测试
- **WHEN** 新贡献者在未下载发布制品的干净克隆中运行默认 test 入口
- **THEN** 后端 unit/contract 测试、前端测试和构建完成，且输出不要求创建或下载真实运行制品

### Requirement: 发布与部署可独立回滚
代码发布和数据制品切换 MUST 分别记录当前与上一版本，并 MUST 提供单一回滚入口恢复二者后执行健康检查。

#### Scenario: 前端发布成功但问答健康检查失败
- **WHEN** 部署后的端到端健康检查未通过
- **THEN** rollback 恢复上一代码构建和制品指针，并重新验证前端、FastAPI、embedding 与 reranker 状态

### Requirement: 结构整理通过分批 PR 合入
目录与架构整理 MUST 拆分为文档、目录迁移、Python 模块化、工作流/制品四类 PR；每个 PR MUST 可单独构建、测试和回滚。

#### Scenario: 目录迁移 PR 接受评审
- **WHEN** 评审目录迁移 PR
- **THEN** 该 PR 不包含检索算法或业务行为变化，并提供旧路径兼容和完整验证证据
