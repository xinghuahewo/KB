# RAG 证据流水线 v2 迁移基线

本基线冻结于 2026-07-14（Asia/Shanghai），用于 `rag-evidence-pipeline-v2` 的迁移比较。采集过程只读访问线上服务和不可变 release；未修改 `current`、`previous`、screen 会话或任何线上文件。

## 代码与制品

- 实施工作树提交：`5a1837908d8fe294650e9ed5c577e4dada4554eb`。
- 线上代码 release：`repo-architecture-05ee222`。
- 线上代码提交：`05ee222e439d22e2cf52004b07c1ca0d9573526c`。
- 前端构建 SHA-256：`1acb5287d789ef8a94663b7c85fcd86981776474d24181509febbd1583726f66`。
- 当前制品 release：`2026-07-13-a776240`。
- 上一制品 release：`2026-07-10-93a4c97`。
- `SHA256SUMS` SHA-256：`4617da2b38ef3e63e77da55b7a0d641db87f2339c8f1426f84e9d3f3690bec90`。
- `SHA256SUMS` 登记文件数：1296。

## 线上健康与检索

- `bgpkb_frontend_wbt`、`bgpkb_fastapi_wbt` 均处于 Detached 运行状态。
- 39280、39281、8011、8012 均监听。
- 前端和后端 `/health` 均返回 SQLite `integrity_check=ok`。
- 固定问题“什么是 RPKI 路由起源验证？”：`answer_status=answered`、`vector_status=complete`、`rerank_status=complete`、`vector_index_mode=fast_numpy`、`degraded=false`。
- 本次真实请求检索耗时 146.645 ms，向量耗时 86.614 ms，reranker 耗时 177.133 ms；该值是单次冻结证据，不替代后续固定并发 p95 门禁。

## 生产数据统计

| 指标 | 冻结值 |
| --- | ---: |
| 来源数 | 54 |
| 来源审核状态 | approved 5；pending 49 |
| chunk 数 | 58,560 |
| 少于 20 字符 chunk | 40,957（69.9402%） |
| 规范化预览精确重复的冗余记录 | 44,239（75.5447%） |
| chunk 字符中位数 | 2 |
| chunk 字符 p95 | 205 |
| PeeringDB API chunk | 41,857（71.4771%） |

## 测试与评测

- 修复前后端稳定基线：450 passed、2 skipped、46 deselected。
- 外置 `BGPKB_DATA_DIR` 评测 CLI 修复后：451 passed、2 skipped、46 deselected。
- 制品校验：通过；SQLite `ok`，向量维度 1024，JSONL 向量 58,792，快索引 chunk 58,560，模式 `fast_numpy`。
- 现有混合检索集：20 题，19 通过、1 失败；Recall@5 79.4118%，Recall@8 88.2353%，MRR 0.6740，无证据拒答率 100%。
- 现有结构回答集：20 题，20 通过；该评测使用 `StructureOnlyClient`，只作为结构基线，不能替代 DeepSeek 发布评测。
- 真实 DeepSeek 单题 smoke：回答成功且使用真实 reranker；现有批量真实回答评测尚未具备可作为 release gate 的 owner、版本绑定和非零失败传播。

## 已知基线问题

1. 混合检索 Recall@8 为 88.2353%，低于 v2 提案的 90% 初始门槛；这是待改进的冻结语义基线，不应通过放宽阈值掩盖。
2. 现有混合检索 CLI 即使有失败题也返回成功；统一非零失败传播属于任务组 9。
3. 回答评测 CLI 原先用 `RESULTS_PATH.relative_to(ROOT)` 展示外置制品路径，导致源码/制品分离后非零崩溃。本轮已通过失败测试复现，并改用仓库逻辑路径 `paths.rel`；服务器 `/tmp` + overlay 复验 20/20，通过后临时目录已删除。
4. 当前回答 citations 仍包含 context pack 全集，不能证明 claim 与 evidence 的逐项绑定；这是本变更后续任务的迁移起点。

## Source registry 首次 dry-run

