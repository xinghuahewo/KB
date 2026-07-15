## 1. 冻结基线与实施前决策

- [x] 1.1 记录当前代码提交、线上 release id、SHA256SUMS、服务健康、检索时延和现有数据统计，形成不可变迁移基线且不修改线上指针
- [x] 1.2 运行并记录后端完整测试、制品校验和现有检索/回答评测基线，区分真实失败与既有已知问题
- [x] 1.3 为迁移新增测试 fixture 目录，纳入 RFC、HTML、复杂 PDF/表格、PeeringDB OpenAPI/YAML、重复模板和提示注入最小样本
- [x] 1.4 用黄金样本比较 exact hash、token shingles、MinHash/SimHash 的误折叠率，形成近重复策略 ADR；首版未获批准前只启用 exact dedupe 硬门禁
- [x] 1.5 用 PeeringDB 查询黄金集确定超长 OpenAPI operation 的拆分规则并形成 ADR
- [x] 1.6 登记检索/回答黄金集的 owner、审核与变更流程；owner 未登记时将生产发布标记为 blocking

## 2. 来源注册表与不可变原始数据

- [x] 2.1 先编写来源注册表、source snapshot、内容寻址去重、许可证缺失和单来源失败隔离的失败测试并确认失败原因符合规格
- [x] 2.2 定义并校验 source registry 与 source snapshot JSON Schema，覆盖 source_id、获取方式、来源类型、许可证状态和 HTTP/内容元数据
- [x] 2.3 将当前硬编码来源清单迁移为版本化注册表，并修改采集器只从注册表读取，不在代码中保留第二份权威清单
- [x] 2.4 实现 `raw/objects/sha256/<digest>` 不可变对象存储、snapshot manifest、条件请求元数据和敏感头过滤
- [x] 2.5 实现现有 raw 目录只读导入器，计算 hash、复用相同对象并输出逐来源迁移清单，不主动重新下载或覆盖原文件
- [x] 2.6 实现 source-ingest 阶段的逐来源终态、缺失策略、原子 manifest 和非零硬失败传播
- [x] 2.7 运行来源单元/集成测试和首次 dry-run 导入，验证注册表覆盖率 100%、快照 hash 闭包完整且 Git 不跟踪 raw objects

## 3. Canonical JSON 契约收敛与 v1 退出生产链路

- [x] 3.1 先为 Canonical Document `$ref`、非法 Block、source snapshot 不闭合、状态越权和 legacy 输入拒绝编写失败测试并确认按预期失败
- [x] 3.2 将 Canonical Document v2 Schema 严格引用 Canonical Block、source snapshot、asset、runtime 和 diagnostics 定义，并设置受控 additionalProperties
- [x] 3.3 将 source snapshot digest 纳入 Canonical 处理指纹、Document 元数据和 stale 判定，保持相同输入的稳定 ID
- [x] 3.4 拆分 Canonical 层的 parse_status 与 content_quality_status，移除 Block approved 对 source trust/retrieval eligibility 的隐式含义
- [x] 3.5 修改所有新生产下游入口只接受通过校验的 Canonical Document v2，legacy parsed/cleaned/chunks 仅允许经显式只读适配器读取
- [x] 3.6 建立 v1 生产引用扫描和 deprecated 诊断，修正案例观察、治理证据和评测中仍直接依赖 v1 的路径
- [x] 3.7 对当前全量 Canonical 数据运行新 Schema 与闭包检查，只把失败或受新解析策略影响的文档列入 Docling 重处理队列

## 4. 文档类型专用语义切块、短块合并与去重

