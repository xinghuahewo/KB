## Context

`rag-evidence-pipeline-v2` 候选已以代码 `2f1957839673f7ef65e1f6dfec332abfcef69972` 和制品 `rag-evidence-pipeline-v2-11.1-20260715T073006Z` 成对切换到生产。生产验收证明 FastAPI 只读 `serving.sqlite`、reader mode 为 current、`BGPKB_ALLOW_LEGACY_READER` 未启用、没有旧 SQLite/parsed/cleaned/chunks/governance 活动文件句柄，候选 manifest 为 `legacy_inputs=[]`，v1 依赖扫描 blocking 为 0。同时代码树仍保留 29 处明确标记的 deprecated 历史构建/迁移/审计引用，以及在线 legacy reader 开关与分支。

本变更是独立退役 release，不在已验证生产代码或制品上原地删除文件。运维者、数据治理者和历史审计人员都需要明确区分“活动生产依赖”与“仓库外不可变历史证据”。

## Goals / Non-Goals

**Goals:**

- 让新代码在线启动面只接受当前 serving schema，不存在通过环境变量重新打开 v1 reader 的路径。
- 移除被五阶段入口取代的过时生产 CLI、平行作业映射和已过期策略登记。
- 在删除前生成机器可读退役证明，并用失败测试保证旧 DB、开关和 manifest 不能重新进入生产。
- 保留全部历史 release、source snapshots、chunk migration、旧人工决策和发布/回滚证据，且不为退役重建它们。
- 以新代码 release 与已验证制品的兼容对执行 canary 和成对切换，保留上一代完整代码/制品对用于回滚。

**Non-Goals:**

- 不删除历史数据目录、不改写旧 manifest、不将大型历史制品移入 Git。
- 不改变 FastAPI/SSE/前端契约，不更换 screen，不引入账号或云同步。
- 不把历史审计数据转换成新 serving 事实，不让 LLM 重放或提升旧批准状态。
- 不把删除兼容代码等同于删除上一 release 的回滚能力。

## Decisions

### 1. 退役门禁区分活动引用和历史保留

新增一个机器可读退役报告，同时检查生产代码 blocking 依赖、部署/测试配置、运行环境开关、进程文件句柄、current manifest 和在线数据库模式。历史 release 与审计记录的存在必须报告为 preserved，不得被计入活动依赖。

仅用文本搜索“v1”会误伤 Schema 版本和历史证据；仅查环境开关又会漏掉静态平行入口。因此选择语义分类扫描加运行证据，不采用单一 grep 或手工清单。

### 2. 在线 reader 完全失败关闭

删除 `BGPKB_ALLOW_LEGACY_READER`、legacy DB 自动发现和 `mode=legacy` 分支。在线 adapter 只解析 current release 的 `serving.sqlite`，当 schema/minimum reader/hash 不兼容时直接拒绝启动，不尝试降级读取旧 DB。

保留开关但强制 false 仍会留下意外重开风险，因此不采用。需要查阅旧数据时，使用历史代码 release 和不可变历史制品在隔离离线环境处理，不复用生产服务进程。

### 3. 过时平行脚本按责任分类处理

- 被五阶段完全取代、且无历史审计必要的构建/报告入口删除代码与导出命令。
- 仅用于已有决策追溯的工具从产品包中移出，收敛为明确的离线审计入口；输出不能进入新候选。
- 更新 `legacy_v1_dependencies.yaml` 和文档，退役后任何重新出现的生产路径必须使 CI 失败，不得再加一条 deprecated 例外规避。

### 4. 发布采用新代码 release 和现有制品兼容对

退役不修改检索文档、SQLite 或向量，因此不为强制制品重建制造新数据。新代码 release 必须重新验证与当前不可变制品的 schema/hash/API 兼容，形成新的代码/制品对并做隔离 canary。previous 仍保留本变更前的完整代码/制品对，rollback 不重建任何历史 release。

### 5. 以失败测试驱动删除

先增加旧 DB、legacy 开关、v1 CLI、混合 manifest 和历史证据进入 serving 必须失败的测试，再最小删除兼容分支。保留历史 release 的测试只验证文件未改写和可用 previous 成对回滚，不要求新 reader 继续打开旧 DB。

## Risks / Trade-offs

- [退役后无法在新服务中直接查询旧 ID] → 保留旧代码/制品 release 和 chunk migration 映射，仅在隔离审计环境读取。
- [删除平行脚本遗漏外部调用者] → 退役前扫描 Make/CI/screen/运维命令和服务进程，对所有命中输出 owner 与替代入口。
- [历史审计工具被误接回生产] → 审计工具不安装到服务运行包，输出类型与路径不被 publish-index 接受。
- [代码变更与当前制品不兼容] → 在隔离 canary 中重跑 artifact verifier、数据库启动、SSE、典型/拒答/多引用和热态性能验收。
- [过早删除导致审计证据丢失] → 删除代码前检查历史 release/snapshot/迁移报告数量和 hash，退役 release 前后必须完全一致。

## Migration Plan

1. 固化当前生产代码/制品对、生产验收报告、v1 分类扫描、进程句柄和历史制品保留基线。
2. 按 TDD 建立退役证明器与旧路径失败契约，先确认当前兼容面会使测试失败。
3. 移除在线 legacy reader 开关/分支，再按策略登记逐个删除或隔离 v1 构建与审计入口。
4. 运行全部测试、静态检查、artifact verifier、OpenSpec strict validation 和退役证明，证明历史制品 hash 未变。
5. 从干净提交构建新代码 release，与当前不可变制品生成兼容报告，启动隔离 canary 并验证旧 DB 被拒绝、新 serving 完整可用。
6. 人工批准后成对切换，验证健康、SSE、拒答、多引用、模型绑定和时延；没有单独数据切换。
7. 若发生回归，使用 previous 成对回滚并恢复上一代 screen；不改写或重建旧 release。

## Open Questions

- 无。历史保留与生产退役边界已由 `rag-evidence-pipeline-v2` 的生产验收和成对回滚证据确定。