- 注册表版本：`2026-07-14-v1`，共 54 个唯一 `source_id`，与线上 source catalog 完全对齐；原硬编码列表中的 53 个远端来源和受控内部来源 `context_2026` 均已登记。
- 在服务器 `/tmp/bgpkb-rag-v2-checkpoint-a` 隔离目录运行，legacy root 只读指向当前 release 的 `data/sources/raw`。
- 结果：54 个来源完成 hash，digest 覆盖 54/54，missing 0，failed 0。
- dry-run 未创建 `objects/`，未修改 raw 文件、release、`current` 或 `previous`；退出后临时代码、manifest 和目录全部删除。
- 本地来源测试：10 passed，覆盖 Schema、license 缺失、source_id 重复、对象复用、条件请求头过滤、legacy 只读、单来源失败隔离、原子 manifest、dry-run 和 Git ignore。
- 检查点 A 完整无制品回归：485 passed、2 skipped、46 deselected；新增目标测试均已纳入该回归。

## Canonical v2 全量迁移扫描

- 扫描对象：不可变 release `2026-07-13-a776240/data/corpus/parsed_v2`，共 54 个文档；扫描程序仅同步到服务器 `/tmp/bgpkb-rag-v2-checkpoint-a`，未写 release。
- 严格新契约结果：valid 0、metadata upgrade 54、Docling reprocess 0。54 个旧文档均具备完整旧 Block 结构和稳定身份，只缺 source snapshot、处理指纹和拆分后的状态字段，因此进入确定性元数据升级队列，不应重新消耗 Docling GPU。
- 来源闭包交叉核对：注册表 54/54、raw 文件 54/54、Canonical 文档 54/54；旧 Canonical `source_sha256` 与对应 raw 内容 SHA-256 一致 54/54，失败 0。
- v1 生产依赖扫描：blocking 0、deprecated 29。所有保留引用均登记用途与退役检查点；案例观察和历史治理证据已强制走显式只读适配器，评测代码没有直接读取 parsed/cleaned/chunks v1。
- 迁移扫描报告 SHA-256：`2a803b7aaf518873a9d044720e2398dca2070d2d78ad722030ac948776ec0258`。报告只保存在临时目录用于本次核验，摘要和闭包结论固化于本基线。
- 结论：当前数据不需要因契约升级全量重跑 Docling；后续只需从冻结 snapshot 补齐严格元数据。任务 4 的文档类型新解析策略若明确影响某来源，再单独把该来源加入重处理队列。

## SemanticChunk v3 全量候选 dry-run

- 执行位置：服务器 `/tmp/bgpkb-rag-v2-checkpoint-b-4-11`；代码和输出均位于 `/tmp`，输入只读指向不可变 release `2026-07-13-a776240` 的 `data/sources/raw` 与 `data/corpus/parsed_v2`。未修改 `/home/wbt/DB`、screen、`current`、`previous`、线上 release 或服务端口。
- 执行入口：`python -m bgpkb.ingestion.semantic_build_dry_run`，注册表版本 `2026-07-14-v1`，固定 snapshot 时间 `2026-07-14T00:00:00Z`。旧 Canonical 仅在内存中补齐 source snapshot、runtime、处理指纹和拆分状态，不写回旧文档。
- 来源闭包：54/54 完成，失败 0；所有文档的非结构 Block 均进入 chunk 或带原因的隔离诊断，最低逐来源内容 Block 覆盖率 100%。
- 候选结果：去重前 2,143 个 chunk，去重后 2,142 个；隔离 852 个 Block，其中非语义类型 404、空内容 371、非 allowlist 短噪声 77；同源 exact 折叠 1 条，近重复只生成诊断，不自动折叠。
- 文档类型分布：RFC 11 个来源/626 chunks；HTML 29/52；PDF/表格 12/596；OpenAPI/YAML 1/861；受控 plain text 1/7。
- PeeringDB 从冻结基线的 41,857 个标量级碎片收敛为 861 个语义块，其中 operation 739、schema 122，最大 788 estimated tokens；method/path、长 overview、request body、response family 和嵌套 property 均按 ADR-0005 边界组织。
- 重点样本：`rfc7908` 11 chunks、最大 800 tokens；`artemis_2018` 67 chunks（含 6 个表格块）、最大 799；`bear_2025` 33 chunks、最大 780；`manrs_netops_actions` 41 chunks（含 2 个表格块）、最大 375；以上内容 Block 覆盖率均为 100%。
- 硬门禁：Schema 错误 0、空内容 0、非 allowlist 少于 20 字符 0、缺失追溯 0、同源 exact duplicate 0（0%），blocking issue 0。唯一非阻断告警是 `rfc9083` 的一个 946-token 原子 JSON code 示例；按“代码原子块不截断、长度尾部默认告警”保留。
- 连续两次稳定候选构建的 chunk、隔离和去重诊断 hash 一致。最终文件 SHA-256：`semantic_chunks_v3.jsonl` 为 `af67dc62a7620865bb92246cc0374e5637fbbaf122ae3781581392210f6ee057`；`semantic_excluded_blocks_v3.jsonl` 为 `2920ef9025642cfb38c2bf5f67787e411ccb5dfa9a618b4475b1a60bda75ff50`；`semantic_dedup_diagnostics_v3.jsonl` 为 `d7bc643bd423274dde35b303f2d0253a2877d4e3a8e07302cd741c196a3c0d05`；质量报告为 `709abb2ec37246c829e701ab99bbb1b32854426cfc07c8ae8fbfc80a806fc603`；dry-run 摘要为 `c87fa864fd4b91c62708067393899296cb383a711432f3fe682d0030d591de23`。
- 该结果只是候选数据审查证据，不是 serving release；未构建 retrieval document、FTS、embedding 或快索引，也未切换线上读取路径。

