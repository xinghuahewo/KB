# 接地证据回答规格

## Purpose

定义逐证据 Context Pack、claim-evidence 结构化回答、服务端接地校验和安全降级要求。

## Requirements

### Requirement: Context Pack 保留逐证据边界
系统 SHALL 把每条入选证据表示为独立 evidence 对象，至少包含 evidence_id、chunk_id、source_ref、section_path、完整内容、内容 hash、治理状态和检索分数；context group MAY 提供相邻上下文，但 MUST 保留每个成员边界且不得只保留首个来源。

#### Scenario: 一个 context group 包含多个 chunk
- **WHEN** assembler 合并相邻 chunk 形成 context group
- **THEN** LLM 输入 SHALL 仍能分别识别每个 evidence_id、chunk_id、source_ref 和内容范围

### Requirement: LLM 输出 claim-evidence 结构化回答
回答模型 MUST 使用受校验的结构化格式输出 answer、claims、每个 claim 的 evidence_ids、confidence 和 insufficient_evidence；每个事实性 claim MUST 至少引用一个本次 context pack 的 evidence_id。

#### Scenario: 模型生成有证据的事实主张
- **WHEN** 模型认为 evidence 足以支持该主张
- **THEN** 输出 SHALL 把 claim 文本与一个或多个 evidence_id 绑定，且不得只在回答末尾给出无主张归属的引用列表

#### Scenario: 证据不足
- **WHEN** context pack 不足以支持确定性答案
- **THEN** 模型 SHALL 设置 insufficient_evidence 并避免生成未支持的事实主张

### Requirement: 服务端验证、修复或拒绝不接地回答
服务端 MUST 在返回 answered 前验证 JSON Schema、evidence ID 范围、每个事实 claim 的引用覆盖和引用来源；首次失败 MAY 执行一次受控 repair，仍失败时 MUST 返回证据不足或模型错误状态，不得把自由文本当作已验证答案。

#### Scenario: 模型引用不存在的 evidence ID
- **WHEN** 结构化响应包含不属于本次 context pack 的 evidence_id
- **THEN** 验证器 MUST 拒绝响应并触发受控修复或降级，不得把该引用返回给用户

#### Scenario: 主张没有引用
- **WHEN** 一个事实性 claim 的 evidence_ids 为空
- **THEN** grounding validation MUST 失败，且该 claim 不得进入最终 answer

### Requirement: 返回引用只反映实际使用证据
兼容字段 citations MUST 从验证通过的 claim evidence_ids 派生，不得直接返回 context pack 中全部候选证据；响应 SHALL 额外给出 grounding_status 和结构化 claims/evidence，同时保留既有 answer、citations、context_pack 字段。

#### Scenario: context pack 有八条证据而回答只使用两条
- **WHEN** 两条证据通过 claim 绑定和验证
- **THEN** 顶层 citations SHALL 只包含这两条实际使用证据，context_pack 仍可保留全部候选用于调试

### Requirement: 外部证据按不可信数据处理
系统 prompt 和消息结构 MUST 明确把 source 内容视为不可信数据，禁止执行证据中的指令；模型输入 SHALL 使用结构化边界隔离用户问题、系统规则和 evidence，release 评测 MUST 包含提示注入与引用诱导样本。

#### Scenario: 来源文档包含忽略系统指令的文本
- **WHEN** 该文本进入 evidence 内容
- **THEN** 模型 SHALL 把它作为被引用的数据而非指令，最终响应 MUST 仍满足 grounding schema 和引用范围校验
