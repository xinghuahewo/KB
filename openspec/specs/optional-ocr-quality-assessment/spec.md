# 可选 OCR 质量评估规格

## Purpose

定义受预算约束的文档抽样、可替换 OCR 质量 Provider、安全失败处理，以及模型评估与确定性语料画像分离展示的要求。

## Requirements

### Requirement: 系统提供固定且受预算约束的文档抽样
系统 SHALL 为每篇正式 cleaned 文档生成首、中、尾固定抽样，并 MUST 遵守单文档字符、最大文档数、总输入字符和并发配置上限。

#### Scenario: 文档超过单篇输入上限
- **WHEN** cleaned 文档长度超过单文档模型输入预算
- **THEN** 抽样 SHALL 覆盖首、中、尾且拼接结果 MUST NOT 超过配置上限

#### Scenario: 批次超过总预算
- **WHEN** 候选文档数或总抽样字符超过批次预算
- **THEN** 系统 SHALL 按稳定文档顺序处理预算内项目，并 SHALL 将其余项目记录为 skipped

### Requirement: 系统隔离通用 Provider 与治理字段
系统 SHALL 定义可替换的 OCR 质量 Provider 契约，首版 SHALL 提供 mock 和 DeepSeek 适配器；Provider 只负责返回语义建议，标识、指纹、版本、状态和生成时间 SHALL 由系统生成。

#### Scenario: 使用 mock Provider
- **WHEN** 测试或离线验收选择 mock Provider
- **THEN** 系统 SHALL 生成稳定结构化评估且不得访问网络

#### Scenario: 显式使用 DeepSeek
- **WHEN** 操作者显式选择 DeepSeek 且配置有效密钥
- **THEN** 系统 SHALL 通过统一契约发送固定抽样并校验结构化响应

### Requirement: 系统安全处理模型不可用和非法响应
系统 MUST 从环境变量读取密钥，MUST NOT 保存密钥或模型原始响应，并 SHALL 把缺密钥、请求失败、预算跳过和非法响应归一为结构化状态。

#### Scenario: 缺少 API key
- **WHEN** 操作者选择 DeepSeek 但没有配置密钥
- **THEN** 系统 SHALL 记录 skipped 状态、明确错误代码且 SHALL 不覆盖既有成功评估

#### Scenario: Provider 返回非法结构
- **WHEN** Provider 返回非法 JSON、未知风险等级或缺少理由与建议
- **THEN** 系统 SHALL 拒绝该响应、记录 failed 状态且 SHALL 不写入未校验内容

### Requirement: 模型评估与确定性画像分离
系统 SHALL 把模型结果写入独立的 `corpus_ocr_assessments.jsonl`，并 MUST NOT 让模型风险等级直接影响质量门禁或主知识数据。

#### Scenario: 模型判断为高风险
- **WHEN** Provider 对文档返回 high 风险
- **THEN** 报告 SHALL 展示风险、理由和人工建议，但质量门禁 SHALL 不因此失败

#### Scenario: 模型服务不可用
- **WHEN** 外部模型不可用或默认未启用
- **THEN** 确定性画像、主流水线和阶段 A 离线验收 SHALL 继续工作

### Requirement: 报告合并展示两类证据
中文画像报告 SHALL 分别汇总确定性覆盖、阻断问题、非阻断告警和 OCR 模型状态，不得把模型判断伪装为确定性事实。

#### Scenario: 同时存在确定性指标和模型评估
- **WHEN** 两类数据集均存在
- **THEN** 报告 SHALL 分区展示，并 SHALL 包含 provider、model、prompt_version 与人工复核提示