## 检查点 B：统一检索文档与索引一致性

- 新增闭合的 Retrieval Document v1 Schema 和 `retrieval_text_v1.0.0` 模板。完整正文、标题、section、文档类型和语义单元共同形成唯一 `retrieval_text`；`content_preview` 只从正文派生，最多 240 字符，不再作为检索模型输入。
- Retrieval Document 只能从显式 `eligible` 的 SemanticChunk v3 确定性派生；由于正交治理状态与生产 eligibility policy 属于任务组 6，本检查点没有擅自把 2,142 个候选 chunk 提升为生产可检索状态，也没有构建或切换线上制品。
- SQLite FTS5 的 `chunk_fts` 只含 `retrieval_doc_id`、`chunk_id` 和完整 `retrieval_text`，并在 meta 中记录 FTS input manifest hash。超过 240 字符后的尾部黄金词已通过查询回归，旧 preview 不再入新 FTS。
- BGE-M3 构建入口只接受同一 Retrieval Document v1 manifest；旧 chunk、entity、glossary、evidence template 或 preview-only 输入会失败。embedding manifest 和向量记录绑定 retrieval input、text hash/version、模型 revision、归一化和 provider contract 指纹。
- embedding cache key 同时绑定 retrieval text hash、模型名、模型 revision、归一化和 provider contract。每个成功批次原子写 checkpoint；中途失败保留已完成批次且不覆盖上一份完整索引，相同 revision 可续建，revision 变化会强制全部重算。
- FTS、embedding 与 reranker 使用同一 input manifest；新 release 任一组件 hash 缺失或不一致会在精排前失败。旧 release 只保留显式兼容读取，不会被误标为 v1 新契约。
- 快索引升级为 `fast_vector_index_v2`：两遍扫描源 JSONL，预分配 `.npy` memmap 并逐行写 metadata，不同时保留 Python 向量列表和完整 NumPy 副本。manifest 绑定源索引 SHA-256、matrix/metadata SHA-256、eligibility 集合和 retrieval input manifest。
- 源索引 SHA-256 在构建和候选 release 验证阶段强制检查；在线读取依赖已验证的不可变 release，只 mmap matrix/metadata，不在进程冷启动重新扫描大型 JSONL，避免恢复旧的秒级性能问题。
- 融合后的候选在精排前执行同来源 exact duplicate 抑制和每文档 2 条上限，所有决定进入 diagnostics；相同文本来自不同来源时仍作为独立证据保留。
- 检查点 B 完整无制品回归：525 passed、2 skipped、46 deselected；相较任务组 4 完成时新增 17 个通过用例。未提交、未部署、未切换 `current`/`previous`，服务器 `/home/wbt/DB` 和在线服务未修改。

## 检查点 C1：正交治理状态与迁移重放

