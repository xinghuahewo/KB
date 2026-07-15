## Why

当前 BGP 知识库已经具备版本化制品、Canonical Block v2、SQLite、混合检索、真实 reranker 和 NumPy mmap 快索引等可靠工程基础，但生产数据仍存在 69.94% chunk 少于 20 字符、75.55% 内容重复、单一 OpenAPI 文档占 71.48% chunk，以及 BM25、embedding、reranker 仅使用 240 字符预览的问题。解析成功、内容质量、来源可信和检索资格又被同一个 `approved` 状态混用，LLM 最终输出缺少 claim 与证据的逐项绑定，现有评测也不足以阻断语义退化，因此需要把从来源快照到可验证回答的整条证据链收敛成单一、可迁移、可回滚的产品流程。

## What Changes

- 建立来源注册表和按 SHA-256 内容寻址的不可变 raw snapshot，记录来源版本、抓取时间、许可证、MIME、ETag、Last-Modified 和获取结果；来源采集正式进入可重复流水线。
- **BREAKING**：将 Canonical Document v2 设为生产语料唯一权威输入，强化 JSON Schema 引用与校验；旧 parsed/chunks v1 退出在线发布和新治理数据生成，仅保留限期只读迁移适配器。
- **BREAKING**：引入文档类型专用语义切块，分别处理 RFC/正文、HTML、PDF/表格及 OpenAPI/YAML；增加短块合并、无意义块隔离、精确与近重复消除、来源占比诊断和语义质量门禁。
- 新增完整且版本化的 `retrieval_text`，统一供 FTS5、BGE-M3 embedding 和 reranker 使用；`content_preview` 降为仅供界面展示，并以内容指纹支持 embedding 断点续建和缓存复用。
- 将解析状态、内容质量、来源可信、语义审核和检索资格拆成独立字段与确定性决策，禁止把结构清洗通过等同于事实可信或可用于回答。
- 将现有实体抽取 scaffold 收敛为显式启用的离线知识候选抽取；LLM 生成的实体、关系或事实必须绑定 evidence ID、固定为 pending_review，并沿用人工审核后显式应用的治理边界。
- 将 context pack 改为边界清晰的证据对象；LLM 输出改为 claim-evidence 结构化结果，并在服务端执行 evidence ID、引用范围和无证据主张校验，同时保留现有 FastAPI 对外问答契约的兼容投影。
- 拆分最小在线 `serving.sqlite` 与治理/审计数据制品，数据库和索引均在候选工作区完成校验后原子发布。
- 建立使用固定真实模型版本的检索、精排、回答忠实度、引用精确率/召回率、拒答和注入防护评测；任何硬门禁失败必须以非零状态阻断发布。
- 将当前数十个串行脚本收敛为来源采集、规范化、语义构建、发布索引、验证发布五个产品阶段，把快向量索引纳入正式 DAG，并规定完整制品重建、迁移、回滚和验收顺序。
- 本变更不引入登录、账号、云端同步，不改变现有 screen 部署方式，不把大型语料或索引重新放入普通 Git 历史，也不允许模型直接批准或写回正式知识数据。

## Capabilities

### New Capabilities

- `immutable-source-registry`: 定义来源登记、不可变 raw snapshot、内容寻址、来源版本与许可证/HTTP 元数据要求。
- `semantic-chunking-v3`: 定义按文档类型生成语义 chunk、短块合并、无意义块隔离、去重、稳定身份与质量门禁。
- `unified-retrieval-document`: 定义完整 `retrieval_text`、FTS/embedding/reranker 一致输入、指纹缓存、快索引与检索多样性要求。
- `evidence-governance`: 定义解析质量、内容质量、来源可信、语义审核和检索资格的正交状态及决策规则。
- `reviewed-knowledge-extraction`: 定义从完整证据生成实体/关系/事实待审核候选、证据绑定、模型指纹和人工显式应用边界。
- `grounded-evidence-answering`: 定义证据对象、claim-evidence 结构化回答、引用校验、拒答和提示注入边界。
- `serving-data-bundle`: 定义最小在线数据库、治理制品分离、原子构建、同 release 数据一致性与兼容读取要求。
- `rag-quality-gates`: 定义真实检索/回答基线、回归阈值、硬失败退出和发布阻断要求。
- `converged-data-pipeline`: 定义五阶段产品流水线、阶段输入输出、候选制品构建、完整重建与原子发布/回滚顺序。

### Modified Capabilities

- `canonical-document-blocks-v2`: 将 Canonical Document 与 Canonical Block Schema 严格关联，并补充来源快照、状态分层和生产权威输入要求。
- `corpus-v2-migration`: 从“v1/v2 并行迁移”转为“v2 唯一生产权威、v1 限期只读兼容并可验证退出”。
- `corpus-quality-profiling`: 将画像从结构告警扩展为对生产 v2 chunk 的长度、重复、来源集中度、可索引性和语义质量硬门禁。

## Impact

- 影响 `backend/src/bgpkb/ingestion`、`indexing`、`publishing`、`retrieval`、`workflows`、相关 Schema、测试、质量配置、制品清单和长期数据文档。
- 会生成新的 chunk 身份、`retrieval_text`、向量索引、快索引和 SQLite serving bundle；旧制品保持不可变，通过 release 指针并存，不进行原地升级。
- 现有 FastAPI 路由、SSE 事件基本语义和前端问答入口保持兼容；新增结构化证据字段采用向后兼容扩展，兼容期内仍输出现有 `answer`、`citations` 和 `context_pack` 字段。
- 当前 SQLite + NumPy mmap 架构继续使用，不以迁移 PostgreSQL、Milvus 或 Elasticsearch 作为本变更前置条件。
- 生产重建需要 Docling GPU 1、embedding `8011`、reranker `8012` 和 DeepSeek 真实评测；任何密钥只从环境变量读取，不进入仓库或制品。
- 旧 release、旧代码 generation 与 `previous` 指针构成回滚基线；新链路只有在完整数据迁移和全部发布门禁通过后才能显式切换。
