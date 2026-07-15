## MODIFIED Requirements

### Requirement: 系统生成跨阶段文档画像
系统 SHALL 以 source snapshots、Canonical Documents、SemanticChunk v3 和 Retrieval Documents 的逻辑 source_id/doc_id 并集生成稳定排序的文档级画像，并 SHALL 显式记录每个阶段是否存在、输入 manifest hash、eligibility 数量和隔离数量；legacy parsed/chunks 只可作为迁移对照单独呈现。

#### Scenario: 四层标识不完全重合
- **WHEN** snapshot、canonical、chunk 和 retrieval document 包含不完全相同的文档标识
- **THEN** 输出 SHALL 包含四处标识的并集，且每条记录 SHALL 正确标记缺失阶段、阻断级别和上游责任阶段

#### Scenario: 排除说明文件并保留正式种子
- **WHEN** 输入包含配置排除的 README 和正式 seed/context 语料
- **THEN** README SHALL 不进入画像，正式种子 SHALL 具有登记来源或受控 internal snapshot 后保留

### Requirement: 系统计算可审计的语料指标
系统 SHALL 从 Canonical、SemanticChunk 和 Retrieval Document 计算字符/token 数、Block/section/chunk 数、chunk 长度分布、少于最小语义长度数量、空 retrieval text、精确/近重复率、单一来源集中度、隔离原因、来源追溯、替换字符、表格/代码保真和 eligibility 分布；阈值 SHALL 来自版本化配置。

#### Scenario: OpenAPI 来源产生大量碎片和重复
- **WHEN** 某来源的 eligible chunk 出现超短内容、模板重复或异常集中
- **THEN** 画像 SHALL 输出绝对数量、占比、样例、策略版本和问题代码，不得只在自由文本报告中描述

### Requirement: 系统区分阻断问题与非阻断告警
系统 MUST 将空 Canonical 正文、`U+FFFD` 替换字符、重复 ID、不可追溯 publishable Block/chunk、空 retrieval text、非 allowlist eligible 超短 chunk、超过阈值的同源精确重复和跨制品 ID 不闭合列为确定性阻断问题；长度尾部、来源集中度、近重复和启发式标题/表格异常 SHALL 默认作为告警，除非版本化策略将其提升为阻断。

#### Scenario: 发现确定性阻断问题
- **WHEN** 任一文档或全局候选命中确定性阻断问题
- **THEN** 系统 SHALL 写出完整画像与中文报告，并 SHALL 以非零状态退出

#### Scenario: 仅发现启发式异常
- **WHEN** 候选只命中来源集中、近重复、超长或其他未提升的告警
- **THEN** 系统 SHALL 记录告警和样例且 SHALL 保持画像命令成功，后续 release gate MAY 依据独立阈值继续阻断

### Requirement: 画像接入治理与阶段验收
系统 SHALL 在 semantic-build、publish-index、制品 producer、质量检查和 verify-release 中登记画像数据集、报告、配置版本和命令；生产发布 MUST 使用候选 v3 数据运行画像，不得以旧 v1/v2 报告替代。

#### Scenario: 离线运行到 semantic-build
- **WHEN** 操作者不配置模型密钥运行前三阶段
- **THEN** 流水线 SHALL 生成来源、Canonical 和 chunk/retrieval 画像，完成确定性结构与数据质量门禁且不调用 LLM

#### Scenario: 运行 verify-release
- **WHEN** 操作者验证候选 release
- **THEN** 报告 SHALL 给出全部硬门禁、阈值、实际值、失败样例、输入 manifest 和与冻结基线的变化