- 新增 `evidence_governance_state_v1` 闭合 Schema 与 `retrieval_eligibility_v1` 版本化策略，独立维护 parse、content quality、source trust、semantic review 和 retrieval eligibility；每个资格结果均包含 policy version、rule id、中文原因、输入指纹和 policy 指纹。
- 旧 `approved` 只迁移为内容质量 approved。来源可信只读取独立 source catalog 的 `review_status + trust_level`，语义状态只读取可精确关联 chunk_id 的实体审核证据；缺失状态保持 pending/unknown。LLM、embedding 和 reranker 直接修改治理字段或检索资格会被拒绝。
- Retrieval Document、catalog、SQLite/FTS、embedding/向量 metadata 与混合检索 API 诊断均传播完整治理对象；`trusted` 只作为旧兼容字段，不再替代五个治理维度。`eligible_with_caution` 可形成候选检索文档，但本检查点没有实际构建或发布任何生产检索制品。
- 真实重放只在服务器 `/tmp/bgpkb-rag-v2-checkpoint-c1-6-6` 执行。输入为检查点 B 保留的 2,142 条 SemanticChunk v3、不可变 release `2026-07-13-a776240` 的 54 条 source catalog 和 246 条 entity evidence；未修改 `/home/wbt/DB`、screen、线上 release、`current` 或 `previous`。
- 重放结果：parse=parsed 2,142；content quality=approved 2,142；source trust=trusted 260、pending 1,882；semantic review=unknown 2,142；retrieval eligibility=eligible_with_caution 2,142；ineligible 0；阻断 0。
- 260 条来源可信提升全部来自五个独立 approved 来源：`context_2026` 7、`rfc4271` 215、`rfc6811` 12、`rfc7908` 11、`rfc9234` 15。旧 entity evidence 无法与新 v3 chunk ID 证明一对一等价，因此没有任何语义状态提升。
- 2,142 条相对旧内容质量 approved 的资格降级均为 `retrieval.pending_governance_caution`，原因是 semantic review 保守保持 unknown；逐条集合校验确认 promotion 260、downgrade 2,142、ineligible 0 的 ID 闭包完整且无重复。
- 临时报告 SHA-256：`evidence_governance_migration_v1.jsonl` 为 `6ae0f3b09dc052ad9c734ade0580a78282d6140546a38dfa3f93aa95a9cacf68`；差异 JSON 为 `fab1fa00b4125dc0b92d12701c029ffeb78dc9f4b267ce6b0bb53127488a1b58`；中文报告为 `788d9eedca88abd285dd4f0868faa4fad17755de622a2ff313a479fb690d41dc`。

## 检查点 C2：证据绑定知识候选与人工应用边界

- 旧 `extract_entities.py` 不再在未执行任何抽取时打印表面成功，而是转发到显式启用的知识候选工作流。默认 provider 为 `disabled`；未显式选择时不读取候选证据、不调用模型、不创建或覆盖输出。
- 新增闭合的 `evidence_bound_knowledge_candidate_v1` Schema，分别约束 entity、relation 和 fact payload。每条有效候选必须绑定至少一个当前批次 evidence ID，并由系统派生 source refs、稳定 input fingerprint 和 candidate ID。
- input fingerprint 同时绑定候选 payload、evidence ID、证据内容 hash、source ref、provider、model revision 和 prompt version；任一输入变化都会形成新候选身份，旧人工决定不能自动复用。
- 模型只允许建议 `candidate_type`、`payload`、`evidence_ids`、`confidence` 和 `reason`。模型返回 approved、trusted、semantic review、retrieval eligibility、candidate ID 或其他治理字段时，记录会进入错误集合且不会进入审核队列；所有有效候选的治理状态固定为 `pending_review`。
- 支持显式 `deterministic` 与 `deepseek` 两类 provider。确定性模式使用版本化术语规则；DeepSeek 缺少密钥或模型不可用时返回 `skipped`，并原样保留候选、错误集和报告的既有版本，不生成 mock 回退结果。
- 人工审核复用现有指纹、审核人和带时区审核时间校验；同一 subject+predicate 的互斥 approved relation 会整组标记为 `blocked_conflict`。dry-run 只写 apply preview，显式 `--write` 也只生成治理侧 `approved_for_next_release` 集合，不修改当前 serving release。
- 原始 `pending_review` 候选不能作为 serving 知识输入；只有当前指纹一致、人工批准且审计状态为 `ready_to_apply` 的记录可形成下一候选 release 输入。本轮没有运行真实 LLM，没有生成生产候选，没有访问服务器，也没有构建、发布或切换任何线上制品。
- 新增知识候选目标测试 21 个；完整后端回归为 571 passed、2 skipped、46 deselected。Python compileall、`uv build`、OpenSpec strict validation 和 `git diff --check` 均通过。

