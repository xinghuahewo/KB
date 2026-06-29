## 为什么实施

阶段三点五已经提供稳定 URI 和 JSON-LD context，但项目尚不能发布完整、可交换、可审计的 JSON-LD、SKOS、PROV-O 与 RDF 产物。阶段五需要补齐正式标准出口，同时允许模型帮助发现语义映射候选，又不破坏确定性发布和人工审核边界。

## 变更内容

- 新增实体、来源、关系和证据的确定性 JSON-LD、PROV-O 与 Turtle 样例出口。
- 新增标准映射配置、Schema、覆盖率报告和完整性检查。
- 新增离线 mock 与显式 DeepSeek 两类模型映射候选生成方式。
- 新增人工决策、审计、dry-run 和显式写入批准映射的治理链路。
- 把阶段五接入确定性流水线、制品清单和阶段验收门禁。
- 修正阶段五文档中关于 JSON-LD context 和命名空间尚未交付的过期基线。
- 不修改现有 JSONL、CSV、SQLite 主发布格式，不允许模型直接改写主实体、主关系或正式出口。

## 能力

### 新增能力

- `standard-knowledge-exports`：生成稳定、可追溯、可验证的 JSON-LD、SKOS、PROV-O 和 RDF/Turtle 发布物。
- `reviewed-semantic-mapping`：生成模型辅助语义映射候选，并通过人工审计和显式应用形成批准映射。

### 修改能力

无。

## 影响

- 新增 `src/bgpkb/pipeline/` 下的标准出口、候选、审计和应用脚本。
- 新增 `metadata/config/standard_exports.yaml` 和三类 JSON Schema。
- 新增 `data/published/`、`data/derived/datasets/`、`data/review_inputs/` 与中文报告产物。
- 更新确定性流水线、制品 producer、报告策略、阶段五文档和阶段验收配置。
- 默认流程保持离线，不新增必需的在线依赖；DeepSeek 仅在显式选择并提供环境变量时调用。
