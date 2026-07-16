## ADDED Requirements

### Requirement: 知识抽取只生成待审核候选
确定性规则或 LLM 从证据抽取的实体、关系和事实 MUST 写入独立候选集合，状态固定为 pending_review；抽取器不得直接创建 approved 记录、修改 serving bundle 或改变任何治理状态。

#### Scenario: 模型返回 approved 实体
- **WHEN** 抽取响应包含 approved、trusted 或 eligible 等越权状态
- **THEN** 系统 MUST 拒绝越权字段、记录校验错误并保持正式知识数据不变

### Requirement: 每条候选绑定完整证据和模型指纹
有效候选 MUST 包含稳定 candidate_id、类型化 payload、一个或多个本次输入的 evidence_id、source_refs、输入指纹、provider、model revision、prompt version、置信度和理由；任一证据或模型输入变化 SHALL 生成新指纹，旧人工决定不得自动复用。

#### Scenario: 候选没有 evidence ID
- **WHEN** 抽取器返回无法映射到输入 Evidence 对象的候选
- **THEN** 候选 MUST 判为 invalid 并不得进入人工审核队列

#### Scenario: 相同实体使用了新证据
- **WHEN** 名称和类型相同但 evidence IDs 或 evidence 内容 hash 改变
- **THEN** 系统 SHALL 生成新的输入指纹和 candidate_id，并要求重新审核

### Requirement: 模型抽取显式启用且不阻断确定性构建
默认五阶段构建 MUST 不调用知识抽取 LLM；只有显式选择 provider 且满足模型配置时才能生成候选，缺少密钥或模型不可用 SHALL 记录 skipped 并不得覆盖既有候选，也不得阻断不依赖候选的确定性 serving release。

#### Scenario: 未配置模型密钥
- **WHEN** 操作者没有显式启用知识抽取 provider
- **THEN** 主流水线 SHALL 完成确定性阶段且不发出 LLM 请求

### Requirement: 候选只有经审计和显式应用才能生效
知识候选 SHALL 复用人工决策校验、冲突检测、审核人/时间和 dry-run preview 边界；只有审计通过且操作者显式执行 apply 的 approved candidate 才能成为下一候选 release 的知识输入。

#### Scenario: 人工批准存在冲突关系
- **WHEN** 同一实体对存在互斥的关系候选同时获批
- **THEN** 审计 MUST 阻断冲突组，显式 apply 不得任意选择一条写入正式集合
