## Context

当前仓库由 Python 知识库工程、Next.js 对话前端、Docling 与检索模型部署资产、OpenSpec 变更记录和服务器运行说明组成。核心功能已经稳定，但 `bgp_knowledge_base/src/bgpkb/pipeline` 聚集了大量脚本式入口，文档以阶段记录为主，CI 仍引用失效路径，在线服务和离线制品构建仍共享隐式的仓库内数据目录假设。

数据制品已经从普通 Git 历史迁移到 `/srv/bgpkb/artifacts/releases/<release-id>/`，远端 `main` 已完成历史瘦身。当前部署继续使用 screen，会话与端口契约保持不变。本次整理涉及开发者、运维者和自动化代理，必须保证每个阶段可独立验证和回滚。

## Goals / Non-Goals

**Goals:**

- 建立清晰、稳定且适合单仓库维护的一级目录。
- 将 Python 工程整理为模块化单体，以依赖方向而非历史阶段划分代码。
- 让离线制品生产、在线只读服务和前端交付具有明确边界。
- 统一本地开发、测试、构建、制品校验、发布、部署和回滚入口。
- 将活动文档收敛为长期有效的架构、运维、治理、ADR 和里程碑记录。
- 通过分批 PR、兼容映射和冻结标签保持全程可追溯。

**Non-Goals:**

- 不把模块化单体拆成独立微服务仓库。
- 不修改 FastAPI 对外请求/响应契约或前端问答语义。
- 不改变 embedding、reranker、DeepSeek、Docling 的模型与运行策略。
- 不把 screen 迁移到 systemd、Kubernetes 或新的编排平台。
- 不重新引入语料、数据库、向量索引或生成报告到普通 Git 历史。
- 不在目录迁移 PR 中同时重写业务算法。

## Decisions

### 1. 采用模块化单体，而不是多包微服务

仓库一级目录统一为 `backend/`、`frontend/`、`infra/`、`artifacts/`、`scripts/`、`docs/` 和 `openspec/`。Python 分发包继续名为 `bgpkb`，内部按 domain、ingestion、indexing、retrieval、publishing、workflows、api、infrastructure 划分。

选择该方案是因为当前团队规模、共享数据模型和部署方式不需要跨服务网络边界。相比继续保留历史阶段目录，它能表达稳定职责；相比拆分多个 Python 包，它减少版本和发布协调成本。

### 2. 强制单向依赖

- `domain` 不依赖文件系统、HTTP、FastAPI 或模型客户端。
- `ingestion`、`indexing`、`publishing` 和 `retrieval` 可依赖 domain 与明确的 infrastructure 接口。
- `api` 只调用 retrieval/application 接口，不直接遍历散落数据文件。
- `workflows` 负责编排离线步骤，不承载领域算法。
- `infrastructure` 实现文件系统、HTTP、数据库和模型服务适配器。

测试将通过导入边界检查防止反向依赖。替代方案是只移动目录而不约束依赖；该方案无法解决当前脚本间隐式耦合，因此不采用。

### 3. 运行数据通过显式制品契约提供

代码使用 `BGPKB_DATA_DIR` 定位运行数据。服务器制品目录采用不可变版本路径：

```text
/srv/bgpkb/artifacts/releases/<release-id>/
```

每个版本必须包含文件级 `SHA256SUMS`、生成提交号、文件数量和制品版本。部署通过只读挂载或受控同步提供数据；`artifacts/releases.yaml` 仅记录定位信息，不保存制品本体。

无制品开发环境必须能运行纯单元与契约测试；需要真实发布数据的测试必须归类为 artifact/integration gate 并明确跳过原因。默认 `test` 入口只执行无制品门禁，`test-artifacts` 必须显式接收 release id 或数据根目录，并在数据根目录、清单或完整性缺失时失败关闭。替代方案是 Git LFS，但当前制品为可再生发布输出且总体积较大，服务器制品库更符合现有离线部署边界。

当前干净克隆的 44 个后端失败用例证明该边界尚未编码。实施顺序因此调整为：先以测试先行方式引入数据根目录配置、测试标记和最小 fixture，将真实语料、SQLite、向量索引与历史阶段文档依赖移入 artifact gate；只有默认无制品测试全绿后，才开始目录迁移。不得为通过默认测试把真实制品复制回仓库。

检索应用层通过 `RetrievalData` 协议访问发布数据，不直接拼接文件路径。生产适配器从 `BGPKB_DATA_DIR` 提供数据库、catalog、信任元数据、section 层级和策略排除信息；单元测试注入内存或临时实现。`search` 与 `context_pack` 在一次请求内共享同一适配器，缺少生产制品时失败关闭，已显式注入测试依赖时不触发任何隐藏文件读取。

