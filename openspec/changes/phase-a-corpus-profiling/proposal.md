## Why

当前知识库能够确定性解析、清洗和切分语料，但尚不能量化文档长度、阶段缺失、表格特征、替换字符和 OCR 风险，也缺少把确定性语料错误接入质量门禁的统一证据。阶段五已经完成标准化出口，下一步需要先建立低风险的语料质量基线，为后续 chunk、分类和结构化候选优化提供可比较指标。

## What Changes

- 新增 parsed、cleaned 与 chunks 三层 `doc_id` 并集画像，输出稳定 JSONL 和中文报告。
- 新增可配置的排除规则、长度阈值、表格与异常符号指标，以及四类确定性阻断问题。
- 新增独立的 OCR 模型评估数据集、通用 Provider 契约、mock 与 DeepSeek 适配器；真实调用保持显式 opt-in。
- 把确定性画像接入主流水线、质量检查、制品登记和阶段 A 效果验收。
- 更新现行路线图，标记阶段五已完成的标准化追溯能力，避免重复建设。

## Capabilities

### New Capabilities

- `corpus-quality-profiling`: 规定跨 parsed、cleaned、chunks 的确定性画像、异常分级、配置、报告和质量门禁行为。
- `optional-ocr-quality-assessment`: 规定固定抽样、Provider 隔离、结构化模型结果、失败跳过和非阻断治理边界。

### Modified Capabilities

无。

## Impact

- 新增语料画像与 OCR 评估流水线模块、配置和 JSON Schema。
- 修改主流水线、质量检查、制品 producer、报告策略和阶段验收配置。
- 新增派生数据集和中文报告，不修改主实体、主关系、chunk 内容或人工复核状态。
- DeepSeek 仍是首个真实适配器；不新增必需联网依赖，缺少密钥时离线流程继续运行。