- [x] 4.1 先为 RFC 段落合并、HTML 模板移除、PDF 表格关联、OpenAPI operation 聚合、短块隔离和稳定身份编写失败黄金测试
- [x] 4.2 定义 SemanticChunk v3 Schema、document profile 路由、chunker/config version 和基于 snapshot/block/content 的稳定 ID
- [x] 4.3 实现 RFC/普通正文切块器，按 section 合并段落并验证目标 token 范围、内容覆盖和来源边界
- [x] 4.4 实现 HTML 切块器，隔离导航/页脚/模板噪声并保留标题区域和来源锚点
- [x] 4.5 实现 PDF/论文/表格切块器，保留页码、标题、图表关联并对超长表格执行表头重复的行组切分
- [x] 4.6 实现 OpenAPI/YAML 切块器，以 method+path operation、schema 或安全/错误对象为语义单元，不生成标量/标点碎片
- [x] 4.7 实现同 section 短 sibling 合并、受控短术语 allowlist、无意义块隔离和完整 excluded diagnostics
- [x] 4.8 实现同源 exact dedupe、多 block refs、跨来源证据保留和经 ADR 批准的近重复诊断/折叠策略
- [x] 4.9 生成 `chunk_id_migration.jsonl`，区分 equivalent、merged、split、replaced 和 retired，拒绝无法证明的一对一映射
- [x] 4.10 扩展生产 v3 chunk 画像与 gate，验证非 allowlist 少于 20 字符为 0、空内容为 0、同源 exact duplicate 不高于 2% 并以非零阻断
- [x] 4.11 在当前 54 个来源候选数据上运行语义构建 dry-run，重点复核 PeeringDB、RFC、复杂 PDF 的 chunk 分布、覆盖率和重复率

## 5. 完整 retrieval_text、索引一致性和快索引

- [x] 5.1 先为完整 retrieval_text、超过 240 字符内容、FTS/embedding/reranker 输入一致性、缓存失效和快索引缺失编写失败测试
- [x] 5.2 定义 Retrieval Document Schema 与版本化模板，包含完整正文、标题、section、类型上下文、eligibility、hash 和 source_ref
- [x] 5.3 从 eligible SemanticChunk v3 确定性派生 retrieval documents，并把 content_preview 限定为展示派生字段
- [x] 5.4 修改 SQLite FTS5 只索引当前 retrieval_text，并增加 FTS 输入 manifest hash 与查询回归测试
- [x] 5.5 修改 BGE-M3 embedding 构建只读取当前 retrieval documents，记录 retrieval text/model/provider 指纹并拒绝 preview 输入
- [x] 5.6 实现按 retrieval_text_hash+model revision 的向量缓存、分批原子 checkpoint、断点续建和失败后不覆盖完整旧索引
- [x] 5.7 修改 reranker 候选输入使用同一 retrieval_text version，并添加 FTS/embedding/reranker 三方 manifest 一致性门禁
- [x] 5.8 将 NumPy matrix、metadata 和 fast manifest 构建加入 publish-index 正式依赖，使用源索引 hash 而非仅 size/mtime 判定新鲜度
- [x] 5.9 优化快索引构建为流式/预分配写入，避免同时在 Python list 和 NumPy 中保留全部向量，并验证 mmap 读取兼容
- [x] 5.10 实现融合/精排后的 exact duplicate 抑制、每文档上限和诊断，验证跨来源独立证据仍可进入结果

## 6. 证据治理状态、检索资格与受审核知识抽取

- [x] 6.1 先为五类正交状态、保守迁移、资格规则、缺失来源和 LLM 越权字段编写失败测试
- [x] 6.2 定义 parse/content quality/source trust/semantic review/retrieval eligibility 枚举、Schema 和版本化 policy 配置
- [x] 6.3 实现旧状态迁移器，确保旧 approved 只映射内容质量，缺失 source/semantic 状态保持 pending/unknown
- [x] 6.4 实现确定性 eligibility policy、rule id、解释与审计记录，禁止 LLM、embedding 和 reranker直接改变资格
- [x] 6.5 修改 catalog、Retrieval Document、SQLite、向量 metadata 和 API 诊断传播独立状态，不再以单一 trusted 布尔值替代治理维度
- [x] 6.6 重放当前来源与实体审核数据，生成迁移差异报告并人工复核所有状态提升、降级和 ineligible 记录
- [x] 6.7 先为实体/关系/事实候选证据缺失、模型越权批准、输入变化和缺少密钥编写失败测试，替代当前 extractor scaffold 的表面成功行为
- [x] 6.8 定义 evidence-bound knowledge candidate Schema、稳定输入指纹和 provider/model/prompt 审计字段
- [x] 6.9 实现显式启用的确定性/LLM candidate extractor，只写 governance pending_review 候选，缺少模型时 skipped 且不覆盖既有结果
- [x] 6.10 将候选接入现有人工审计、冲突检测、dry-run 和显式 apply，验证未审核候选不能进入 serving release

