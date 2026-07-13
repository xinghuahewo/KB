# Governed Cleaning Transformations 规格

## Purpose

本规格定义文档清洗转换的治理边界，通过规则分级、逐次转换追溯和原始 Block 永久保留，确保只有已批准内容能够进入下游，并明确禁止为图片生成未经证据支持的语义解释。

## Requirements

### Requirement: 清洗规则必须分级
系统 SHALL 把规则分为无损规范化、结构校正和语义性修改；只有无损规范化可以无人工介入自动批准。

#### Scenario: 执行 Unicode 和空白规范化
- **WHEN** Block 命中已登记无损规则
- **THEN** 系统 SHALL 自动应用规则并生成 transformation 记录

#### Scenario: 规则试图改写正文语义
- **WHEN** 规则属于语义性修改
- **THEN** 系统 MUST NOT 自动写入 approved cleaned Block

### Requirement: 每次清洗转换可追溯
删除、替换、合并、拆分和结构移动 MUST 记录 transformation ID、规则版本、输入输出 Block、前后值、证据、置信度和生成步骤。

#### Scenario: 移除重复页眉
- **WHEN** 结构规则移除跨页重复页眉
- **THEN** 审计记录 SHALL 指向全部原始 Block，并说明移除规则和证据

### Requirement: 原始 Block 永久保留
cleaned Block SHALL 作为原始 Block 的派生层；系统 MUST NOT 覆盖或删除作为证据的 parsed Block。

#### Scenario: 清洗结果被人工纠正
- **WHEN** 审核人修正 cleaned Block
- **THEN** 原始 Block、自动转换和人工决策 SHALL 同时可查询

### Requirement: 未批准内容不得进入下游
只有 approved cleaned Block 或满足确定性自动批准规则的 Block SHALL 进入 Markdown v2 和 chunks v2；fallback、低置信 OCR、冲突和 pending_review Block MUST 被排除。

#### Scenario: 文档包含低置信度 OCR Block
- **WHEN** OCR 置信度低于配置门槛且尚未审核
- **THEN** 该 Block SHALL 进入复核队列，且不得出现在正式 chunks v2

### Requirement: 图片不产生语义解释
系统 SHALL 保留图片资产和结构元数据，但 MUST NOT 调用视觉模型或生成图片/图表解释文本。

#### Scenario: 文档包含图表
- **WHEN** Docling 识别图表图片
- **THEN** 系统 SHALL 保存图片引用、坐标与标题，不得添加模型生成事实