## 正式检查点 C（第一部分）：Context Pack 与结构化接地回答

- 新增闭合的 `evidence_v1`、`context_group_v1`、`grounded_claim_v1` 和 `grounded_answer_v1` Schema。Evidence ID 稳定绑定 chunk ID、source ref 和内容 SHA-256；内容变化会形成新 ID，成员边界、五维治理状态和检索分数均为显式字段。
- Context assembler 在保留旧 `context_units`、`content` 和 `citations` 的同时新增逐条 `evidence` 与 `context_groups`。相邻 chunk 可以组合，但每个成员仍保留 evidence ID、chunk ID、source ref、字符起止边界和完整 `retrieval_text`，不再只保留首个来源或退回 240 字符 preview。
- DeepSeek 请求使用 JSON response format 和隔离的结构化用户 payload。system 规则明确把外部 evidence 视为不可信数据，禁止执行其中要求忽略系统规则、改变身份、批准治理状态或越界引用的指令；提示注入文本不会进入 system 消息。
- 服务端只接受合法 `grounded_answer_v1` JSON 对象，拒绝未知 evidence ID、事实 claim 无引用、Schema 非法、顶层与 claim evidence 集不一致以及非法 Context Evidence。证据不足必须使用空 answer/claims/evidence IDs 的显式状态，不能以自由文本冒充 answered。
- 首次 grounding 失败最多执行一次受控 repair，只向模型提供错误码、允许 evidence IDs 和结构修复规则。目标测试覆盖 4 类确定性拒绝、1 次 repair 成功、1 次 repair 后仍失败降级、1 次证据不足降级和 1 次模型不可用降级；没有第二次 repair，也没有自由文本 answered。
- 顶层 `citations` 只从验证通过、实际被 claim 使用的 Evidence 派生；未使用候选只保留在 `context_pack`。成功响应向后兼容保留 `answer`、`citations`、`context_pack`，并新增 `claims`、`evidence`、`grounding_status`；所有降级响应的新数组字段为空。
- FastAPI 路由未变化，OpenAPI 以兼容扩展声明新字段。SSE 顺序保持 `accepted → retrieval → rerank → context_pack → generation → done`，done payload 透传结构化字段。前端同步和流式代理可直接读取 claims/evidence/groundingStatus，旧 citations 多引用展示路径继续工作，不需要同步大规模界面重构。
- 本轮新增 20 个后端通过用例，完整后端回归为 591 passed、2 skipped、46 deselected；前端为 22 passed。离线 `StructureOnlyClient` 也改为输出同一 GroundedAnswer 契约，但仍只用于开发结构检查，不能替代真实 DeepSeek 发布评测。Python compileall、`uv build`、`corepack yarn build`、OpenSpec strict validation 和 `git diff --check` 均通过。
- 本轮未访问服务器，未调用真实 LLM，未构建或发布 SQLite、retrieval documents、embedding 或快索引，未修改 `/home/wbt/DB`、screen、`current` 或 `previous`，也未提交、推送、合并或部署。

## 正式检查点 C（第二部分）：Serving DB 与治理制品分离

