# Docling 私有化成熟知识清洗 v2 设计

## 1. 背景与目标

当前知识库已经具备 TXT、HTML、YAML、PDF 的确定性解析、Markdown 清洗语料、chunk 生成、质量检查和阶段 A 语料画像。现有链路能够稳定抽取文本，但 PDF 主要按页提取，HTML 主要形成全文，尚未统一保留版面块、阅读顺序、表格结构、代码、公式、图片引用、坐标和解析置信度。

本变更把知识清洗升级为生产级批处理平台：在独立 Linux GPU 服务器上私有化部署 Docling，以结构化 Block JSON 为权威数据，建立自适应 OCR、可审计清洗、失败隔离、断点续跑、全量 v2 迁移、逐文档差异验收和可回滚切换。

### 目标

- Docling 成为默认文档理解引擎，现有解析器保留为显式降级和质量对照基线。
- 对全部现有 54 篇语料生成结构化 v2 产物，而不是只在少量试点文档上验证。
- 以 Block JSON 保存标题、正文、表格、代码、公式、图片、坐标、阅读顺序和完整追溯。
- 对数字原生文档优先使用原生文本，只对扫描页、图片区域或低质量页面自适应启用 OCR。
- 清洗规则分级、每次转换可解释、任何语义性改写必须经过人工审核。
- v2 在并行目录完成全量验收后一次性切换，保留 v1 回滚能力。

### 非目标

- 不建设实时上传或查询 API。
- 不引入 PP-StructureV3、Unstructured 或第二个版面解析引擎。
- 不生成图片或图表语义解释。
- 不让模型自动重写原文事实、自动批准清洗结果或绕过质量门禁。
- 不在本变更中重做 topic 分类、实体抽取或关系抽取。

## 2. 部署与供应链边界

Docling 运行在独立 Linux GPU 服务器的固定容器镜像中。构建阶段完成 Python 包、Docling 模型和 OCR 模型下载，生成依赖锁、模型文件 SHA-256、镜像摘要和许可证清单；生产运行阶段禁止外网访问，不允许自动更新模型或依赖。

部署必须记录：

- 容器镜像 digest；
- Python、CUDA、驱动和 Docling 版本；
- 模型名称、版本、文件 hash 和加载配置；
- GPU 型号、显存和推理精度；
- 清洗配置版本与规则版本。

批处理通过容器命令运行并挂载知识库目录，不提供常驻 HTTP 服务。密钥不是运行依赖，模型与语料不得离开内网服务器。

Docling 的统一文档表示、版面、阅读顺序、表格结构和本地 OCR 能力以官方文档为实现依据：<https://docling-project.github.io/docling/>。

## 3. 总体架构

```text
不可变 raw
  -> 文档预检与输入指纹
  -> Docling 私有化解析
  -> 自适应 OCR
  -> parsed v2 / 原始 Block
  -> 分级清洗与结构校正
  -> cleaned Block v2（权威数据）
  -> Markdown v2 / chunks v2（派生产物）
  -> v1-v2 差异与质量验收
  -> 发布指针切换
```

### 3.1 文档预检

预检读取文件格式、大小、页数、文本层覆盖、图片页比例、加密状态和输入 hash。结果决定 Docling 配置、OCR 策略、超时和资源预算。预检不修改原文件。

### 3.2 Docling 主引擎

所有受支持文档默认进入 Docling。TXT、HTML、YAML 等格式若 Docling 无法保持现有契约，可调用现有解析器，但必须生成 `fallback` 状态、原因和对照记录，不能静默混入正常结果。

Docling 输出先转换为项目自有 Canonical Block Schema，避免下游直接依赖某一版本的 Docling 内部对象。

### 3.3 自适应 OCR

OCR 不对全部 PDF 强制整页运行。触发条件至少包括：

- 页面没有可用文本层；
- 文本字符量或覆盖率低于配置阈值；
- 页面主要由图片区域组成；
- 原生文本出现明显编码、断裂或阅读顺序异常。

每页记录 `native_text`、`ocr_applied`、OCR 引擎、语言、置信度和触发原因。OCR 结果不得覆盖原生文本证据；两者都要保留，清洗层明确选择最终文本。

## 4. 权威数据模型

### 4.1 Canonical Block JSON

cleaned Block JSON v2 是唯一权威清洗数据。Markdown 和 chunks 只能从通过治理检查的 cleaned Block 派生。

每个 Block 至少包含：

- 身份：`doc_id`、`page_id`、`block_id`、`parent_block_id`；
- 结构：`block_type`、`heading_level`、`reading_order`、子块引用；
- 版面：页码、bbox、列号和旋转信息；
- 内容：原始文本、规范化文本、语言；
- 特殊内容：表格行列、表头、合并单元格、代码语言、公式表示、图片文件和标题引用；
- 质量：解析置信度、OCR 置信度、问题代码；
- 追溯：源文件 hash、Docling/模型/配置版本、生成步骤；
- 治理：`review_status`、转换记录和生成时间。

图片只保存裁剪文件、页码、bbox、标题、alt 文本和邻接 Block 引用，不做图片语义解释。

### 4.2 v2 目录

- `data/corpus/parsed_v2/`：Docling 原始结构的项目规范化表示；
- `data/corpus/cleaned_blocks_v2/`：权威 cleaned Block；
- `data/corpus/cleaned_markdown_v2/`：人读派生版本；
- `data/corpus/assets_v2/`：图片、表格和页面级引用资源；
- `data/corpus/chunks_v2/`：从 approved cleaned Block 派生的 chunk；
- `data/derived/datasets/cleaning_runs_v2.jsonl`：运行级事件；
- `data/derived/datasets/cleaning_document_status_v2.jsonl`：文档状态与错误；
- `data/derived/datasets/cleaning_transformations_v2.jsonl`：清洗转换审计；
- `data/generated/reports/corpus/cleaning_v2/`：差异、质量、性能和迁移报告。

