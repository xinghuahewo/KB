## ADDED Requirements

### Requirement: 生成稳定的标准化实体和来源目录
系统 MUST 从现有发布目录和阶段三点五语义标识生成排序稳定的 JSON-LD 实体与来源目录，并保留复核状态和来源 URI。

#### Scenario: 重复生成结果稳定
- **WHEN** 输入文件和配置未发生变化时连续运行标准出口生成器
- **THEN** 两次生成的实体和来源 JSON-LD 内容必须一致

### Requirement: 表达 SKOS 和 PROV-O 语义
系统 MUST 将概念标签、定义和别名映射为 SKOS，并将来源、raw、parsed、cleaned、chunk、实体、证据和生成活动的主链映射为可追溯的 PROV-O 记录。

#### Scenario: 概念实体具有来源链
- **WHEN** 一个实体具有名称、定义和 `source_refs`
- **THEN** JSON-LD 必须包含稳定 `@id`、SKOS 标签或定义以及可解析的来源 URI

#### Scenario: 数据加工主链可追溯
- **WHEN** 来源目录、解析路径、清洗路径、chunk 和实体证据均存在
- **THEN** provenance 记录必须能从实体和 chunk 回溯到 cleaned、parsed、raw 与 source

### Requirement: 提供 RDF Turtle 样例
系统 MUST 从正式标准出口生成确定性 Turtle 样例。v1 仅允许 IRI 主语、CURIE 谓词、IRI/CURIE 对象与纯字符串 literal；其他类型必须显式拒绝。

#### Scenario: 特殊字符安全导出
- **WHEN** 标签或定义包含引号、反斜杠或换行
- **THEN** Turtle 样例必须使用合法转义且保持稳定排序

#### Scenario: 不支持的 RDF 对象被拒绝
- **WHEN** 三元组包含未登记对象类型或不允许的控制字符
- **THEN** 序列化器必须失败并说明原因，不得输出表面成功的 Turtle

### Requirement: 保持现有发布格式兼容
系统 MUST NOT 修改现有 JSONL、CSV、SQLite、RAG 或服务接口的语义和路径。

#### Scenario: 标准出口独立生成
- **WHEN** 运行阶段五生成器
- **THEN** 现有主发布文件必须保持不变，新增内容只能写入阶段五派生出口和报告路径

### Requirement: 报告覆盖率与阻塞项
系统 MUST 生成中文标准化报告，列出资源数量、标准词汇覆盖率、未映射项、重复 URI 和来源解析错误。

#### Scenario: 未映射关系可见
- **WHEN** 本地关系没有确定性标准谓词映射
- **THEN** 报告必须列出该关系且正式出口使用受控 `bgpkb:` 谓词或明确阻塞
