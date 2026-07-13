## ADDED Requirements

### Requirement: 运行数据由显式数据根目录提供
后端 MUST 通过 `BGPKB_DATA_DIR` 定位语料、派生数据、数据库和索引；未设置时的开发默认值 MUST 明确且不得假定 Git 含有完整制品。

#### Scenario: 在线服务挂载发布制品
- **WHEN** 服务以 `BGPKB_DATA_DIR=/srv/bgpkb/artifacts/releases/<release-id>/data` 启动
- **THEN** 所有运行数据读取都解析到该不可变制品版本

### Requirement: 制品版本不可变且可校验
每个制品版本 MUST 存放在独立 release id 目录，并 MUST 包含文件级 SHA-256 清单、生成提交号和文件数量；验证失败时部署 MUST 失败关闭。

#### Scenario: 制品文件被修改
- **WHEN** `sha256sum -c SHA256SUMS` 检测到任一文件不匹配
- **THEN** 部署流程停止且不切换 current 指针或重启线上服务

### Requirement: 普通 Git 历史不包含运行制品
仓库 MUST 只跟踪制品定位和校验元数据，并 MUST 拒绝提交语料、SQLite、向量索引、大型派生数据或生成报告。

#### Scenario: 提交引入大型制品
- **WHEN** PR 新增受忽略的运行数据路径或超过仓库阈值的 blob
- **THEN** CI 大文件与忽略规则门禁失败

### Requirement: 无制品环境与制品门禁分层
纯单元和契约测试 MUST 可在未展开制品的干净克隆中运行；依赖真实发布数据的测试 MUST 标记为 artifact/integration gate，并 MUST 给出明确的跳过或失败原因。

#### Scenario: PR 在无制品 CI 中运行
- **WHEN** CI 未挂载服务器制品
- **THEN** 单元和契约测试执行，制品门禁被明确识别为未运行而非静默通过

#### Scenario: 默认测试遇到真实制品依赖
- **WHEN** 用例需要语料、SQLite、向量索引或历史发布数据
- **THEN** 该用例仅在显式 artifact/integration gate 中执行，默认测试不通过隐式仓库数据路径读取它

### Requirement: 缺失制品必须失败关闭且给出操作指引
依赖运行数据的命令 MUST 在 `BGPKB_DATA_DIR` 未配置、release 元数据缺失或制品校验未通过时停止，并 MUST 输出所需 release id 或数据根目录的说明。

#### Scenario: 未挂载制品执行真实检索门禁
- **WHEN** 维护者未设置有效 `BGPKB_DATA_DIR` 就运行 artifact/integration gate
- **THEN** 命令以非零状态退出并说明如何提供已验证制品，且不得回退读取仓库内旧 `data/`

#### Scenario: artifact 测试工作区指向不可变源 release
- **WHEN** `BGPKB_ARTIFACT_TEST_DIR` 缺失、不可用或与 `BGPKB_DATA_DIR` 指向同一目录
- **THEN** 门禁在启动 pytest 前失败，源 release 不发生任何写入

#### Scenario: artifact 测试使用隔离 overlay
- **WHEN** 源 release 已验证且 `BGPKB_ARTIFACT_TEST_DIR` 指向独立临时副本或 overlay
- **THEN** pytest 的所有读取和生成输出都发生在测试工作区，结束后源 release 的 `SHA256SUMS` 仍全部匹配

### Requirement: 检索应用通过单一数据访问边界读取制品
检索和上下文组装 MUST 通过可注入的 `RetrievalData` 边界读取数据库、catalog、信任元数据、章节层级和策略排除信息，并 MUST 不在应用函数中隐藏拼接运行制品路径。

#### Scenario: 单元测试注入内存数据访问对象
- **WHEN** 测试向检索和上下文组装显式注入内存数据访问对象、假 retriever 与假 store
- **THEN** 整个调用链不读取 `BGPKB_DATA_DIR` 或仓库内 `data/`，且仍验证真实应用编排行为

#### Scenario: 生产检索未配置数据访问对象
- **WHEN** 在线请求未显式注入测试对象
- **THEN** 应用创建基于 `BGPKB_DATA_DIR` 的生产适配器，并在制品缺失时失败关闭

### Requirement: 制品回滚不依赖重新构建
部署系统 MUST 能将运行数据指针恢复到上一个已验证 release id，且 MUST 不删除任何旧制品版本。

#### Scenario: 新制品导致线上异常
- **WHEN** 运维者选择上一已验证 release id 执行回滚
- **THEN** 数据指针恢复、服务重启并通过健康检查，无需重新运行离线流水线
