## Why

当前清洗链路能够确定性抽取文本并生成质量画像，但尚未统一保留版面块、阅读顺序、表格结构、代码、公式、图片引用、坐标和解析置信度，难以达到生产级知识清洗的结构保真与审计要求。阶段 A 已提供质量基线，现在可以在不破坏 v1 的前提下，以私有化 Docling 和并行 v2 迁移把清洗升级为可追溯、可评测、可回滚的成熟批处理平台。

## What Changes

- 在独立 Linux GPU 服务器上部署锁定镜像与模型的 Docling 批处理运行环境，生产运行禁止外网访问。
- Docling 成为默认解析引擎；现有解析器保留为显式 fallback 和质量对照，不允许静默降级。
- 新增项目自有 Canonical Block JSON v2，保存结构、版面、表格、代码、公式、图片引用、质量和追溯字段。
- 新增自适应 OCR：优先原生文本，仅对扫描页、图片区域或低质量页面启用 OCR，并并行保留两类证据。
- 新增分级清洗规则、逐字段 transformation 审计、人工复核状态和下游发布隔离。
- 新增幂等批处理状态机、输入指纹、断点续跑、有限重试、失败隔离和运行级证据。
- 对现有 54 篇语料全量生成并行 v2 产物，执行 v1/v2 差异、人工高风险验收、发布指针切换和 v1 回滚验证。
- **BREAKING**：完成验收并切换后，cleaned Block v2 成为权威清洗数据；Markdown 和 chunks 变为只读派生产物。切换前 v1 契约保持不变。

## Capabilities

### New Capabilities

- `private-docling-runtime`: 规定 GPU 容器、依赖与模型锁定、离线运行和运行环境证据。
- `canonical-document-blocks-v2`: 规定 Docling 适配、自适应 OCR、Canonical Block、特殊内容和追溯契约。
- `governed-cleaning-transformations`: 规定清洗规则分级、转换审计、人工审核和下游隔离。
- `resumable-cleaning-batches`: 规定幂等批处理状态机、断点续跑、重试、fallback 和失败隔离。
- `corpus-v2-migration`: 规定 54 篇全量 v2 迁移、差异评测、发布切换、验收门槛和回滚。

### Modified Capabilities

无。现有 OpenSpec 主规格尚未归档；v1 行为在切换前保持兼容，新契约以新增能力表达。

## Impact

- 新增 Docling GPU 容器、模型锁和离线安装资产；增加显著的 GPU、镜像和模型存储需求。
- 新增 parsed v2、cleaned Block v2、Markdown v2、assets v2、chunks v2、运行状态和转换审计数据集。
- 修改解析、清洗、chunk、质量检查、制品清单、主流水线和阶段验收入口，但先以并行 v2 方式接入。
- 引入 Docling 及其模型依赖；不引入实时 API、PP-StructureV3、外部多模态 API 或图片语义解释。
- 发布切换后，下游必须从 approved cleaned Block v2 派生 Markdown 和 chunks；保留 v1 快速回滚路径。
