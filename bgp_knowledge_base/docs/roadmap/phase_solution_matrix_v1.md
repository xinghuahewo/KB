---
title: "BGP KB 阶段方案矩阵 v1"
document_type: "阶段方案矩阵"
purpose: "用一张矩阵记录各阶段较优解、简易版和当前推荐取舍。"
scope: "BGP KB 阶段路线"
status: "现行参考"
last_reviewed: "2026-06-20"
---
# BGP KB 阶段方案矩阵 v1

## 总览矩阵

| 阶段 | 较优解 | 简易版 | 当前采用 |
| --- | --- | --- | --- |
| 阶段一：数据管理体系 | 资产登记、机器配置、自动报告和测试。 | 手工资产清单。 | 已完成较优解。 |
| 阶段二：生命周期与元数据治理 | 生命周期派生、状态规则和报告。 | 继续只用 `review_status`。 | 已完成较优解。 |
| 阶段三：语义质量治理 | blocker/warning/info 规则扫描和 findings。 | 人工抽查。 | 已完成较优解。 |
| 阶段三点五：语义标识前置 | `bgpkb:`、URI 规则、JSON-LD context 和字段映射。 | 只冻结 ID 命名。 | 已完成小步较优解。 |
| 阶段四：RAG 就绪与混合检索 | 远程 embedding、向量检索、BM25/关键词、元数据索引、融合排序、context pack 和答案评测。 | SQLite/关键词检索、手写 query expansion 和固定 context pack。 | 4.1-4.4 已完成简易到评测闭环；4.5 开始较优解 v1。 |
| 阶段五：轻量标准化出口 | JSON-LD、SKOS、PROV-O、RDF 导出和标准化报告。 | JSON-LD context 与少量样例。 | 阶段四稳定后启动。 |
| 阶段六：知识覆盖扩展 | 系统扩展来源、案例、论文方法和运营实践。 | 按缺口队列补少量高价值主题。 | 阶段四、五稳定后启动。 |

## 当前决策

当前不再继续扩写阶段四简易版。下一步直接进入阶段 4.5：

> 使用阿里云 BGE-M3 远程 embedding，实现 BM25/关键词检索、向量检索、元数据过滤和 RRF 融合排序的混合检索较优解 v1。

## 阶段 4.5 技术取舍

| 问题 | 选择 | 理由 |
| --- | --- | --- |
| embedding 模型 | 阿里云 BGE-M3 远程服务 | 当前设备不运行模型，同时 BGE-M3 支持跨语言与长文本向量化。 |
| LLM 回答 | DeepSeek API | 已有阶段 4.1-4.4 能力和评测报告。 |
| 向量库 | 先用文件化 JSONL 索引 | 数据规模小，先验证混合检索质量；Milvus/Qdrant 后置。 |
| 关键词检索 | 继续保留 BM25/FTS/规则命中 | BGP 协议词、RFC、AS 编号、字段名适合精确召回。 |
| 融合排序 | RRF + 元数据 boost | 简单、稳定、可解释，适合第一版工业化排序。 |
| 写回知识库 | 禁止 | 阶段 4.5 只改检索和评测，不自动改实体、关系或 chunk。 |

## 不做清单

- 不在当前设备部署 BGE-M3、Qwen 或其它本地模型。
- 不把 API key、endpoint token 写入仓库。
- 不引入需要常驻服务的 Milvus 作为阶段 4.5 必选项。
- 不让 LLM 自动写回知识库。
- 不把 pending、deprecated、archived 内容默认放入高可信 context pack。

## 验收门槛

- 有真实或 fake embedding provider 的可复跑测试。
- 有 embedding manifest 和构建报告。
- 中文“路由泄露”和英文 `route leak` 都能召回相关证据。
- 协议定义类问题优先召回 RFC/standards。
- 事件类问题优先召回 cases。
- context pack 每条证据都有来源、状态和排序解释。
- 质量检查通过，仓库不包含真实 API key。
