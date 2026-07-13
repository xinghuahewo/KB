# 系统架构

## 总体形态

项目采用模块化单体。离线数据处理、发布、在线检索、API 和前端在同一仓库协作，但依赖方向和运行数据边界明确。

```mermaid
flowchart LR
    S["外部资料"] --> I["ingestion 清洗与规范化"]
    I --> X["indexing 分块与索引"]
    X --> P["publishing 不可变 release"]
    P --> R["retrieval 检索与证据组装"]
    R --> A["FastAPI"]
    A --> F["React/Next.js 前端"]
```

## 目录职责

- `backend/`：Python 包、元数据配置和测试。
- `frontend/`：对话与证据工作台。
- `infra/`：nginx、服务启动和部署资产。
- `scripts/`：仓库级测试、构建、发布、部署和回滚入口。
- `artifacts/`：只保存轻量 release 注册表。
- `docs/`：长期权威文档与 ADR。
- `openspec/`：尚未归档的变更规格和历史规格归档。

## Python 模块方向

目标依赖方向如下：

```text
domain
  ↑
infrastructure ← ingestion / indexing / publishing
  ↑
retrieval ← api ← workflows
```

- `domain` 只包含值对象、模型与无 I/O 规则。
- `infrastructure` 实现文件系统、SQLite、HTTP、模型服务和 LLM 适配器。
- `ingestion`、`indexing`、`publishing` 负责离线构建。
- `retrieval` 负责召回、重排、证据组装与回答编排。
- `api` 只调用应用/检索接口，不直接遍历语料。
- `workflows` 只做编排，不承载领域算法。

原 `service` 仅保留旧导入包装，原 `pipeline` 仅保留指向上述责任包的同文件兼容链接。算法实现只有一份；新代码不得反向依赖兼容包。兼容入口在服务器稳定运行一个发布周期后移除。

部署层把代码、制品和状态写入不可变 generation，并通过唯一 `current-generation` 符号链接完成原子切换；`current`、`current-artifact` 和两个旧目录兼容链接都是固定的间接入口。

## 在线边界

FastAPI 契约在本次整理中保持不变。运行时必须通过 `BGPKB_DATA_DIR` 选择一个已验证 release；检索请求中的 SQLite、向量索引、catalog 和信任元数据必须来自同一制品适配器。

## 离线边界

Docling、清洗、索引与报告生成可写入构建工作区，但不得直接写当前线上 release。发布流程先生成候选目录、完成校验，再原子切换制品指针。