## 5. 清洗规则与治理

清洗规则分三级：

1. 无损规范化：Unicode、换行、空白、编码和稳定标识，可自动执行。
2. 结构校正：页眉页脚移除、标题修正、跨页段落拼接、表格跨页合并，必须保存规则 ID、前后值、证据和置信度。
3. 语义性修改：正文改写、图表解释、事实补全，一律禁止自动进入正式 cleaned Block，只能形成待人工审核建议。

原始 Block 永久保留。每条 cleaned Block 必须能回溯到原始 Block、页面和原文件。删除正文、合并结构或替换文本时必须生成 transformation 记录，禁止无法解释的静默清洗。

只有 `review_status=approved` 或满足确定性自动批准规则的 cleaned Block 可以进入 chunks v2。fallback、低置信度 OCR、结构冲突和人工待审 Block 必须被下游排除。

## 6. 批处理状态机

```text
discovered -> preflighted -> parsed -> normalized -> validated -> approved
                                      |              |
                                      +-> quarantined+
                                             |
                                      manually_reviewed
```

每次运行生成唯一 `run_id`，记录输入 hash、配置、容器、Docling、模型、GPU、开始结束时间、返回码和输入输出摘要。

批处理要求：

- 以文档为最小幂等单元；输入、配置和模型未变化时复用成功结果；
- 单篇失败不终止整个批次，进入隔离队列并保存错误与中间产物；
- 支持从预检、解析、清洗、验证或派生阶段断点续跑；
- OOM、超时和暂态模型错误采用有上限重试；内容、Schema 和治理错误不自动重试；
- Docling 失败允许显式降级，但 fallback 结果未经人工确认不得发布；
- 所有输出采用临时目录生成并原子切换，失败批次不得留下半成品。

## 7. 全量迁移与切换

1. 对现有 54 篇语料全量生成 v2 产物，不覆盖 v1。
2. 对每篇文档生成 v1/v2 正文、标题、section、表格、图片、chunk 和来源引用差异。
3. 对异常文档、fallback、低置信度 OCR 和内容覆盖下降文档进入人工复核队列。
4. 从全量结果选取约 12 篇高风险文档建立人工验收集，覆盖复杂 PDF、扫描页、表格、RFC、HTML 和超长文档。
5. 所有硬门禁通过后，更新发布指针一次性切换到 v2。
6. v1 目录、发布 manifest 和回滚命令保留；切换失败可立即恢复旧指针。

## 8. 质量验收

### 8.1 全量确定性门禁

- 54/54 文档完成处理；
- JSON/Schema 错误为 0；
- 不可追溯 Block、空正文、替换字符和重复 ID 为 0；
- 相同输入、配置、容器和模型重复运行时，非时间字段完全一致；
- 每个 PDF Block 都能追到页码和 bbox；
- 表格保留行列、表头、合并单元格和来源页；
- fallback 必须显式登记，未审核 fallback 发布数为 0；
- v2 相对 v1 的正文覆盖率不低于 99.5%，被移除内容必须能归因到已登记清洗规则。

### 8.2 人工验收集

- 标题层级 F1 不低于 95%；
- 阅读顺序准确率不低于 98%；
- 表格单元格结构准确率不低于 95%；
- OCR 字符错误率不高于 2%。

### 8.3 运行验收

- 报告每篇文档耗时、GPU 峰值显存、OCR 页数、重试和 fallback；
- 汇总吞吐量、p50/p95 时延和失败率，形成后续容量基线；
- 任何硬门禁失败时不得切换发布指针；
- 阶段验收必须说明新增能力、使用者可执行动作、下游可依赖契约和剩余人工事项。

## 9. 测试策略

- 契约测试：Canonical Block、run、status、transformation 和差异记录 Schema；
- 单元测试：预检路由、自适应 OCR、规则分级、状态机、幂等和重试；
- 适配器测试：使用固定 Docling fixture，不依赖外网；
- 故障测试：OOM、超时、损坏 PDF、加密 PDF、模型缺失和磁盘半写；
- 回归测试：54 篇全量生成、两次运行稳定性和 v1/v2 差异；
- 人工验收测试：12 篇高风险文档的标题、阅读顺序、表格和 OCR 指标；
- 发布测试：v2 指针切换、下游 chunk 构建和 v1 回滚。

## 10. 风险与控制

- GPU 或模型版本漂移：锁定镜像与模型 hash，运行时禁止联网。
- Docling 内部格式变化：通过项目 Canonical Block 适配层隔离。
- OCR 覆盖原生文本：并行保留原生文本与 OCR 证据，由规则选择最终值。
- 清洗过度删除：所有结构删除都必须有 transformation 记录和 v1/v2 差异。
- 全量迁移影响发布：并行 v2 目录、人工验收、原子指针切换和 v1 回滚。
- 单引擎盲区：保留现有解析器作显式 fallback 与基线，但不静默降级。

## 11. 实施拆分

本设计只覆盖一个 OpenSpec 变更：Docling 清洗内核、批处理运行、全量 v2 迁移、质量验收和发布切换。实时 API、图片语义解释、第二解析引擎和下游语义抽取保持独立，不进入本阶段。
