## MODIFIED Requirements

### Requirement: 系统生成稳定 Canonical Block v2
每个 Block MUST 包含稳定身份、父子结构、类型、阅读顺序、内容、质量、追溯和治理字段；PDF Block MUST 包含页码与 bbox。Canonical Document MUST 通过严格 JSON Schema 引用 Canonical Block、source snapshot、asset 和 runtime 定义，文档、Block 与 source snapshot 的身份闭包 MUST 在发布前校验通过。

#### Scenario: 相同输入重复适配
- **WHEN** source snapshot、镜像、模型和配置完全相同
- **THEN** Document ID、Block ID、排序和非时间字段 SHALL 完全一致

#### Scenario: Document 中的 Block 不满足独立 Block Schema
- **WHEN** 任一 blocks 数组成员缺少必需字段或包含未允许字段
- **THEN** Canonical Document 校验 MUST 失败且不得进入 semantic-build

## ADDED Requirements

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
