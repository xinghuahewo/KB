## 1. 冻结基线与迁移保护

- [x] 1.1 验证远端 `main` 已禁止直接推送、要求 PR 与必需检查，并将验证结果记录到治理文档
- [x] 1.2 创建整理前冻结 tag，记录线上代码提交、前端构建、制品 release id 和 `SHA256SUMS` 哈希
- [x] 1.3 在干净克隆中记录后端测试、前端测试与生产构建基线，并确认当前 FastAPI 契约和远端健康状态
- [x] 1.4 扫描 Git 历史和工作树中的大型 blob、语料、SQLite、向量索引及生成报告，建立必须保持为零的仓库卫生基线
- [x] 1.5 确认 `.claude/` 的保留或移除决定、旧部署路径兼容期限和服务器制品备份责任人

## 2. PR 1：制品契约与测试分层

- [x] 2.1 为 `BGPKB_DATA_DIR` 解析、缺失制品提示、越界路径拒绝和不可变 release 元数据编写失败测试
- [x] 2.2 实现集中式数据根目录配置和可注入 `RetrievalData` 边界，迁移数据库、catalog、信任元数据、章节层级、策略排除、索引和报告读取路径，保留明确的无制品开发默认行为
- [x] 2.3 审计并标记依赖真实语料、SQLite、向量索引或发布数据的现有测试；为默认测试所需行为创建最小 fixture 或临时数据库
- [x] 2.4 实现显式 release id 的 artifact/integration gate；强制使用与不可变源 release 分离的临时副本或 overlay，未提供有效源目录和测试工作区时必须失败关闭并说明操作方法
- [x] 2.5 定义 `artifacts/releases.yaml` 元数据格式，记录 release id、生成提交、文件数量、清单哈希与部署状态，不记录制品本体
- [x] 2.6 实现 `verify-artifacts`，校验 SHA-256、文件数量、SQLite 完整性、索引元数据和必需目录，并在任一失败时关闭部署
- [x] 2.7 建立根 Makefile 的 bootstrap、test、test-artifacts、build 和 verify-artifacts 稳定入口，并将逻辑下沉到可测试的 `scripts/`
- [x] 2.8 扩充 CI，使默认 PR 门禁只运行无制品后端测试、前端测试/构建、API 契约与仓库卫生检查
- [x] 2.9 在干净克隆中验证默认 test 与 build 全绿，并以指定 release id 验证 artifact/integration gate

## 3. PR 2：文档收敛与规格归档

- [x] 3.1 建立旧文档到 README、架构、数据与制品、运维、治理、里程碑、CHANGELOG 或 ADR 的逐项内容映射表
- [x] 3.2 编写根 README 文档索引，确保架构、部署、数据制品和治理均可一次跳转到唯一权威文档
- [x] 3.3 将系统边界、模块依赖方向、在线与离线数据流提炼到架构文档
- [x] 3.4 将 `BGPKB_DATA_DIR`、不可变 release、哈希清单、发布与回滚约束提炼到数据与制品文档
- [x] 3.5 将端口、screen 会话、健康检查、部署和故障回滚流程收敛到运维文档
- [x] 3.6 将分支保护、PR 门禁、大文件策略、发布四元组和文档维护规则收敛到治理文档
- [x] 3.7 为模块化单体、服务器制品库和 screen 保留策略分别创建编号 ADR，并记录替代方案与后果
- [x] 3.8 更新里程碑与 CHANGELOG，记录已完成阶段、冻结版本和本次整理计划
- [x] 3.9 归档 `phase-5-standard-exports`、`phase-a-corpus-profiling` 和 `docling-private-cleaning-v2` 三个已完成 OpenSpec change
- [x] 3.10 删除已完成映射的阶段、项目和路线图文档，运行链接检查与 OpenSpec 校验；原计划独立 PR 2 在实施时并入受保护的 PR #1，验收内容保持不变

## 4. PR 3：一级目录与兼容迁移