- 新增 `serving_sqlite_v1` 与 `governance_sqlite_v1` 两个独立契约。`serving.sqlite` 只保存在线来源、实体、关系、chunk、Retrieval Document、词项/术语和完整 `retrieval_text` FTS；人工复核、决策审计、历史 v1 evidence、候选与离线工作流统一进入 `governance.sqlite` 的版本化记录集合。
- `serving.sqlite` 的 meta 显式记录 `schema_version`、`minimum_reader_version`、release ID、Retrieval Document manifest hash、记录数和数据库角色。FTS 只索引完整 `retrieval_text`，不打开或依赖治理数据库；治理制品不存在时，BM25、在线状态投影以及 stats/actions/progress 兼容响应仍可工作。
- 两个数据库均在目标文件同目录的唯一临时路径构建。serving 候选必须通过 `foreign_key_check`、`integrity_check`、retrieval/chunk/FTS 记录数和 chunk ID 闭包；governance 候选必须通过数据集 manifest 计数闭包和完整性检查，随后才以 `os.replace` 原子替换。
- 原子失败测试先保留完整旧 serving 文件，再用重复主键让新候选在真实插入阶段失败；结果为旧文件 SHA-256 不变、半写文件未暴露、同目录临时文件残留 0。
- 新 `rag_release_manifest_v2` 绑定 source snapshot、Canonical、SemanticChunk、Retrieval Document、serving/governance SQLite、向量 JSONL、fast matrix/metadata/manifest 和评测证据的路径、SHA-256 与 release ID。校验同时检查 serving/governance 内部 release identity、retrieval/chunk ID 集闭包和 fast manifest 的源索引 hash；跨 release 或任一文件 hash 变化都会失败。
- 在线 reader 优先且默认只选择 `serving.sqlite`，使用 SQLite `mode=ro&immutable=1` 和 `query_only`。旧 `bgp_knowledge_base.sqlite` 只有在显式 `BGPKB_ALLOW_LEGACY_READER=1` 或调用方明确选择 legacy 时才可读取，并报告 `mode=legacy`、`degraded=true`；reader 低于数据库 `minimum_reader_version` 时直接拒绝启动。
- 本轮新增 6 个后端通过用例，完整后端标准回归为 597 passed、2 skipped、46 deselected；相关 serving、runtime path、retriever、artifact verification 和旧 SQLite 回归共 49 passed。Python compileall、`uv build`、OpenSpec strict validation 和 `git diff --check` 均通过。
- 本轮只在测试临时目录构建微型 SQLite 和 manifest，没有构建生产 retrieval documents、数据库、embedding 或快索引，没有访问或修改服务器 `/home/wbt/DB`，没有切换 `current`/`previous`，也没有提交、推送、合并或部署。

## 检查点 D（第一部分）：发布失败契约与版本化黄金集

- 任务 9.1 先新增 5 个失败契约测试，首次运行均因 `bgpkb.domain.rag_quality_gates` 尚不存在而按预期失败；最小实现后分别证明评测硬失败、`skipped_blocking`、manifest/time 过期、context 内合法但不能支持 claim 的错误引用，以及 `legacy_jsonl_scan`/degraded 性能结果都会形成非零发布决定。
- `rag_quality_gates` 当前只提供纯函数式失败判定契约，没有提前修改现有混合检索、回答、DeepSeek CLI 或 verify-release 编排；真实评测接线、报告新鲜度完整绑定和阈值执行仍属于 9.4–9.8。
- 新增 `retrieval_gold_v1.0.0`：104 题，中文 52、英文 52，fact/process/policy/global 各 26；同义表达 16、来源冲突 8、难负例 16。88 个正例全部绑定当前 source registry 中的 expected evidence 选择器，16 个难负例明确要求 `no_evidence` 且不伪造来源。
- 新增 `answer_gold_v1.0.0`：24 个结构化案例，中文 12、英文 12；18 个有证据回答、6 个拒答、4 个提示注入和 4 个来源冲突。每个事实 claim 均声明可接受证据引用和正确性标准，回答案例与检索问题、登记来源保持闭包。
- 中文人工评分说明定义主张正确性、引用精确率、引用召回率、拒答和提示注入五个维度，明确“evidence ID 在 context pack 中合法”不能代替语义支持校验，LLM judge 不能覆盖人工结论。
- 黄金集 manifest 记录 Schema、数据版本、模型族、prompt version、owner 配置和变更流程；精确模型 revision 必须由候选 release 绑定。当前 owner 仍未登记，因此发布效果保持 `skipped_blocking`，未伪造人工签署或绕过阻断。
- 本轮开始基线为 597 passed、2 skipped、46 deselected；完成后完整标准回归为 606 passed、2 skipped、46 deselected。Python compileall、OpenSpec strict validation 和 `git diff --check` 均通过。
- 本轮未运行真实 embedding、reranker 或 DeepSeek 评测，未访问服务器，未构建或切换任何线上制品，也未提交、推送、合并或部署。

## 复核命令类别

- 本地：`uv run pytest -q -m 'not artifact and not legacy_documentation'`。
- 服务器：只读健康、`bgpkb.artifact_verification`、固定 SSE 请求。
- 评测：在 Linux overlay 中运行，lowerdir 指向当前 release，所有结果只写临时 upperdir，结束后卸载并删除。

## 检查点 D（第二部分）：真实评测边界、阈值与服务器性能观察

