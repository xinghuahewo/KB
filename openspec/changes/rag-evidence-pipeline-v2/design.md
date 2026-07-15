## Context

BGP 知识库当前以模块化单体运行：离线侧从 54 个来源生成 Canonical Block v2、层级 chunk、catalog、SQLite、BGE-M3 JSONL 和 NumPy mmap 快索引；在线侧通过 FTS5、dense、RRF、`BAAI/bge-reranker-v2-m3`、context assembler 和 DeepSeek 完成问答。代码与大型数据制品已经分离，运行时通过 `BGPKB_DATA_DIR` 读取不可变 release，当前单机只读部署继续适合 SQLite + NumPy mmap。

本次审计确认工程可靠性与数据语义质量不均衡：生产 release 含 58,560 个 chunk，其中 40,957 个少于 20 字符，约 75.55% 内容重复，PeeringDB OpenAPI 文档独占约 71.48% chunk；FTS、embedding 和 reranker 主要使用 240 字符 `content_preview`。54 个来源中仅 5 个处于 approved，但 v2 派生 chunk 全部标记为 approved/trusted。context unit 合并多个 chunk 后只向 LLM 暴露首个 `source_ref`，回答 citations 又是 context pack 全集，不能证明主张与证据逐项对应。现有 chunking 评测以结构完整性为主，部分检索和回答失败不会返回非零状态。

本变更涉及离线数据模型、生产制品、在线检索和回答契约内部结构，必须以新 release 并行构建，不能原地修改当前 release。主要使用者包括离线数据维护者、人工复核者、FastAPI 服务、前端证据工作台和发布运维者。

## Goals / Non-Goals

**Goals:**

- 建立从来源登记、raw snapshot、Canonical Document、语义 chunk、检索文档、证据包到结构化回答的单一权威链路。
- 让每个可检索 chunk 具备完整语义、稳定身份、低重复率、明确来源和可解释检索资格。
- 让 BM25、embedding 与 reranker 使用同一份完整、版本化 `retrieval_text`。
- 把解析质量、内容质量、来源可信、语义审核与检索资格拆开，采用保守且可审计的派生规则。
- 让回答中的每个事实主张显式绑定本次证据包中的 evidence ID，并由服务端校验。
- 将在线 serving 数据与治理/审计数据分离，同时保持当前 FastAPI 和前端兼容。
- 用真实模型固定基线、确定性门禁和非零退出码阻止语义退化进入 release。
- 将完整重建收敛为五阶段 DAG，支持候选构建、原子发布和代码/制品成对回滚。

**Non-Goals:**

- 不引入登录、账号、权限系统或云端同步。
- 不更换当前 screen 常驻方式，不自动部署、不自动切换线上 release。
- 不因本变更迁移到 PostgreSQL、Milvus、Elasticsearch 或其他分布式数据平台。
- 不把大型语料、向量、SQLite 或生成数据重新提交到普通 Git 历史。
- 不允许 LLM 自动批准来源、实体、语义映射或写回正式知识数据。
- 不在本变更中修改前端视觉设计或取消现有 API 字段。

## Decisions

### 1. 采用不可变 Source Snapshot，而不是覆盖 raw 路径

来源定义进入版本化注册表；每次获取产生 manifest 记录，内容写入由 `BGPKB_SOURCE_STORE_DIR` 指定的外置对象库 `objects/sha256/<digest>`，生产服务器默认规划为 `/srv/bgpkb/sources`，逻辑来源通过 snapshot 引用对象。对象库和 snapshot 数据不得进入普通 Git 历史。首次迁移直接导入现有 raw 文件并计算 hash，不强制重新下载。注册记录至少包含 source_id、URL/本地来源、来源类型、许可证状态、抓取时间、HTTP 状态、MIME、ETag、Last-Modified、字节数和 SHA-256。

选择内容寻址是为了让解析输入可复现、避免远端页面更新后静默覆盖。仅在原路径旁增加时间戳不能可靠去重，也不能作为处理指纹。

### 2. Canonical Document v2 是唯一生产权威，v1 只读退役

`canonical_document_v2.schema.json` SHALL 通过 `$ref` 严格引用 block、asset、source snapshot 和 runtime 定义。所有生产 chunk 必须从通过 schema、来源闭包和治理校验的 Canonical Document 派生。v1 parsed/chunks 仅允许被迁移工具读取，禁止进入新 serving bundle、embedding、评测样本或新治理数据。

兼容期保留旧导入入口一个已验证发布周期，并输出显式 deprecated 诊断。不会删除旧 release，也不会在原位置重写 v1 数据。

### 3. 引入 SemanticChunk v3 和文档类型策略

切块器按 `document_profile` 路由：