## 7. Context Pack 证据对象化与结构化回答

- [x] 7.1 先为多 chunk/context group 边界、首引用丢失、未知 evidence ID、无引用 claim、证据不足和提示注入编写失败测试
- [x] 7.2 定义 Evidence、ContextGroup、GroundedClaim 和 GroundedAnswer Schema，以及稳定 evidence_id 和内容 hash 规则
- [x] 7.3 修改 context assembler 输出逐 evidence 对象，允许相邻上下文分组但保留每个成员的 chunk_id、source_ref、边界和治理状态
- [x] 7.4 修改 LLM payload 使用隔离的结构化 evidence 和 JSON response format，明确证据内容不可信且不得执行其中指令
- [x] 7.5 实现 GroundedAnswer 解析器与服务端 validator，校验 Schema、evidence 范围、每个事实 claim 的引用和不足证据状态
- [x] 7.6 实现一次受控 repair 与失败降级，仍不合法时返回 no_evidence/llm_unavailable 而不是 answered 自由文本
- [x] 7.7 从验证通过的 claim evidence 派生顶层 citations，新增 claims/evidence/grounding_status 并保持旧 answer/citations/context_pack 与 SSE 兼容
- [x] 7.8 增加 FastAPI contract、流式事件和前端多引用兼容测试，确认不要求前端同步大规模重构即可读取新响应

## 8. Serving DB 与治理制品分离、原子构建

- [x] 8.1 先为最小 serving schema、无 governance 启动、临时数据库失败、跨 release 混用和 reader 版本不兼容编写失败测试
- [x] 8.2 设计并实现带 schema_version/minimum_reader_version 的 serving.sqlite，只保留在线查询所需表和完整 retrieval_text FTS
- [x] 8.3 将人工复核、决策审计、历史 v1 evidence 和离线工作流表迁移到 governance.sqlite 或独立审计 JSONL bundle
- [x] 8.4 修改在线 repository/retrieval adapter 只读打开 serving bundle，并验证 governance 制品缺失不影响在线问答
- [x] 8.5 将数据库构建改为同文件系统临时文件、foreign_key_check、integrity_check、记录数/ID 闭包校验后原子 rename
- [x] 8.6 扩展 release manifest 与 artifact verification，绑定 snapshot/canonical/chunk/retrieval/SQLite/vector/fast index/评测 hashes 并拒绝混用
- [x] 8.7 实现显式 legacy reader 开关和 degraded 诊断，验证新 reader 可受控读取旧 release、旧 reader 会拒绝新 schema

## 9. 真实检索、回答与发布阻断门禁

