## ADDED Requirements

### Requirement: 系统生成跨阶段文档画像
系统 SHALL 以 parsed、cleaned 和 chunks 三处逻辑 `doc_id` 的并集生成按标识稳定排序的文档级画像，并 SHALL 显式记录每个阶段是否存在。

#### Scenario: 三层标识不完全重合
- **WHEN** parsed、cleaned 和 chunks 包含不完全相同的文档标识
- **THEN** 输出 SHALL 包含三处标识的并集，且每条记录 SHALL 正确标记阶段存在性

#### Scenario: 排除说明文件并保留正式种子
- **WHEN** 输入包含配置排除的 README 和正式 seed/context 语料
- **THEN** README SHALL 不进入画像，seed/context 文档 SHALL 保留

### Requirement: 系统计算可审计的语料指标
系统 SHALL 从现有语料计算字符数、段落数、section 数、chunk 数、平均段落长度、替换字符、疑似表格行、异常符号、空标题和重复标题指标，阈值 SHALL 来自版本化 YAML 配置。

#### Scenario: 文档包含结构和字符异常
- **WHEN** cleaned 文档包含表格样式行、替换字符、异常符号或标题问题
- **THEN** 画像 SHALL 输出对应计数、布尔信号和问题代码，不得只在自由文本报告中描述

### Requirement: 系统区分阻断问题与非阻断告警
系统 MUST 仅将空 cleaned 正文、`U+FFFD` 替换字符、重复 `doc_id` 和孤儿 chunk 文档列为确定性阻断问题；长度、表格、异常符号、标题及阶段缺失 SHALL 作为非阻断告警。

#### Scenario: 发现确定性阻断问题
- **WHEN** 任一文档命中四类确定性阻断问题
- **THEN** 系统 SHALL 写出完整画像与中文报告，并 SHALL 以非零状态退出

#### Scenario: 仅发现启发式异常
- **WHEN** 文档只命中超短、超长、表格、异常符号、标题或阶段缺失告警
- **THEN** 系统 SHALL 记录告警且 SHALL 保持成功退出

### Requirement: 画像输出保持确定性与原子性
系统 SHALL 按稳定顺序和稳定 JSON 序列化写入画像，并 SHALL 使用原子替换避免半写输出。

#### Scenario: 相同输入重复运行
- **WHEN** 使用相同配置和输入连续运行画像命令
- **THEN** 除明确允许的运行时间字段外，数据集内容 SHALL 完全一致

#### Scenario: 输入无法解析
- **WHEN** 输入 JSON 或 JSONL 无法解析到可信画像
- **THEN** 系统 SHALL 返回失败且 MUST NOT 用半写内容覆盖既有输出

### Requirement: 画像接入治理与阶段验收
系统 SHALL 在报告策略、制品 producer、质量检查、主流水线和阶段 A gate 中登记画像数据集、报告和命令。

#### Scenario: 离线运行主流水线
- **WHEN** 操作者不配置任何模型密钥运行确定性主流水线
- **THEN** 流水线 SHALL 生成语料画像、通过结构校验，并 SHALL 不访问网络

#### Scenario: 运行阶段 A 验收
- **WHEN** 操作者执行阶段 A 验收 gate
- **THEN** 报告 SHALL 给出交付物、命令、报告检查、实际新增能力和剩余人工事项