- RFC/普通正文：按 section 和段落语义合并，默认目标 180–800 tokens，允许配置化小重叠。
- HTML：移除导航/页脚等模板块后按标题区域合并正文。
- PDF/论文：保留标题层级、页码和表格/图注关联；大表按表头重复的行组切分。
- OpenAPI/YAML：以 `method + path` operation、schema 定义或安全/错误对象为原子语义单元，不按标量或标点逐项切块。

短 sibling block 优先在同 section、同来源范围内合并。少于 20 字符的检索单元必须命中受控 allowlist（例如有定义的术语、命令或协议字段），否则隔离。精确重复按规范化内容 hash 合并，近重复只在同源模板区域自动折叠，跨来源近重复保留来源独立性但在检索时抑制重复展示。

chunk ID 由 source snapshot、规范化 section 路径、source block hashes、chunker version 和内容 hash 生成。由于身份规则变化，本次允许 chunk ID 变化，并生成 `chunk_id_migration.jsonl` 记录可证明等价的旧新映射。

### 4. 建立唯一 Retrieval Document 契约

每个 eligible chunk 派生：

```json
{
  "retrieval_doc_id": "...",
  "chunk_id": "...",
  "retrieval_text": "标题 + section 路径 + 完整正文 + 类型化上下文",
  "retrieval_text_hash": "sha256:...",
  "retrieval_text_version": "retrieval_text_v1",
  "eligibility": "eligible",
  "source_ref": "..."
}
```

FTS5、BGE-M3 与 reranker MUST 使用相同 `retrieval_text`；`content_preview` 仅由其派生并用于展示。embedding 缓存键由 retrieval text hash、模型、模型 revision、归一化配置和 provider contract 组成，支持逐批原子 checkpoint。快向量 matrix/metadata/manifest 在向量 JSONL 完成后由主 DAG 强制构建。

检索融合后执行精确内容去重、近重复抑制和每文档候选上限；这比在语料层删除跨来源相同论述更能保留证据独立性。

### 5. 用正交状态替代单一 approved

核心状态分为：

- `parse_status`：解析/结构是否有效。
- `content_quality_status`：文本、表格、阅读顺序和 chunk 质量是否合格。
- `source_trust_status`：来源权威性与审核状态。
- `semantic_review_status`：实体、事实或映射是否经过语义复核。
- `retrieval_eligibility`：根据前述状态和用途确定 `eligible`、`eligible_with_caution` 或 `ineligible`。

迁移时，旧 block `approved` 只能映射为 content quality approved；不得自动提升来源可信或语义审核。旧来源 trust level 和 review status 分别迁移，缺失值采用 pending/unknown。eligibility 由版本化策略确定并记录 rule id，不由 LLM 决定。

### 6. 离线知识抽取只形成受审核候选

现有实体抽取 scaffold 将被替换为可显式启用的离线 candidate extractor。确定性规则或 LLM 可从完整 Evidence 对象生成实体、关系和事实候选，但每条候选必须包含 evidence IDs、输入指纹、provider、model revision、prompt version、置信度和理由，状态固定为 `pending_review`。候选只进入 governance 制品，不能直接改变 serving entities、source trust、semantic review 或 retrieval eligibility。

默认五阶段确定性构建不要求 LLM 候选抽取成功；缺少模型密钥时记录 skipped，不覆盖已有候选。只有通过既有人工审计并显式 apply 的记录才能进入后续新 release。这样补齐当前 scaffold，但不把不稳定模型输出变成生产构建的隐式依赖。

### 7. context pack 使用逐证据对象，回答使用 claim-evidence 结构

检索结果进入 context pack 时，每条证据保持独立边界：evidence_id、chunk_id、source_ref、标题、section 路径、完整文本、内容 hash、信任状态和检索分数。相邻 chunk 可以形成 context group，但不得丢失成员边界或把多个来源压成首个引用。

LLM 使用 JSON response format 输出 `answer`、`claims[]`、`evidence_ids[]`、`confidence` 和 `insufficient_evidence`。服务端在返回前校验：evidence ID 属于本次 pack、每个事实 claim 至少有证据、引用未越界、无证据时不得生成确定性结论。校验失败允许一次受控 repair；仍失败则返回证据不足或 LLM 不可用，不把未验证自由文本标为 answered。

现有 API 顶层 `answer`、`citations`、`context_pack` 和 SSE 阶段保持，新增 `claims`、`evidence` 和 `grounding_status`。旧 citations 由实际使用的 evidence 派生，不再返回 context pack 全集。

来源内容被标记为不可信数据并置于结构化 evidence 字段，system prompt 明确禁止执行证据中的指令；评测集包含提示注入样本。

### 8. 分离 serving bundle 与治理制品

