## ADDED Requirements

### Requirement: 模型只生成待审核候选
系统 MUST 把 mock 或 DeepSeek 生成的语义映射记录为 `pending_review` 候选，模型不得设置批准状态或直接修改正式出口。

#### Scenario: 模型尝试越权批准
- **WHEN** 模型响应包含 approved 或其他非待审核状态
- **THEN** 系统必须拒绝该候选并记录校验错误

### Requirement: 候选必须具有证据和可审计元数据
每条有效候选 MUST 包含稳定 ID、本地项、建议标准映射、来源证据、输入指纹、置信度、理由、provider、model 和 prompt version。候选 ID 必须包含输入指纹，使证据或模型输入变化后旧批准不能复用。

#### Scenario: 缺少来源证据
- **WHEN** 模型返回的候选没有 `source_refs`
- **THEN** 系统必须将候选判定为无效且不得写入候选数据集

#### Scenario: 候选证据发生变化
- **WHEN** 本地项和建议映射相同但来源证据、输入内容或 prompt version 发生变化
- **THEN** 系统必须生成新的输入指纹和 candidate ID，旧人工决策不得适用于新候选

### Requirement: 默认离线且模型调用显式启用
默认流水线 MUST 使用离线 mock provider；DeepSeek 只有在显式选择且存在环境变量密钥时才能调用。

#### Scenario: 缺少 DeepSeek 密钥
- **WHEN** 用户显式选择 DeepSeek 但未配置 `DEEPSEEK_API_KEY`
- **THEN** 系统必须返回 skipped 状态且不得覆盖已有候选

### Requirement: 人工决策必须经过审计
系统 MUST 校验人工 CSV 中的候选 ID、提交输入指纹、决策值、重复项和审核元数据，并生成中文审计报告。审计记录必须同时保留提交指纹和当前候选指纹；只有 `ready_to_apply` 状态强制两者合法且一致。`approved` 决策必须包含审核人和合法的审核时间，坏输入仍必须能以阻塞记录进入审计产物。

#### Scenario: 审核引用未知候选
- **WHEN** 人工决策引用不存在的 candidate ID
- **THEN** 审计必须失败且禁止形成批准映射

#### Scenario: 批准缺少可归责信息
- **WHEN** approved 决策缺少 reviewer、合法 reviewed_at 或当前候选输入指纹
- **THEN** 审计必须标记为 blocked_invalid_input 且禁止写入批准映射

#### Scenario: 同一本地项存在冲突批准
- **WHEN** 同一 candidate_type 和 local_value 有多个不同 suggested_mapping 被批准
- **THEN** 审计必须把冲突组全部阻塞，不得任意选择优先映射

### Requirement: 批准映射只能显式写入
默认应用命令 MUST 只生成预览；只有显式 `--write` 才能把审计通过的 approved 候选写入批准映射集合。

#### Scenario: dry-run 不改变批准集合
- **WHEN** 用户未传入 `--write` 运行应用命令
- **THEN** 系统必须生成预览但不得创建或修改正式批准映射文件

### Requirement: 未审核候选不得影响正式出口
正式标准出口生成器 MUST 忽略 pending、rejected、needs_evidence 和无效候选。

#### Scenario: 候选尚未批准
- **WHEN** 候选数据集中存在 pending_review 映射但批准集合中不存在该项
- **THEN** 正式标准出口不得采用该候选映射
