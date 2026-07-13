# Corpus v2 Migration 规格

## Purpose

本规格定义现有语料在不覆盖 v1 的前提下并行迁移到 v2 的完整流程，涵盖逐文档差异核验、确定性门禁、高风险人工验收、原子发布切换以及经过验证的回滚能力。

## Requirements

### Requirement: 系统并行生成完整 v2 语料
系统 SHALL 对当前 54 篇语料生成 parsed v2、cleaned Block v2、Markdown v2、assets v2 和 chunks v2，MUST NOT 在验收前覆盖 v1。

#### Scenario: 执行首次全量迁移
- **WHEN** 操作者运行 v2 全量批处理
- **THEN** 54 篇文档 SHALL 各自具有明确终态，v1 目录与发布指针 SHALL 保持不变

### Requirement: 系统生成逐文档 v1/v2 差异
差异 SHALL 覆盖正文、标题、section、表格、图片、chunk、来源引用和被清洗规则移除的内容。

#### Scenario: v2 正文覆盖下降
- **WHEN** v2 相对 v1 正文覆盖率低于 99.5%
- **THEN** 文档 SHALL 阻断迁移验收，除非全部差异均能归因到已批准规则

### Requirement: 全量迁移满足确定性门禁
迁移 MUST 达到 54/54 文档终态、Schema 错误 0、不可追溯 Block 0、空正文 0、替换字符 0、重复 ID 0、未审核 fallback 发布数 0，并 SHALL 通过重复运行稳定性检查。

#### Scenario: 任一硬门禁失败
- **WHEN** 全量结果存在硬门禁问题
- **THEN** 系统 MUST NOT 切换 v2 发布指针，并 SHALL 输出问题文档与修复建议

### Requirement: 高风险人工验收达到门槛
系统 SHALL 从全量结果选择约 12 篇复杂 PDF、扫描页、表格、RFC、HTML 和超长文档建立人工验收集；标题层级 F1 MUST 不低于 95%，阅读顺序准确率 MUST 不低于 98%，表格结构准确率 MUST 不低于 95%，OCR 字符错误率 MUST 不高于 2%。

#### Scenario: 人工验收指标不足
- **WHEN** 任一人工指标未达到门槛
- **THEN** 阶段验收 SHALL 失败，且发布指针 MUST 保持 v1

### Requirement: 发布切换原子且可回滚
全部门禁通过后，系统 SHALL 原子更新版本化发布指针到 v2，并 SHALL 保留 v1 manifest、数据和验证过的回滚命令。

#### Scenario: v2 切换成功
- **WHEN** 阶段验收通过且操作者显式执行切换
- **THEN** 下游 SHALL 从 approved cleaned Block v2 派生，并生成包含版本和输入快照的新发布 manifest

#### Scenario: 切换后需要回滚
- **WHEN** 操作者执行已验证回滚命令
- **THEN** 系统 SHALL 恢复 v1 指针、重建 manifest，并保留 v2 诊断证据
