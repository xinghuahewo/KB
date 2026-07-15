## MODIFIED Requirements

### Requirement: 系统并行生成完整 v2 语料
系统 SHALL 保留 Canonical Document v2 作为唯一生产权威，并在不修改现有 v2 release 的候选工作区并行生成 SemanticChunk v3、retrieval documents、serving bundle 和索引；生产输入 MUST 覆盖当前来源注册表中的全部有效 snapshot，旧 parsed/chunks v1 不得进入新 release。

#### Scenario: 执行首次 v3 候选全量迁移
- **WHEN** 操作者从冻结 source snapshots 运行完整迁移
- **THEN** 每个有效来源 SHALL 具有明确终态，新候选 SHALL 从 Canonical Document v2 全量派生，当前 v2 release 和线上指针 SHALL 保持不变

### Requirement: 系统生成逐文档 v1/v2 差异
迁移 SHALL 生成逐文档 Canonical v2 与 SemanticChunk v3/旧发布 chunk 的差异，覆盖正文内容、section、表格、chunk 数量与长度、重复折叠、来源引用、状态迁移和旧新 chunk identity；v1 只作为历史对照，不再作为覆盖率权威基线。

#### Scenario: 新切块正文覆盖下降
- **WHEN** v3 eligible 与 isolated 内容合计无法覆盖 Canonical v2 的全部 publishable blocks
- **THEN** 文档 SHALL 阻断迁移验收，除非缺失内容全部由版本化且已批准的隔离规则解释

### Requirement: 全量迁移满足确定性门禁
迁移 MUST 达到全部有效 source snapshots 终态、Schema 错误 0、不可追溯 Block/chunk 0、空 retrieval text 0、替换字符 0、重复 ID 0、未审核 fallback 发布数 0、非 allowlist eligible 超短 chunk 0、同源精确重复率不高于 2%，并 SHALL 通过重复运行稳定性和跨制品 ID 闭包检查。

#### Scenario: 任一硬门禁失败
- **WHEN** 全量候选存在任一迁移硬门禁问题
- **THEN** 系统 MUST NOT 创建可切换 release 或更新线上指针，并 SHALL 输出问题来源、文档、chunk 和修复建议

### Requirement: 发布切换原子且可回滚
全部数据、检索、回答和性能门禁通过后，系统 SHALL 生成新的不可变 release，并只在人工显式批准后把代码 generation 与制品 release 作为一对原子切换；系统 SHALL 保留旧 release、previous 指针、manifest 和验证过的成对回滚命令。

#### Scenario: 新 release 切换成功
- **WHEN** 候选验收通过且操作者显式执行切换
- **THEN** 在线服务 SHALL 从 SemanticChunk v3 serving bundle 读取，并报告代码提交、release id、retrieval text version 和 fast index mode

#### Scenario: 切换后需要回滚
- **WHEN** 操作者执行已验证回滚命令
- **THEN** 系统 SHALL 同时恢复上一代码 generation 与 previous 制品指针，旧 release MUST 无需重建即可恢复服务

## ADDED Requirements

### Requirement: v1 兼容入口必须限期退出生产
旧 parsed/chunks v1 MAY 在一个已验证发布周期内由只读迁移适配器读取，但 MUST 报告 deprecated/legacy 模式，MUST NOT 进入新 serving bundle、embedding、真实评测或新的治理决定；移除前 SHALL 有零生产引用证明。

#### Scenario: 兼容期内读取历史人工证据
- **WHEN** 治理人员查询旧 review 记录
- **THEN** 系统 MAY 从历史只读制品展示旧证据，但不得把它混入新 release 的在线检索集合

#### Scenario: 准备移除 v1 适配器
- **WHEN** 生产、测试、部署和数据 manifests 已连续一个发布周期无 v1 引用
- **THEN** 系统 SHALL 生成退役证明后移除兼容入口，历史 release 和审计记录仍需保留
