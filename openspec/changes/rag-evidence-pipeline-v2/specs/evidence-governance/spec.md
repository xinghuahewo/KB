## ADDED Requirements

### Requirement: 系统维护正交的证据治理状态
系统 MUST 分别维护 parse_status、content_quality_status、source_trust_status、semantic_review_status 和 retrieval_eligibility，字段 SHALL 使用独立枚举、规则版本和来源；任何单一 approved 状态不得隐式提升其他维度。

#### Scenario: 文档解析和清洗通过但来源尚未审核
- **WHEN** parse_status 与 content_quality_status 均为 approved，而 source_trust_status 为 pending
- **THEN** 系统 MUST 保持来源可信状态为 pending，并按 eligibility policy 决定是否仅能 eligible_with_caution

### Requirement: 检索资格由确定性策略派生
retrieval_eligibility MUST 由版本化规则根据用途、前置状态、来源类型和隔离信号确定，结果 SHALL 包含 rule id 和解释；LLM、embedding 或 reranker 不得直接修改资格。

#### Scenario: chunk 来源追溯不完整
- **WHEN** chunk 缺少有效 source snapshot 或 source_ref
- **THEN** eligibility policy MUST 将其设为 ineligible 并阻断进入 serving bundle

#### Scenario: 中等可信来源内容质量合格
- **WHEN** 来源满足配置允许的中等可信规则且其他硬门禁通过
- **THEN** 策略 MAY 设为 eligible_with_caution，并在 evidence 对象中显式暴露该状态

### Requirement: 旧状态迁移必须保守
迁移器 SHALL 把旧 chunk/block approved 仅解释为已通过相应结构或内容质量检查；旧来源 trust_level 与 review_status SHALL 分别迁移，缺失信息 MUST 映射为 pending/unknown，旧批准不得自动变成 semantic approval。

#### Scenario: 旧 chunk 为 approved 而来源为 pending
- **WHEN** 系统迁移该记录
- **THEN** content_quality_status MAY 为 approved，但 source_trust_status 与 semantic_review_status MUST 保持 pending/unknown

### Requirement: 状态变化可审计且不可由生成流程越权
每次治理状态变化 SHALL 记录对象 ID、旧值、新值、规则或人工决定、输入指纹、操作者/系统身份和时间；模型生成内容只能形成 pending candidate，不得形成 approved 或 eligible 决定。

#### Scenario: LLM 输出批准状态
- **WHEN** 候选响应尝试设置 source trust、semantic approval 或 retrieval eligibility
- **THEN** 系统 MUST 拒绝越权字段、记录校验错误并保持正式状态不变
