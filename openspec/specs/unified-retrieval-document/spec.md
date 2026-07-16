# 统一检索文档规格

## Purpose

定义完整 Retrieval Document、检索输入一致性、embedding 断点缓存、快索引发布依赖和结果去重。

## Requirements

### Requirement: 每个可检索 chunk 派生完整 Retrieval Document
系统 SHALL 为每个 eligible chunk 生成版本化 Retrieval Document，至少包含 retrieval_doc_id、chunk_id、完整 retrieval_text、retrieval_text_hash、retrieval_text_version、source_ref、section_path 和 eligibility；retrieval_text MUST 包含标题、必要的层级上下文和完整语义正文，不得由固定长度 preview 代替。

#### Scenario: chunk 正文超过 240 字符
- **WHEN** 系统派生该 chunk 的 Retrieval Document
- **THEN** retrieval_text SHALL 包含经过模型 token 上限策略处理的完整语义内容，content_preview 只能作为独立展示字段

### Requirement: 所有检索阶段使用同一 Retrieval Document 内容
FTS5、BGE-M3 embedding 和 reranker MUST 使用同一 retrieval_text version；release manifest SHALL 记录三者的输入 manifest hash，任一 hash 不一致 MUST 阻断发布。

#### Scenario: reranker 输入仍来自 content_preview
- **WHEN** 一致性校验发现 reranker 文档未使用当前 retrieval_text
- **THEN** verify-release MUST 失败并报告不一致的组件和版本

### Requirement: embedding 构建可缓存且可断点续建
embedding 缓存键 MUST 包含 retrieval_text_hash、模型名、模型 revision、归一化配置和 provider contract；构建器 SHALL 分批原子 checkpoint，重启后只复用完全匹配的成功向量，不得以 chunk_id 单独判定缓存有效。

#### Scenario: embedding 服务在中途失败
- **WHEN** 已有若干批次完成且输入指纹未变化
- **THEN** 重跑 SHALL 复用已校验批次并从首个未完成批次继续，不得覆盖上一完整发布索引

#### Scenario: 模型 revision 发生变化
- **WHEN** retrieval_text 相同但 embedding 模型 revision 改变
- **THEN** 旧向量 MUST 视为缓存未命中并重新生成

### Requirement: 快向量索引是正式发布依赖
publish-index 阶段 MUST 在向量 JSONL 完成后构建 matrix、metadata 和 fast manifest，并验证记录数、维度、源索引 hash 与 eligibility 集合；缺少或过期的快索引 MUST 阻断候选 release。

#### Scenario: 主流水线只生成 JSONL 向量
- **WHEN** matrix、metadata 或 fast manifest 任一不存在
- **THEN** publish-index 或 verify-release MUST 返回非零且不得依赖人工补跑

### Requirement: 检索结果执行重复抑制与来源多样性
系统 SHALL 在融合与精排过程中按 retrieval_text hash 抑制精确重复，并应用版本化的每文档候选上限；跨来源独立证据 SHALL 保留，所有抑制决定 SHALL 进入检索诊断。

#### Scenario: 同一文档的重复描述占据前八名
- **WHEN** 融合候选包含多个同 hash 或同模板结果
- **THEN** 系统 SHALL 抑制重复并用其他相关候选补位，响应诊断 SHALL 给出被抑制的 chunk_id 和规则