- [x] 4.1 先添加会因新目录缺失而失败的仓库结构、路径有效性和旧路径兼容测试
- [x] 4.2 使用纯 `git mv` 提交将后端、前端和部署资产迁移到 `backend/`、`frontend/` 与 `infra/`，不修改业务内容
- [x] 4.3 建立 `artifacts/` 制品元数据目录和 `scripts/` 自动化目录，确认根目录不产生第二套应用源码
- [x] 4.4 在独立提交中修复 Python、Yarn、OpenSpec、代理配置、文档链接和开发工具中的仓库相对路径
- [x] 4.5 修复 CI 对不存在脚本路径的引用，并增加工作流静态路径校验
- [x] 4.6 为服务器旧后端和前端绝对路径实现限期符号链接或启动路径映射，并记录唯一真实源码位置与移除条件
- [x] 4.7 运行后端测试、前端测试和生产构建，确认 FastAPI 契约及 screen 启动参数未改变
- [x] 4.8 在临时部署目录演练新旧路径切换和回滚，并提交不含算法变化的 PR 3

## 5. PR 4：Python 模块化单体、工作流与制品切换

- [x] 5.1 添加 import-linter 或等价的依赖边界测试，使 domain I/O 依赖、api 直接文件遍历和 workflows 领域算法在实现前按预期失败
- [x] 5.2 建立 `bgpkb/domain` 及稳定公共接口，迁移纯数据模型、值对象和无 I/O 规则并保持 `import bgpkb` 可用
- [x] 5.3 建立 `bgpkb/infrastructure`，迁移文件系统、HTTP、数据库、embedding、reranker 和 LLM 适配器
- [x] 5.4 建立 `bgpkb/ingestion`，迁移采集、Docling 转换、清洗和语料规范化能力
- [x] 5.5 建立 `bgpkb/indexing` 与 `bgpkb/publishing`，迁移分块、embedding、索引、标准导出和发布能力
- [x] 5.6 建立 `bgpkb/retrieval`，迁移查询、召回、重排、证据组装和回答编排，同时锁定现有行为测试
- [x] 5.7 建立 `bgpkb/api`，让 FastAPI 路由仅调用 retrieval/application 接口并通过现有 API 契约测试
- [x] 5.8 建立 `bgpkb/workflows`，将阶段脚本收敛为薄编排入口并为旧 CLI 提供限期兼容包装
- [x] 5.9 删除已无调用方的重复模块与兼容包装，运行依赖边界、单元、契约和回归测试
- [x] 5.10 在无制品环境完成后端安装与全量测试，确认不改变检索算法和问答语义后提交 PR 4

## 6. 部署、回滚与最终验收


- [x] 6.1 实现 release、deploy 和 rollback 稳定入口，并将逻辑下沉到可测试的 `scripts/`
- [x] 6.2 实现独立记录当前/上一代码版本与制品版本的部署状态，并在切换前完成制品门禁
- [x] 6.3 实现单一 rollback 入口，恢复上一代码构建和制品指针后验证前端、FastAPI、embedding 与 reranker 健康状态
- [x] 6.4 在本地制品副本完成发布、部署失败保护和无需重建制品的回滚演练；原计划独立 PR 4 在实施时并入受保护的 PR #1


- [x] 6.5 在 `10.99.8.28` 重新检查 GPU、screen、端口、磁盘空间、当前制品哈希和上一版本回滚可用性
- [x] 6.6 使用指定 release id 在远端运行 `verify-artifacts` 与 artifact/integration gate，失败时保持 current 指针和线上会话不变
- [x] 6.7 部署整理后的代码并切换只读数据根目录，保持 `39280`、`39281`、`8011`、`8012` 和既有 screen 会话契约
- [x] 6.8 验证静态前端、FastAPI 健康检查和真实端到端问答均通过，确认 reranker 完整且服务未降级
- [x] 6.9 执行一次代码与制品联合回滚演练，再恢复新版本并记录耗时、结果和恢复点
- [x] 6.10 记录正式发布四元组并创建整理完成 tag，更新里程碑和 CHANGELOG
- [ ] 6.11 稳定一个约定发布周期后移除旧路径兼容映射，再次执行完整测试、构建、制品校验和远端健康检查
- [ ] 6.12 归档 `repository-architecture-consolidation` OpenSpec change，确认活动列表只保留未完成变更

## 7. 快向量索引制品回归修复

- [x] 7.1 以失败测试复现候选制品缺少或携带过期快索引时门禁仍通过的问题
- [x] 7.2 强制校验 NumPy matrix、metadata、fast manifest 与源 JSONL，并让 JSONL 兼容回退显式标记性能降级
- [x] 7.3 创建新的不可变快索引制品，通过完整门禁后部署并验证 `fast_numpy`、检索耗时和回滚点