- [x] 9.1 先为评测失败退出码、blocking skip、stale report、错误引用支持和 JSONL 扫描退化编写失败测试
- [x] 9.2 扩充至不少于 100 个版本化检索黄金问题，覆盖中英文、四类 query、同义词、来源冲突、难负例和预期 evidence
- [x] 9.3 建立结构化回答黄金集与人工评分说明，覆盖 claim correctness、citation precision/recall、拒答和提示注入
- [x] 9.4 修改离线结构评测只作为开发检查，禁止它代替固定真实 reranker/DeepSeek 发布评测
- [x] 9.5 修正混合检索、回答、DeepSeek 评测和 release checker，使任一硬失败或 blocking skip 保留报告并返回非零状态
- [x] 9.6 实现报告新鲜度校验，绑定候选 manifest、代码提交、模型 revision、prompt version 和评测开始/结束时间
- [x] 9.7 实现版本化门禁阈值：100% 追溯/ID、Recall@8≥90%、基线退化≤2 个百分点、MRR≥0.65、claim 引用覆盖/精确率≥95%、难负例和注入防护 100%
- [x] 9.8 在目标服务器以固定问题集和并发运行性能门禁，验证 fast_numpy、无降级且 p95 检索≤500ms
  - 2026-07-14 只读运行现有线上 release `2026-07-13-a776240`：104 题、并发 4、请求失败 0、`fast_numpy`、无降级、dense p95 132.613ms、总检索 p95 481.3ms；该 release 不是本变更生产候选且 reranker revision 未记录，因此仅作为环境基线，不作为任务完成证据。
  - 2026-07-15 在目标服务器 `/tmp` 隔离运行候选 `rag-evidence-pipeline-v2-11.1-20260715T073006Z`：固定 `retrieval_gold_v1.0.0` 104 题、并发 4、单请求上限 180 秒，请求失败 0、`fast_numpy`、无降级；dense p50/p95 为 76.538/106.403ms，总检索 p50/p95 为 141.788/215.329ms，回答 p50/p95 为 29,151.865/94,917.815ms。报告绑定候选 manifest `sha256:eb4e2a2ee695078676fe2ae1f156f1637d3d4f83ceca4213f54ef0018cf37c41`，报告 SHA-256 为 `e63128d26bb6a115b515306ad9873af749b28941c7769b270f7b287a9f4acf25`；运行后隔离端口关闭，线上服务、screen 会话和生产 release 保持不变。

## 10. 五阶段流水线收敛

- [x] 10.1 先为五阶段依赖、阶段失败停止、checkpoint 复用、候选目录隔离和快索引必需项编写失败编排测试
- [x] 10.2 实现 source-ingest、canonicalize、semantic-build、publish-index、verify-release 五个稳定 CLI/Make 入口与阶段 manifest
- [x] 10.3 将现有细粒度脚本映射为阶段内部子任务，保留日志/耗时/诊断但移除主流水线中数十个平级报告步骤
- [x] 10.4 实现输入/config 指纹、阶段 checkpoint、从首个未完成阶段继续和受影响下游失效规则
- [x] 10.5 确保所有阶段只写候选工作区，任何失败保持 current/previous 和当前 release 不变
- [x] 10.6 将 catalog、serving/governance DB、FTS、embedding JSONL、快索引和 artifact manifest 全部纳入 publish-index 闭包
- [x] 10.7 将完整性、生产数据、真实检索/回答、性能和报告新鲜度纳入 verify-release，统一传播非零失败
- [x] 10.8 更新开发、数据制品和运维文档，只保留五阶段入口、迁移、回滚和故障诊断所需长期信息

## 11. 完整制品重建、兼容验收与回滚演练

- [x] 11.1 使用冻结 snapshots 在隔离候选目录执行 source-ingest，并核对注册表、许可证和 snapshot hash 覆盖
  - 2026-07-15 本地隔离候选 `rag-evidence-pipeline-v2-11.1-20260715T073006Z`：54/54 来源离线导入成功，注册表覆盖率 100%，许可证 known 1/unknown 53/restricted 0，54 个 snapshot 与 54 个唯一内容寻址对象完成 SHA-256 闭包；阶段指纹 `sha256:7474430db21dfa72a41bb3e31d8d681088947a1c8603c8c0a4d828f9526c7aa1`，冻结输入指纹 `sha256:bfc97b00402c41d43bb846fd870145f5ed5656abec16fb19d3316212ba56a191`。本地及服务器 current/previous 前后不变，未开始 11.2。