`serving.sqlite` 只包含在线检索必需的 source、chunk/retrieval document、FTS、必要实体/关系和 release meta。人工复核工作簿、决策审计、历史 v1 evidence 等进入独立 `governance.sqlite` 或 JSONL 审计包，不由在线进程打开。

数据库在候选临时路径构建，完成 schema version、foreign key check、integrity check、记录数和跨制品 hash 校验后原子 rename。在线仍以只读 immutable 模式打开。当前单机规模不需要引入外部数据库。

### 9. 以真实基线和硬失败构建质量门禁

评测分四层：

1. Schema/属性测试：来源闭包、稳定 ID、切块不丢内容、原子失败。
2. 生产数据门禁：无意义短块、重复率、空 retrieval text、来源集中度、索引一致性。
3. 检索评测：中英文、事实/过程/政策/全局、同义表达、硬负例和来源多样性。
4. 回答评测：固定 DeepSeek 模型版本，验证事实忠实度、claim citation precision/recall、拒答和提示注入防护；人工黄金集是最终基线，LLM judge 只能辅助。

所有硬门禁命令必须在失败时返回非零。没有真实模型或评测版本不匹配时，release gate 标记 skipped_blocking，而不是由结构客户端替代并通过。

初始发布门槛：schema/追溯/引用 ID 有效率 100%；eligible chunk 中非 allowlist 的少于 20 字符记录为 0；空 retrieval text 为 0；同源精确重复率不高于 2%；黄金集 Recall@8 不低于 90% 且相对冻结基线下降不超过 2 个百分点；MRR 不低于 0.65；回答 claim 引用覆盖率和引用精确率均不低于 95%；硬负例拒答率和提示注入防护通过率 100%；服务器 p95 检索时延不高于 500ms。阈值均进入版本化配置，放宽必须有 ADR 和人工批准。

### 10. 主流水线收敛为五阶段 DAG

阶段及唯一输出为：

1. `source-ingest`：source registry + immutable snapshots。
2. `canonicalize`：Canonical Document v2 + assets + parse/quality diagnostics。
3. `semantic-build`：SemanticChunk v3 + governance states + retrieval documents。
4. `publish-index`：catalog + serving/governance bundle + FTS + embedding + vector JSONL + fast matrix。
5. `verify-release`：完整性、数据质量、真实检索/回答评测、release manifest。

人工治理报告作为阶段产物或独立工作流，不再把几十个报告生成器逐个暴露为主流水线阶段。每个阶段声明输入 hash、输出 manifest、可恢复 checkpoint 和依赖，候选目录成功前不得写当前 release。

### 11. 采用同 release 全量重建，不原地迁移在线数据

本次 chunk 和 retrieval contract 变化较大，选择从冻结 source snapshot 全量派生新 release。SQLite、FTS、embedding 和 fast index 都不在旧 release 上增量修改。内容 hash 缓存只用于安全复用相同 embedding，不能复用旧 chunk 身份或旧评测结论。

这种方式需要一次较长构建，但回滚简单且避免混合 v2/v3 数据。直接原地升级 SQLite 或只替换向量索引会产生跨制品身份不一致，因此不采用。

## Migration Plan

### 数据迁移与生产制品重建顺序

1. 冻结当前代码提交、当前 release id、`SHA256SUMS`、线上健康结果和现有检索/回答基线，确认 `previous` 可用。
2. 从现有来源 inventory 和 raw 文件导入 source registry 与首个 immutable snapshot；先计算 hash，不主动重新抓取远端内容。
3. 严格校验现有 Canonical Document v2；只有 schema/来源快照不闭合或需要新解析策略的文档才重新运行 Docling。
4. 在候选工作区生成 SemanticChunk v3、隔离清单、旧新 chunk 映射和质量画像，不修改 v2 release。
5. 派生正交治理状态、retrieval documents 和完整 `retrieval_text`，执行生产数据硬门禁。
6. 构建 catalog、`serving.sqlite.tmp` 和治理制品；校验后原子形成候选数据库。
7. 按 retrieval text fingerprint 分批构建 BGE-M3 JSONL，复用严格匹配的 embedding cache；随后构建 NumPy matrix、metadata 和 fast manifest。
8. 运行 artifact verification、SQLite integrity/foreign key、索引维度和跨制品 ID 闭包校验。
9. 使用固定 embedding、reranker、DeepSeek 版本执行完整检索和回答黄金集，生成不可变评测证据。
10. 生成候选 release、`SHA256SUMS`、迁移报告、兼容报告和回滚命令；不自动修改 `current`。
11. 经人工批准后先以候选 `BGPKB_DATA_DIR` 做同机 canary，再原子切换代码 generation 与 artifact release 对；验证前端入口、后端健康、SSE、典型问答和时延。
12. 稳定一个发布周期后移除在线 v1 fallback；旧 release 继续按保留策略保存。

### 兼容策略