完整制品按用途区分为线上运行包、审计验收包和可再生中间产物。第一阶段先建立逻辑边界和清单，不复制或删除现有服务器数据；后续发布可只部署 SQLite、catalog、向量索引与 manifest 组成的运行包。

artifact/integration gate 采用双目录：`BGPKB_DATA_DIR` 指向只校验、不写入的不可变源 release，`BGPKB_ARTIFACT_TEST_DIR` 指向独立临时副本或 overlay 合并目录。pytest 进程只接收测试目录；两者缺失、相同或测试目录不可用时门禁失败关闭。服务器优先使用只读 lowerdir + 可丢弃 upperdir 的 overlay，结束后卸载并删除临时上层。

### 4. 统一入口使用 Makefile 包装现有工具

根目录提供 `make bootstrap`、`make test`、`make test-artifacts`、`make build`、`make verify-artifacts`、`make release`、`make deploy` 和 `make rollback`。Makefile 只做稳定入口，具体实现放在 `scripts/`，Python 依赖仍由 uv 管理，前端依赖仍由 Corepack Yarn 管理。

选择 Makefile 是因为目标服务器与 CI 均可直接使用，不引入新的任务运行器依赖。

### 5. 文档采用“入口 + ADR + 里程碑”模型

活动文档限定为根 README、架构、数据与制品、运维、治理、里程碑、CHANGELOG 和少量 ADR。阶段、项目和路线图文档中的长期决策先提炼到上述文件，再从活动树删除；不建立新的 `docs/archive/` 垃圾抽屉。

完整过程通过 Git tag、OpenSpec archive 和提交历史追溯。配置中的端口、文件数量等机器事实不在多份文档中重复维护。

### 6. 分四个 PR 实施

1. 制品契约、测试分层和无制品 PR 基线。
2. 文档收敛与完成变更归档。
3. 一级目录迁移、兼容路径和 CI 路径修复。
4. Python 内部模块化、统一命令入口、部署/回滚脚本和最终门禁。

每个 PR 必须保持测试与当前部署可运行。禁止将目录迁移与算法修改混入同一提交。

## Risks / Trade-offs

- [大规模 `git mv` 导致评审难度上升] → 先完成纯移动提交，再单独提交引用和配置修复；PR 中启用 rename 检测。
- [部署脚本仍依赖旧绝对路径] → 提供一个发布周期的符号链接或路径映射，并在运维文档中记录移除条件。
- [无制品 CI 与真实制品门禁结果不同] → 明确拆分 unit/contract 与 artifact/integration 两类作业，部署前强制运行后者。
- [文档压缩时遗失关键决策] → 删除旧文档前建立内容映射表，要求每项长期决策落入 ADR、架构或 milestones。
- [Python 模块移动引入循环依赖] → 先建立导入边界测试，再逐模块迁移；不在同一任务中改变业务行为。
- [当前远端保护规则状态不确定] → 实施前先验证 `main` 禁止直接推送且要求 PR；未确认前不开始目录迁移。
- [服务器制品目录成为单点] → 保留不可变历史版本、SHA-256 和回滚指针，后续再评估异地备份，不在本次引入新对象存储。
- [历史 artifact 测试会生成派生输出] → 禁止测试直接指向不可变 release，强制独立测试工作区，并在测试前后复核源 release 清单哈希。

## Migration Plan

1. 在当前瘦身 `main` 创建冻结 tag，记录线上代码提交、前端构建与制品 release id。
2. 验证远端 `main` 分支保护，创建本变更专用分支。
3. PR 1 以失败测试为起点，引入 `BGPKB_DATA_DIR`、测试分层、最小 fixture 和制品门禁，令干净克隆的默认测试全绿。
4. PR 2 收敛文档、生成 ADR/里程碑，并归档三个已完成 OpenSpec change。
5. PR 3 使用 `git mv` 调整一级目录，修复所有路径、CI 与部署兼容映射；部署仍使用旧运行路径。
6. PR 4 建立模块依赖测试并逐步迁移 Python 模块，补全统一 Makefile/脚本、制品验证和回滚门禁，保持 `bgpkb` 包名与 API 契约。
7. 在本地和服务器执行完整验证，切换部署路径；保留上一版本代码和制品。
8. 稳定一个发布周期后移除旧路径兼容映射并打整理完成 tag。

回滚以 PR 为单位：代码回退到上一个 tag，数据指针恢复到上一不可变制品版本，screen 会话按现有端口重新启动。任何阶段均不得删除服务器旧制品。

## Open Questions

- `.claude/` 是否仍需作为跨工具兼容层保留，还是只保留 `.codex/` 与 `AGENTS.md`？该决定在 PR 1 完成前确认。
- 服务器制品库是否需要在本次整理后增加异地只读备份？本变更先只保留接口和文档位置。
- 旧部署路径兼容期采用一个发布周期还是固定日期？PR 2 需要写入明确移除条件。