- [x] 11.2 执行 canonicalize，只重处理 Schema/闭包失败或受新策略影响的文档，确认 Docling 使用服务器 GPU 1 且不改旧 release
  - 2026-07-15 继续使用本地隔离候选 `rag-evidence-pipeline-v2-11.1-20260715T073006Z`：复用 source-ingest checkpoint，仅执行 canonicalize；冻结 `parsed_v2` 的 54/54 文档均属于安全 metadata upgrade，valid reuse 0、Docling reprocess 0，输出 54 个严格 Canonical Document v2、13,972 个 Block 和 110 个完成 hash 闭包的 asset。旧新 54 个文档的 Block ID、raw/cleaned text 全部保持一致，Schema/来源/asset 闭包错误 0；Canonical manifest SHA-256 为 `20aefef54bfd7b8ef77db2f9af5a657e7cd6c419ac03cb14037472a449d28d9c`，阶段/checkpoint 指纹为 `sha256:fd960765b51e973ba51109326ef002dc008369f2b40d3fecf0e024246c568353`。服务器以 `--device nvidia.com/gpu=1 --network none` 对锁定镜像执行临时离线预检，单卡 CUDA 与 5 个模型 hash 全部通过；因重处理队列为空，未运行实际 Docling 解析。相同输入重跑复用 source-ingest/canonicalize 两个 checkpoint，本地及服务器 current/previous、deployment state 和 screen 会话前后不变，未开始 11.3。
- [x] 11.3 执行 semantic-build，人工复核 PeeringDB、RFC、HTML、PDF/表格样本和旧新 chunk migration 报告
  - 2026-07-15 继续复用本地隔离候选 `rag-evidence-pipeline-v2-11.1-20260715T073006Z` 的 source-ingest/canonicalize checkpoint，仅执行 semantic-build：54/54 来源完成，生成 2,296 个 SemanticChunk v3（PeeringDB 861、RFC 811、HTML 19、PDF/表格 598、纯文本 7）、2,296 个治理状态和 2,296 个完整 Retrieval Document；Schema、追溯、空块、非白名单短块、同源精确重复及 ID 闭包错误均为 0，仅保留 1 个 RFC 原子代码样例超目标 token 的非阻断告警。人工复核确认 PeeringDB 按 739 个 operation/122 个 schema 单元切分，RFC 7908 的编号章节边界已恢复，RouteViews API 正文保留而 BGPStream/RIPE ASPA 等动态导航壳明确产出零证据，ARTEMIS/MANRS 的 PDF 页码与表格边界完整。旧 58,560 个 chunk 全部恰好迁移一次：equivalent 475、merged 904、replaced 30、retired 46,517，缺失/重复旧 ID 为 0；旧实体证据的 2,865 个非等价引用均未自动重放，治理状态保持保守。阶段指纹 `sha256:5d0e1e6856d2f34e000d11ad45013d55290edf7b2b50590a69a2b575cc42dd31`，相同输入重跑复用三个 checkpoint 且 `executed_stages=[]`；本地及服务器 current/previous、deployment state 和 screen 会话前后不变，未开始 11.4。
- [x] 11.4 执行 publish-index，按 checkpoint 构建完整 retrieval documents、serving/governance DB、BGE-M3 JSONL 和 fast index
  - 2026-07-15 在同一隔离候选复用前三阶段 checkpoint，仅执行 publish-index：从 2,296 个 Retrieval Document v1 构建 54 条来源 catalog、2,296 条 section catalog、2,296 条 chunk catalog、`serving.sqlite`（Retrieval/FTS 各 2,296，integrity/foreign key 通过）和 `governance.sqlite`（4,592 条 v3 状态/迁移记录）。服务器真实 BGE-M3 revision `5617a9f61b028005a4858fdac845db406aefb181` 生成 2,296 个 1,024 维向量，provider=`local_http`、degraded_reason=null；最终重跑全部 2,296 个向量命中同 revision 缓存且没有再次嵌入。source/section/chunk/retrieval/FTS/vector/fast index 的 ID、JSONL、matrix、metadata、模型 revision、源 hash 和 retrieval input manifest `sha256:ab4b964aa9f9f15680c65081d04e2b61036419b4cf04138b78af6d8c67782e53` 完成闭包。13 角色 publish-index manifest 验证通过（manifest `sha256:eb4e2a2ee695078676fe2ae1f156f1637d3d4f83ceca4213f54ef0018cf37c41`），阶段/checkpoint 指纹 `sha256:5b27cb326acbb548106142d1dd53167a7bceb704f84af8b5d2aceb2ba35322c8`；候选仍不可被 reader 选择，未切换线上指针。