- 离线 `StructureOnlyClient` 已显式标记为 `development_structure_only` 且不可用于 release。发布检索评测默认强制真实 reranker；发布回答评测强制 DeepSeek provider、固定 model 和精确 model revision，缺失或不匹配时保留 `skipped_blocking` 报告并返回非零。
- 混合检索、结构回答、真实 DeepSeek 和 release checker 已统一硬失败传播。评测报告生成成功不再掩盖失败；黄金集 owner 未登记或真实评测证据缺失仍保持阻断。
- 新增 `rag_release_gate_evidence_v1`：绑定候选 release ID、manifest hash 与生成时间、代码提交、embedding/reranker/LLM 的 model+revision、prompt version 和带时区的评测起止时间。报告引用其他候选、早于 manifest、时间顺序非法或任一绑定不一致都会被判为 stale。
- 新增 `rag_quality_gates_v1.0.0` 版本化配置和 fail-closed 评估器，固化 100% 追溯/引用 ID、空/超短记录为 0、同源精确重复率不高于 2%、Recall@8 不低于 90%、相对冻结基线退化不超过 2 个百分点、MRR 不低于 0.65、claim 引用覆盖/精确率不低于 95%、难负例和注入防护 100%、`fast_numpy`、无降级及检索 p95 不高于 500ms。放宽阈值必须有 ADR 和人工批准。
- 新增目标服务器性能门禁工具，固定使用 `retrieval_gold_v1.0.0` 的 104 题和并发 4，记录 dense、总检索、完整回答 p50/p95、index mode、降级和逐题失败；报告原子写入并绑定候选 release 与 manifest。
- 2026-07-14 对现有线上 release `2026-07-13-a776240` 做了只读环境基线：104/104 请求成功，`fast_numpy`，无降级；dense p50/p95 为 74.116/132.613ms，总检索为 145.965/481.300ms，完整回答为 6.946/14.623s。报告位于本机临时路径 `/tmp/bgpkb-observed-current-2026-07-13-performance.json`，不进入 Git 或生产目录。
- 上述线上 release 不是本变更生产候选，且在线 reranker 响应没有 revision，因此该观察不能完成任务 9.8，也不能替代新鲜度门禁。9.8 必须等待后续任务生成未切换的候选制品，再在候选目录和对应服务进程上重跑。
- 本轮完整标准回归为 641 passed、2 skipped、46 deselected；Python compileall、`uv build`、OpenSpec strict validation 和 `git diff --check` 均通过。服务器 screen 与健康状态保持不变；未提交、推送、合并、部署或切换 `current`/`previous`。

## 检查点 D2-A：五阶段编排与 checkpoint 契约

- 新增唯一产品编排入口 `bgpkb-pipeline`，固定公开 `source-ingest → canonicalize → semantic-build → publish-index → verify-release` 五阶段；根目录 Makefile 同名目标只接受显式 `CANDIDATE_DIR`，不会推断或写入当前 release。
- 五阶段声明线性依赖、输入 manifests、必需输出、成功标准与内部子任务。原来源采集、Canonical 解析、语义构建、catalog/SQLite、BGE-M3、NumPy 快索引、真实检索/回答/性能评测及就绪检查均收敛到阶段内部；旧 `bgpkb.pipeline.*` 细粒度入口和旧 `run_pipeline` 继续保留用于诊断与迁移兼容，本轮未删除。
- 每个内部子任务独立记录模块、渲染命令、返回码、耗时、stdout/stderr 日志和结构化 diagnostics；任一非零返回立即写失败阶段 manifest，并停止所有下游阶段。
- 所有子任务环境强制绑定候选目录下的 `BGPKB_DATA_DIR`、`BGPKB_SOURCE_STORE_DIR` 和 `BGPKB_CANDIDATE_DIR`。候选目录若等于、包含或位于受保护的 current/previous/data 路径内，或直接使用 `current`/`previous` 指针名称，编排器会在执行前拒绝。
- 阶段指纹由直接输入文件与外部输入指纹、该阶段的版本化配置、该阶段代码内容和上游阶段 manifest SHA-256 共同形成。成功 checkpoint 另外绑定阶段 manifest SHA-256 与每个必需输出 SHA-256；任一文件缺失、变化、Schema 不匹配或状态非 complete 均禁止复用。
- 相同指纹重跑会零执行复用已验证阶段；某阶段 checkpoint 缺失，或输入/config/代码/上游 manifest 首次变化时，从首个受影响阶段到目标阶段统一失效并重跑，之前未受影响阶段继续复用。级联失效事件原子记录在候选目录 `.pipeline/invalidations.json`。
- `publish-index` 的必需输出已包含 vector JSONL、matrix、metadata 和 fast manifest；快索引三件套任一缺失都会形成 `missing_required_output` 并返回非零，不会把补跑责任留给部署人员。
- 本检查点只用 pytest 临时目录和微型占位制品验证编排行为，没有运行全量来源、Docling、embedding、reranker 或 LLM，没有访问服务器或修改 `/home/wbt/DB`，没有切换 `current`/`previous`，也没有提交、推送、合并或部署。

