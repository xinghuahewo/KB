## ADDED Requirements

### Requirement: 主数据流水线公开五个产品阶段
系统 SHALL 对外提供 source-ingest、canonicalize、semantic-build、publish-index、verify-release 五个阶段；每个阶段 MUST 声明输入 manifests、输出 manifest、依赖、配置版本和成功标准，人工治理报告生成器不得作为大量平级生产阶段暴露。

#### Scenario: 操作者执行完整构建
- **WHEN** 从已登记来源创建候选 release
- **THEN** 编排器 SHALL 按五阶段依赖顺序运行，并在报告中保留阶段内部子任务和耗时

### Requirement: 阶段可恢复、幂等且不写当前 release
每个阶段 SHALL 使用输入与配置指纹复用已校验输出，支持从首个未完成阶段继续；所有写入 MUST 位于候选工作区，直到 verify-release 和人工切换完成前不得修改 current/previous 指针或当前 release 内容。

#### Scenario: embedding 阶段中途终止
- **WHEN** 操作者以相同指纹继续完整流水线
- **THEN** 编排器 SHALL 复用前三阶段和已完成 embedding checkpoints，从未完成批次继续

#### Scenario: 候选构建失败
- **WHEN** 任一阶段返回非零
- **THEN** 后续阶段 SHALL 停止，current 和 previous SHALL 保持不变，失败诊断 SHALL 保存在候选工作区

### Requirement: publish-index 生成完整一致的服务制品
publish-index MUST 在一个阶段内完成 catalogs、serving/governance bundle、FTS、embedding JSONL、快向量 matrix/metadata/manifest 和 artifact manifest；阶段成功要求所有子制品完成跨 ID 和 hash 闭包校验。

#### Scenario: 快索引构建未执行
- **WHEN** 其他发布文件已生成但快索引三件套缺失
- **THEN** publish-index MUST 失败，不得把补跑责任留给部署操作者

### Requirement: 完整重建按受控顺序形成新 release
当 chunk、retrieval contract 或 serving schema 发生不兼容变化时，系统 MUST 从冻结 source snapshot 在新候选目录全量派生，不得原地修改旧 release；重建顺序 SHALL 为 snapshot、canonical、chunk/governance、retrieval document、database/catalog、embedding、fast index、评测、manifest。

#### Scenario: SemanticChunk 版本升级
- **WHEN** chunker version 从 v2 变为 v3
- **THEN** 系统 SHALL 创建新 release id 并重新验证全部下游制品，旧 release SHALL 保持可回滚

### Requirement: 发布和回滚以代码/制品对为单位
发布切换 MUST 绑定代码 generation、前端构建、artifact release id 和 SHA256SUMS；回滚 MUST 同时恢复上一代码 generation 与 previous artifact，系统 MUST 拒绝未验证的跨版本组合。

#### Scenario: 新代码 canary 失败
- **WHEN** 候选代码和制品尚未切换 current
- **THEN** 操作者 SHALL 能停止 canary 而不影响线上进程和指针

#### Scenario: 切换后出现严重回归
- **WHEN** 操作者执行已验证回滚命令
- **THEN** 系统 SHALL 原子恢复上一代码/制品对并运行健康与典型问答检查，不得重建历史 release
