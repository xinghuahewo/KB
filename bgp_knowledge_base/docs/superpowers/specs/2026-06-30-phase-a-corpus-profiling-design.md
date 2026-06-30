# 阶段 A：语料质量画像设计

## 目标

为 parsed、cleaned 与 chunks 三层语料建立可复跑、可审计的质量画像，使空正文、替换字符、重复文档标识和孤儿 chunk 成为确定性门禁，同时把长度、表格与 OCR 风险转化为非阻断告警。外部模型只提供可选 OCR 风险建议，不改变确定性结果，也不直接阻断流水线。

## 范围与原则

- 画像对象取 parsed、cleaned、chunks 三处逻辑 `doc_id` 的并集，缺失阶段必须显式记录。
- 排除目录说明文件，例如 `README.md`；保留正式 seed/context 语料。排除规则由配置声明。
- 确定性画像和外部模型结果分库存储，避免网络、模型版本或响应漂移污染治理基线。
- 所有阈值、抽样上限和 Provider 白名单由 YAML 配置管理。
- 不修改主实体、主关系、chunk 内容或人工复核状态。

## 架构

### 确定性画像轨

`profile_cleaned_corpus.py` 读取 parsed JSON、cleaned Markdown 和 chunk JSONL，归一化为按 `doc_id` 排序的文档视图。每条画像记录包含阶段存在性、字符与段落统计、section 与 chunk 数量、标题异常、重复标题、替换字符、疑似表格、异常符号和确定性问题代码。

输出：

- `data/derived/datasets/corpus_profile.jsonl`
- `data/generated/reports/corpus/corpus_profile_report.md`

硬阻断项限定为：

1. cleaned 正文为空；
2. cleaned 正文含 `U+FFFD`；
3. parsed 输入中出现重复 `doc_id`；
4. chunk 的 `doc_id` 在 parsed 与 cleaned 中均不存在。

缺失阶段、超短/超长、疑似表格、异常符号、空标题和重复标题只生成告警。画像命令遇到硬阻断项时仍先原子写出完整数据集和报告，再以非零状态退出，便于定位问题。

### 可选模型评估轨

`assess_corpus_ocr_quality.py` 读取 cleaned 文档，为每篇文档构造固定的首/中/尾抽样。通用 Provider 接口负责接收结构化请求并返回风险等级、理由和人工建议；首版提供稳定 mock 与 DeepSeek 适配器。真实调用必须显式选择 Provider，缺少密钥、网络失败或非法响应时记录结构化 `skipped`/`failed` 状态，不覆盖既有有效结果。

输出：

- `data/derived/datasets/corpus_ocr_assessments.jsonl`

模型输入受每篇字符数、总输入字符数、最大请求数和并发上限约束。模型输出不进入 `quality_check.py` 的阻断判定，只在画像报告中作为非阻断参考。

### 配置与契约

新增 `metadata/config/corpus_profiling.yaml`，包含：

- 文件排除规则；
- 短/长文档、段落和异常符号阈值；
- 疑似表格检测参数；
- OCR 抽样、请求和并发预算；
- 允许的 Provider、模型和提示词版本。

新增 JSON Schema 分别约束确定性画像与 OCR 评估记录。报告在 `report_policy.yaml` 注册，新增数据集和报告在制品 producer 映射中登记。

## 数据流

```text
parsed ───┐
cleaned ──┼─> 文档并集与确定性指标 ─> corpus_profile.jsonl ─┐
chunks ───┘                                                 ├─> 中文画像报告
cleaned ─> 固定首/中/尾抽样 ─> Provider ─> OCR assessments ─┘
```

主流水线只运行确定性画像。真实 Provider 调用保持显式 opt-in；默认离线运行不会访问网络。

## 错误处理与安全边界

- JSON/JSONL 解析错误、字段类型错误和重复标识必须产生可定位的问题代码。
- 输出采用稳定排序、稳定 JSON 序列化和原子替换，失败时不留下半写文件。
- API key 只从环境变量读取，不写入数据集、报告或日志。
- 不保存模型原始响应；只保存通过严格字段校验的结构化评估。
- 外部调用失败不改变确定性画像，也不升级为质量门禁失败。

## 测试与验收

实现采用测试驱动开发，至少覆盖：

- 三层 `doc_id` 并集、README 排除和 seed/context 保留；
- 字符、段落、section、chunk、标题、表格和异常符号指标；
- 四类硬阻断及告警与阻断的隔离；
- 稳定排序、稳定序列化和原子输出；
- 首/中/尾抽样及总请求、总字符预算；
- mock、DeepSeek 缺密钥、请求失败和非法结构化响应；
- 模型结果不参与确定性门禁；
- 报告策略、制品清单、主流水线和阶段 A 验收 gate。

验收通过条件：确定性画像可完整生成；当前语料不存在硬阻断问题；模型不可用时有明确跳过记录；报告能列出覆盖率、分布、异常文档、模型状态和后续人工建议；全量测试及阶段验收通过。

## 非目标

- 不引入完整 OCR、版面重建或商业文档解析服务。
- 不上传完整文档到模型服务。
- 不让模型结果自动修改语料或质量阈值。
- 不在本阶段实现 topic 分类候选、层级 chunk 或增量流水线。