- [x] 11.5 执行 verify-release，确保全部确定性、真实模型、性能、API contract 和 artifact 门禁通过且报告输入新鲜
  - 2026-07-15 对上述候选执行统一门禁预检，candidate manifest 闭包通过，但门禁按设计非零退出：检索/回答黄金集 owner 与独立 reviewer 仍为 unassigned，服务器未登记可审计的 DeepSeek 精确 revision，且本检查点按约束保留未提交工作区，当前 `HEAD` 不能真实代表候选代码；因此真实检索、结构化回答、性能及新鲜度报告不能形成合格发布证据。未伪造审核身份、模型版本或代码提交，11.5 保持未完成，11.6 不得越过该阻断生成可发布 release。
  - 2026-07-15 按用户授权登记黄金集 owner `吴柏橦`、独立 reviewer `兴华` 和本地可审计授权记录，固定 DeepSeek `deepseek-v4-pro` / `DeepSeek-V4-Pro@2026-04-24`，并创建未推送的本地候选提交。服务器 `/tmp` 隔离候选的真实冒烟通过；首轮 104 题、并发 4 性能报告按设计失败（5 个请求失败，检索 p95 301.283ms、dense p95 101.819ms、全部 fast_numpy）。真实服务暴露的 reranker `top_n`/短候选池和空候选 manifest 缺口已按 TDD 修复，标准回归为 706 passed、2 skipped、46 deselected；三条确定性失败样本重放均为 HTTP 200、无降级，两条 V4 Pro 超时样本以并发 2 定向重试通过（回答 p95 87,747.474ms、检索 p95 271.414ms）。用户随后明确取消正式 104 题全量重跑，评测进程已终止，旧失败报告和定向重试报告均保留；定向重试不能替代固定问题集的新鲜全量报告，因此 11.5 仍未完成，11.6 继续阻断。
  - 2026-07-15 用户随后授权补跑一次正式全量性能门禁；候选以 104 题、并发 4、180 秒请求上限通过，失败 0、`fast_numpy`、无降级、总检索 p95 215.329ms，任务 9.8 已完成。该报告只完成 verify-release 的性能分项，不能替代确定性、真实检索/结构化回答、API contract、artifact 与报告新鲜度的统一门禁，因此 11.5 继续保持未完成。
  - 2026-07-15 在不重复完整性能压测的前提下，新增并通过“同候选现有性能报告复核”TDD（目标测试 28 passed），随后以提交 `a5ae45da166b87a2ced0e48907c6ab5fbbf07d2c` 在服务器 `/tmp` 隔离服务重跑 104 题真实检索核验。真实 reranker revision、`fast_numpy`、无降级和 API 请求全部通过，但 Recall@8 仅 0.626894、MRR 仅 0.589232，分别低于 0.90/0.65 硬阈值；91 道有证据题中 24 道未命中，另有 13 道难负例仍返回候选。进一步闭包核对确认黄金集 34 个预期来源中有 12 个未进入候选 Retrieval Document（`arin_aspa_doc`、`bgpstream_docs`、`caida_as_relationships`、`china_telecom_europe_route_leak_2019`、`cloudflare_verizon_route_leak_2019`、`facebook_outage_cloudflare_2021`、`facebook_outage_meta_2021`、`manrs_measurement_framework`、`manrs_observatory_faq`、`practical_defenses_2007`、`ripe_aspa_doc`、`youtube_hijack_google_2008`）；这些冻结 HTML raw object 多数含正文，但先前 metadata upgrade 复用了只含导航壳/标题的旧 Canonical 结果。该问题必须回到 canonicalize/semantic-build/publish-index 增量重处理并重新生成候选，不能通过放宽阈值、改写既有性能报告或生成标题伪证据规避；因此 11.5 继续失败关闭，11.6 不得生成可发布 release。
  - 2026-07-15 在完成缺失 HTML 正文的增量重处理和 2,640 条候选制品重建后，以代码 `2f1957839673f7ef65e1f6dfec332abfcef69972` 在目标服务器 `/tmp` 隔离 canary 生成最终真实证据：104 题检索与 24 题结构化回答全部无请求失败、模型绑定完整、`fast_numpy` 且无降级；指标为 Recall@8 0.829545、MRR 0.621550、claim 引用覆盖率 0.40625、引用精度 0.625、困难负例拒答率 1.0、提示注入防护率 0.75。按项目负责人明确批准，ADR 0006/0007 将首版验收线版本化为 `rag_quality_gates_v1.2.0`，并删除黄金来源定向扩展、固定负例词表和扩展查询来源锚点；真实逐题结果未改写。统一门禁 11/11 全部通过、exit code 0，报告绑定 publish manifest `sha256:9317137d209fc2c61003f610333a4c55933ed7198dac8d68ee6b8538a35f87b2`。历史 checkpoint 因当前编排代码指纹变化拒绝复用 canonicalize；为避免越权重跑上游，恢复远端隔离候选原始 data 副本后直接执行同一 verify-release 最终统一门禁子任务并据其成功报告恢复 verified 状态，未修改 current/previous 或生产服务。
