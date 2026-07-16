# Canonical Document Blocks v2 规格

## Purpose

本规格定义以 Docling 为默认解析引擎生成 Canonical Block v2 的统一约束，确保解析结果具备稳定身份、完整结构、可追溯 OCR 证据、特殊内容保真能力，并通过原子写入避免产生不完整的权威数据。

## Requirements

### Requirement: Docling 是默认解析引擎
系统 SHALL 默认使用 Docling 解析受支持文档；现有解析器只能作为显式 fallback，且 fallback 结果 MUST 标记原因、引擎和审核状态。

#### Scenario: Docling 成功解析
- **WHEN** Docling 完成受支持文档解析
- **THEN** 系统 SHALL 生成 Canonical Block v2，且不得调用 fallback

#### Scenario: Docling 解析失败
- **WHEN** Docling 返回受控失败且配置允许 fallback
- **THEN** 系统 SHALL 运行现有解析器、标记 fallback，并禁止未经审核的结果进入发布集合

### Requirement: 系统生成稳定 Canonical Block v2
每个 Block MUST 包含稳定身份、父子结构、类型、阅读顺序、内容、质量、追溯和治理字段；PDF Block MUST 包含页码与 bbox。Canonical Document MUST 通过严格 JSON Schema 引用 Canonical Block、source snapshot、asset 和 runtime 定义，文档、Block 与 source snapshot 的身份闭包 MUST 在发布前校验通过。

#### Scenario: 相同输入重复适配
- **WHEN** source snapshot、镜像、模型和配置完全相同
- **THEN** Document ID、Block ID、排序和非时间字段 SHALL 完全一致

#### Scenario: Document 中的 Block 不满足独立 Block Schema
- **WHEN** 任一 blocks 数组成员缺少必需字段或包含未允许字段
- **THEN** Canonical Document 校验 MUST 失败且不得进入 semantic-build

### Requirement: 系统自适应启用 OCR
系统 SHALL 优先使用原生文本，只在扫描页、图片区域、低文本覆盖或异常页面启用 OCR，并 SHALL 并行保存原生文本与 OCR 证据。

#### Scenario: 数字原生页面质量正常
- **WHEN** 页面文本层覆盖和质量达到配置门槛
- **THEN** 系统 SHALL 保留原生文本且不得强制整页 OCR

#### Scenario: 扫描页面没有文本层
- **WHEN** 页面预检判定无可用文本层
- **THEN** 系统 SHALL 启用 OCR，并记录触发原因、语言、引擎和置信度

### Requirement: 系统保留特殊内容结构
系统 SHALL 类型化保留表格、代码、公式、图片和标题；表格 SHALL 保留行列、表头、合并单元格和来源页，图片 SHALL 保留文件引用、bbox 和邻接标题。

#### Scenario: 文档包含复杂表格和图片
- **WHEN** Docling 识别出表格和图片区域
- **THEN** Canonical Block SHALL 保存结构与来源坐标，且 MUST NOT 自动生成图片语义解释

### Requirement: v2 输出采用原子写入
系统 SHALL 先在临时目录完成单篇文档全部 v2 产物，校验通过后再原子替换目标；失败时 MUST NOT 留下半写权威数据。

#### Scenario: 适配期间发生异常
- **WHEN** 任一 Block 或资产写入失败
- **THEN** 系统 SHALL 保留既有成功版本并把本次文档标记为失败

### Requirement: Canonical Document v2 是生产语料唯一权威输入
生产 SemanticChunk、retrieval document、serving bundle 和新治理数据 MUST 从通过校验的 Canonical Document v2 派生；旧 parsed document、cleaned markdown 或 chunks v1 不得作为新 release 的直接生产输入。

#### Scenario: 下游构建器收到 legacy parsed JSON
- **WHEN** 操作者尝试把 v1 parsed document 直接送入 semantic-build
- **THEN** 构建器 MUST 拒绝输入并提示先执行只读迁移适配

### Requirement: Canonical Document 绑定不可变来源快照
每个 Canonical Document MUST 引用 source snapshot id、内容 SHA-256 和逻辑 source_id；处理指纹 MUST 包含 snapshot digest，远端来源变化后不得静默复用旧解析结果。

#### Scenario: URL 不变但 raw 内容发生变化
- **WHEN** 新 source snapshot digest 与已有 Canonical Document 的 digest 不同
- **THEN** 该文档及全部下游阶段 SHALL 被判定为 stale 并重新派生

### Requirement: Canonical 治理状态不得越权表示来源可信
Block 的解析/内容质量审核 SHALL 与 source trust、semantic review 和 retrieval eligibility 分开保存；Block approved 只能表示相应结构或内容质量通过，MUST NOT 自动表示来源可信或可用于回答。

#### Scenario: Block 内容质量通过但来源待审核
- **WHEN** Block 质量校验通过且 source trust 为 pending
- **THEN** Canonical 输出 SHALL 保持两个独立状态，下游不得把该 Block 自动标记为 trusted