## 检查点 D2-B：候选隔离、制品闭包与统一门禁

- 每个阶段内部子任务现在必须声明候选内写根；编排器把 `BGPKB_DATA_DIR`、`BGPKB_SOURCE_STORE_DIR`、临时目录、缓存目录和统一 `BGPKB_RELEASE_ID` 绑定到候选目录。候选 basename 是本次构建唯一 release ID，SQLite、publish manifest 与验证报告不再各自推导身份。
- 编排器在运行前记录 current/previous 及其 release 的受保护状态，并在每个子任务返回后复核。测试分别冻结 current、previous 符号链接目标和 release sentinel 字节；阶段失败后四项全部不变。失败候选写入 `candidate.json`，`reader_selectable=false`，即使目录中存在 `serving.sqlite` 半成品，在线 reader 也会失败关闭。
- `publish-index` 新增 `publish_index_manifest_v1.json` 原子闭包，覆盖 source/chunk catalog、Retrieval Document、serving/governance SQLite、FTS、embedding JSONL/manifest、fast matrix/metadata/manifest 和 artifact manifest 共 12 个逻辑角色。每项绑定 release ID、候选相对路径、SHA-256、记录数、模型 revision 和适用的 retrieval input manifest hash。
- 闭包验证要求 Retrieval Document、serving/FTS、embedding JSONL 和 fast metadata 的 chunk/retrieval document ID 集一致；fast manifest 必须绑定 embedding JSONL SHA-256。缺文件、跨 release、空模型 revision、输入 hash 不一致、ID 集不闭合或 artifact manifest hash 过期均非零失败，且不会覆盖上一份完整闭包 manifest。
- serving/FTS 的输入指纹已收敛为与 embedding/reranker 相同的 `retrieval_input_manifest_v1`，移除了原先额外加入 `chunk_id` 导致的同输入不同 hash 偏差。
- `verify-release` 新增统一 `release_verification_report_v1.json`，矩阵覆盖候选 manifest、黄金集 owner、制品完整性、生产数据质量、真实检索、结构化回答、真实模型配置、性能、报告新鲜度和版本化阈值。缺 owner、code commit、任一模型 revision、prompt version、候选 manifest 或新鲜报告均失败关闭；结构 mock、其他 release 和线上旧报告不能替代候选真实评测。
- verify-release 内部报告子任务采用 `collect_for_gate`：单项非零先保留报告并继续形成最终矩阵；所有非零仍由阶段统一传播，最终报告生成成功不能掩盖前序失败。其他四阶段继续使用立即停止策略。
- 新增长期权威文档 `docs/pipeline.md`，集中维护五阶段入口、候选结构、checkpoint、闭包、迁移、门禁、成对发布/回滚和故障诊断。架构、数据制品、运维和根 README 改为链接；5 份 ADR、迁移基线、历史映射和回答黄金集评分说明继续保留，本轮没有删除可追溯事实。
- 完整后端标准回归为 672 passed、2 skipped、46 deselected；Python compileall、`uv build`、OpenSpec strict validation 和 `git diff --check` 均通过。没有修改前端，因此未运行前端测试或构建。
- 本轮全部候选、SQLite、manifest、索引占位和报告只写 pytest 临时目录；未运行生产全量 source、Docling、embedding、reranker 或 DeepSeek，未访问或修改服务器 `/home/wbt/DB`，未重启服务，未切换 current/previous，也未提交、推送、合并或部署。
- 任务 9.8 仍不能完成：当前只有线上旧 release `2026-07-13-a776240` 的只读性能观察，没有由本变更五阶段生成并验证的新候选；线上证据仍缺精确 reranker revision，黄金集 owner 也未登记。旧 release 的 104 题结果不能替代候选 manifest 绑定的真实模型与性能门禁。
