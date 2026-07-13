## ADDED Requirements

### Requirement: 活动文档集合保持精简
项目 MUST 只保留根 README、架构、数据与制品、运维、治理、里程碑、CHANGELOG、ADR 和必要的代理约束文档作为活动文档入口。

#### Scenario: 维护者查找系统事实
- **WHEN** 维护者从根 README 进入文档
- **THEN** 可在一次索引跳转内找到架构、部署、数据制品和治理的唯一权威说明

### Requirement: 阶段文档先提炼后移除
阶段、项目和路线图文档中的长期有效决策 MUST 在删除前映射到架构文档、ADR 或 milestones；项目 MUST 不创建新的大规模 `docs/archive/`。

#### Scenario: 删除阶段实现计划
- **WHEN** 文档整理任务准备删除某个阶段计划
- **THEN** 评审清单标明其长期决策的目标文档或确认其仅为可由 Git 历史追溯的过程记录

### Requirement: 关键决策使用 ADR
影响数据边界、模型运行、检索架构、API/前端交付或部署方式的长期技术选择 MUST 使用编号 ADR 记录背景、决定、替代方案和后果。

#### Scenario: 变更制品存储策略
- **WHEN** 项目决定从服务器制品库迁移到其他存储
- **THEN** 新 ADR 记录迁移动机、兼容策略和对旧决定的替代关系

### Requirement: 版本可由四元组追溯
每次正式发布 MUST 能由 Git tag、提交号、制品 release id 和制品清单 SHA-256 唯一追溯。

#### Scenario: 调查历史线上版本
- **WHEN** 运维者在 milestones 或发布记录中选择一个版本
- **THEN** 可定位对应代码提交、制品目录和完整性清单

### Requirement: 已完成 OpenSpec 变更被归档
状态为 complete 的 OpenSpec change MUST 在整理过程中归档，并 MUST 不继续显示为活动变更。

#### Scenario: 查看活动 OpenSpec 列表
- **WHEN** 三个既有完成变更完成归档后运行 `openspec list`
- **THEN** 活动列表只包含尚未完成或当前实施中的变更
