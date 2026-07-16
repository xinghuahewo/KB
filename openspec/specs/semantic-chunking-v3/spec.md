# 语义切块 v3 规格

## Purpose

定义 RFC、HTML、PDF/表格和 OpenAPI 等文档类型专用的语义切块策略，覆盖短块合并或隔离、同源与跨来源重复控制、稳定 chunk 身份、旧新迁移以及阻断无效候选的生产质量门禁。

## Requirements

### Requirement: 系统按文档类型选择语义切块策略
系统 MUST 根据受控 document profile 为 RFC/普通正文、HTML、PDF/论文/表格和 OpenAPI/YAML 选择独立策略；每个策略 SHALL 以语义单元而不是字符、标点或孤立标量为基本 chunk，并记录 chunker name、version 和配置指纹。

#### Scenario: 处理 OpenAPI operation
- **WHEN** Canonical Document 包含一个 method + path operation 及其参数和响应
- **THEN** 系统 SHALL 将 endpoint、method、描述和必要参数/响应上下文组合为一个或少量有边界的语义 chunk，不得为每个标量生成独立 chunk

#### Scenario: 处理 RFC 小节
- **WHEN** RFC 小节包含多个连续短段落
- **THEN** 系统 SHALL 在不跨越不兼容标题边界的前提下合并为满足目标 token 范围的 chunk，并保留完整 section_path

### Requirement: 短块必须合并、允许或隔离
可检索 chunk 少于配置的最小语义长度时 MUST 在同 section 和来源范围内尝试与 sibling 合并；无法合并的 chunk 只有命中版本化 allowlist 才能进入检索，否则 SHALL 进入隔离清单并说明原因。

#### Scenario: Canonical block 只包含标点或短代码
- **WHEN** block 内容为孤立标点、括号、分隔符或未登记的短代码
- **THEN** 系统 MUST NOT 生成 eligible chunk，并 SHALL 在隔离清单中关联原 block_id

#### Scenario: 短协议术语有独立定义
- **WHEN** 短内容命中 allowlist 且其 section 提供完整定义上下文
- **THEN** 系统 MAY 生成 eligible chunk，但 SHALL 把定义上下文纳入 retrieval_text 并记录 allowlist rule id

### Requirement: 系统控制精确重复与近重复
系统 MUST 对规范化内容计算 exact hash，对同源精确重复自动折叠；近重复策略 SHALL 记录算法、阈值和决定，跨来源近重复 MUST 保留独立证据身份并在检索展示阶段抑制重复，不得无审计地删除。

#### Scenario: OpenAPI 模板描述在同一来源重复出现
- **WHEN** 多个候选 chunk 的规范化内容和语义上下文 hash 相同
- **THEN** 系统 SHALL 保留一个 canonical chunk、记录全部 source block refs，并将其余候选标记为 deduplicated

#### Scenario: 两个权威来源表达相同事实
- **WHEN** 跨来源 chunk 被判定为近重复
- **THEN** 系统 SHALL 保留两个 chunk 及各自来源，只在单次检索结果中按多样性规则减少重复展示

### Requirement: SemanticChunk v3 身份稳定且可迁移
chunk ID MUST 由 source snapshot、规范化 section 路径、source block hashes、chunker version 和内容 hash 确定；相同输入和配置重跑 SHALL 产生相同 ID。迁移 SHALL 输出旧新 chunk 映射，只有内容和来源可证明等价时才能建立映射。

#### Scenario: 相同 snapshot 重复切块
- **WHEN** Canonical Document、chunker version 和配置完全相同
- **THEN** chunk 内容、顺序、ID 和非时间字段 SHALL 完全一致

#### Scenario: 旧 chunk 被新的合并策略取代
- **WHEN** 多个旧 chunk 合并为一个新语义 chunk
- **THEN** 迁移清单 SHALL 记录 replaced/merged 关系，不得伪装成一对一等价映射

### Requirement: 生产 chunk 质量门禁必须阻断无效候选
系统 SHALL 对 eligible chunk 的空内容、非 allowlist 超短内容、exact duplicate、来源追溯、token 范围、单一来源集中度和隔离原因生成机器可读指标；任何硬阈值失败 MUST 以非零状态阻断 publish-index。

#### Scenario: 候选语料仍含大量两字符碎片
- **WHEN** 非 allowlist eligible chunk 少于 20 字符的数量大于零
- **THEN** 语义构建 gate MUST 失败并列出 doc_id、chunk_id、内容和产生策略
