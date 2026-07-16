## ADDED Requirements

### Requirement: 退役前必须证明零活动 v1 引用
系统 MUST 在移除任何兼容入口前生成机器可读退役证明，至少覆盖生产代码 blocking 依赖、测试/部署配置、运行环境开关、进程文件句柄、current data manifests 和在线 reader 模式；任一活动 v1 引用存在时退役 MUST 失败关闭。

#### Scenario: 生产进程仍打开旧 SQLite
- **WHEN** 退役证明发现 FastAPI 进程打开 `bgp_knowledge_base.sqlite` 或开启 legacy reader
- **THEN** 退役门禁 MUST 返回非零，并保留完整诊断而不删除兼容代码

#### Scenario: 只存在不可变历史 release
- **WHEN** 生产和候选链路无 v1 引用，但仓库外历史 release 仍保留 v1 数据
- **THEN** 退役证明 SHALL 将其标记为 preserved audit evidence 而非活动依赖，且 MUST 记录路径、release id 和 hash

### Requirement: 在线 reader 必须移除 legacy 回退
新代码 release 的在线 database 和 retrieval adapters MUST 只读取经验证的当前 serving bundle，MUST NOT 提供 `BGPKB_ALLOW_LEGACY_READER`、旧 SQLite 自动发现或 `mode=legacy` 降级分支；不兼容 schema/hash/release 组合 MUST 拒绝启动。

#### Scenario: 操作者设置旧环境开关
- **WHEN** 运行环境包含 `BGPKB_ALLOW_LEGACY_READER=1`
- **THEN** 新服务 MUST 忽略或拒绝该已退役配置，且 MUST NOT 打开旧 SQLite

#### Scenario: 当前 release 缺少 serving.sqlite
- **WHEN** current artifact 只包含旧 `bgp_knowledge_base.sqlite`
- **THEN** FastAPI 启动 MUST 失败并报告代码/制品不兼容，MUST NOT 退回 legacy reader

### Requirement: v1 平行生产入口必须从产品面移除
被 source-ingest、canonicalize、semantic-build、publish-index 和 verify-release 取代的 v1 parsed/cleaned/chunks 构建器、报告器和平行 CLI MUST 从稳定 Make/CLI/CI/部署入口移除；退役后的依赖扫描 MUST 对新增例外失败，不得用新 deprecated 登记规避。

#### Scenario: CI 重新引用旧 chunk 构建器
- **WHEN** Makefile、CI 或生产脚本重新调用 v1 chunk/parsed/cleaned 入口
- **THEN** 退役扫描与 CI MUST 以非零状态失败并指向对应五阶段入口

### Requirement: 历史 release 和审计证据必须保留且与生产隔离
退役 MUST NOT 删除或改写已发布 release、source snapshots、v1 人工决策、chunk migration、评测和回滚证据；需要查阅时 MUST 使用隔离离线审计环境，其输出 MUST NOT 进入 serving、embedding、真实评测或新治理决定。

#### Scenario: 治理人员查阅旧人工决策
- **WHEN** 操作者在明确的离线审计工作区读取历史证据
- **THEN** 系统 SHALL 只输出追溯展示/导出，MUST NOT 修改正式治理状态或新 release 检索资格

#### Scenario: 退役前后核对历史制品
- **WHEN** 生成退役 release
- **THEN** 历史 release/snapshot/审计证据的数量与 hash SHALL 与退役基线一致

### Requirement: 退役发布必须可 canary 且成对回滚
退役变更 MUST 从干净提交构建新代码 release，与经重新验证的当前不可变制品形成兼容对，并在生产切换前通过隔离 canary；切换和回滚 MUST 同时更换代码/制品对，previous release MUST 无需重建即可恢复。

#### Scenario: 退役 canary 尝试打开旧 DB
- **WHEN** canary 使用退役后代码和旧 SQLite 制品组合
- **THEN** canary MUST 启动失败，而使用已验证 serving bundle 时 SHALL 通过健康、SSE、拒答、多引用和时延验收

#### Scenario: 退役发布后出现回归
- **WHEN** 操作者执行已验证的 previous 成对回滚命令
- **THEN** 系统 SHALL 恢复上一代代码/制品对并重启原 screen，MUST NOT 重建或改写历史 release