- API 保留现有字段，结构化 claims/evidence 作为新增字段；前端在兼容期可继续读取旧 citations。
- loader 优先读取 v3 manifest；只在显式兼容开关下读取旧 release，并报告 degraded/legacy 模式。
- `chunk_id_migration.jsonl` 只映射内容与来源可证明等价的记录，无法映射的旧 ID 标记 retired。
- 旧人工决策不会仅凭旧 `approved` 自动转换为 source trust 或 semantic approval；需要按新状态规则重放。
- v1 数据不删除，但不进入新 serving bundle 和新 embedding。

### 回滚方式

- 发布前失败：删除候选工作区或标记 failed，保持 current 代码和制品指针不变。
- canary 失败：停止候选进程，不切换 current。
- 切换后失败：同时恢复上一代码 generation 与 `previous` artifact 指针，重启现有 screen 会话并运行健康/问答巡检；不得让新代码配旧 serving bundle 或反向混用。
- 回滚不重建、不修改历史 release；修复后生成新的 release id。

## Testing Strategy

- 每个实现任务先写失败测试，覆盖 schema、状态迁移、切块策略、去重、retrieval text、embedding cache、数据库原子性、证据校验和 CLI 退出码。
- 为 RFC、HTML、复杂 PDF/表格、OpenAPI/YAML 建立小型黄金 fixture 和属性测试；验证内容覆盖、稳定身份、短块合并、同源重复折叠和跨来源追溯。
- 对生产候选制品运行统计门禁，并将本审计数字保留为迁移前基线，报告必须同时给出绝对值和相对变化。
- 建立不少于 100 个检索黄金问题，覆盖中英文、事实、过程、政策、全局、难负例、近义词和来源冲突；回答集包含真实 DeepSeek 固定版本、人工期望证据和提示注入样本。
- API contract 测试验证旧字段不被删除、SSE 顺序兼容、引用只来自实际使用证据；浏览器回归验证前端仍能展示回答和多引用。
- 在生产服务器候选目录验证 p50/p95 检索、内存、启动时间和完整问答，不直接覆盖 current。

## Implementation Checkpoints

- 检查点 A（任务 1–3）：冻结基线，完成 source store、注册表、Canonical Schema 和 v1 生产依赖扫描；不改变线上读取路径。
- 检查点 B（任务 4–6）：完成 SemanticChunk v3、retrieval documents、索引输入和治理/知识候选模型，在本地或候选数据目录验证；仍不切换 serving release。
- 检查点 C（任务 7–8）：完成 evidence/claim 回答与 serving/governance bundle，保持 API 兼容并通过后端/前端 contract 测试。
- 检查点 D（任务 9–10）：完成真实评测门禁和五阶段流水线，使候选构建可以端到端重复运行。
- 检查点 E（任务 11–12）：执行完整制品重建、canary、回滚演练和最终验收；任何生产切换都必须另行获得人工明确批准。

每个检查点应独立审查、验证和形成可回滚提交，不把 95 个任务压入单个不可审查提交；OpenSpec `tasks.md` 是跨对话的唯一进度来源。

## Risks / Trade-offs

- [chunk ID 大面积变化导致历史引用失效] → 保留旧 release，生成可证明等价的迁移映射，并在一个发布周期内支持旧 ID 查询。
- [切块去重误删有独立来源价值的证据] → 只自动折叠同源精确/模板重复，跨来源保留但在检索展示层抑制。
- [完整 retrieval text 增加 embedding 成本和索引体积] → 使用内容指纹缓存、批次 checkpoint 和最大 token 策略；质量优先于继续索引无意义碎片。
- [真实 LLM 评测不完全确定] → 固定模型与 prompt 版本，确定性检查作为硬底线，LLM judge 结果与人工黄金集分开记录。
- [五阶段编排隐藏细粒度诊断] → 阶段内部仍保留子任务 manifest、耗时、日志和可恢复 checkpoint，只收敛外部入口。
- [serving/governance 拆分增加制品数量] → 用统一 release manifest 和跨制品 hash 闭包保证一致性，在线适配器只打开 serving bundle。
- [迁移周期中 v2/v3 双轨增加复杂度] → 新 release 全量并行构建，禁止同一 release 混用版本；兼容期开关有明确到期条件。

## Open Questions

- 近重复检测首版采用 MinHash/SimHash 还是规范化 token shingles，需要在小型黄金集上比较误折叠率后写入 ADR；在此之前只启用精确重复硬门禁。
- OpenAPI operation 超长时按参数组、响应码还是 schema 引用拆分，需要以 PeeringDB 查询黄金集决定默认策略。
- 真实回答评测的人工黄金集由谁最终签署、后续如何变更，需要在实施前登记 owner；缺少 owner 不阻止生产切换前的实现工作，但阻止生产 release。