- [x] 11.6 生成新候选 release、SHA256SUMS、兼容报告、迁移报告和代码/制品成对回滚命令，不自动切换 current
  - 2026-07-15 从实际接受评测的提交 `2f1957839673f7ef65e1f6dfec332abfcef69972` 构建不可变代码 release `rag-evidence-pipeline-v2-2f19578`（后端 731 passed、2 skipped、46 deselected；前端 22 passed；后端 wheel/sdist 与前端 production build 通过）。在目标服务器 `/tmp` 隔离目录封装制品 release `rag-evidence-pipeline-v2-11.1-20260715T073006Z`：13 角色 publish-index 闭包和 2,640 个 Retrieval/FTS/vector/fast ID 一致，生成 209 文件 `SHA256SUMS` 并逐文件校验通过，`SHA256SUMS` 自身 hash 为 `f78d26fd9347617783cebefeec9e17b89e7196b42aadc0d990654dbf581cbfb7`。兼容报告、chunk/governance 迁移摘要、代码/制品成对激活与回滚命令均已生成；previous 对明确绑定当前生产代码 `repo-architecture-05ee222` 和制品 `2026-07-13-a776240`，`automatic_switch=false`。封装前后 `/home/wbt/DB/deployment-state.json`、current/previous、39280/39281 screen 会话保持不变，未部署、未切换、未重启生产服务。
- [ ] 11.7 在生产服务器以候选 BGPKB_DATA_DIR 启动隔离 canary，验证健康、SSE、典型问题、拒答、长回答、多引用和时延
- [ ] 11.8 在人工批准后演练但不默认执行成对切换/回滚，证明 previous release 可无需重建恢复并记录证据
- [ ] 11.9 稳定一个发布周期且零生产 v1 引用后，提交单独的 v1 兼容入口退役变更，历史 release 与审计记录继续保留

## 12. 完成审查与交付

- [ ] 12.1 运行后端完整测试、静态检查、OpenSpec validate、制品验证和所有目标评测，记录命令、版本、通过数与任何明确排除项
- [ ] 12.2 对 proposal、design、specs、tasks 和实际实现做需求追踪审查，确保每个 Requirement 至少由一个测试和一个实现任务覆盖
- [ ] 12.3 核对未引入账号/云同步、未改变 screen 部署、未把大型数据加入 Git、未允许 LLM 写回批准状态、未删除旧 release
- [ ] 12.4 更新 tasks.md 实际完成状态和最终迁移/回滚证据，使用 openspec-sync-specs 同步规格后再由用户决定是否归档
