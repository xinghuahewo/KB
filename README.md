# BGP 知识库

BGP 知识库是一个模块化单体项目：离线流水线把标准、论文、案例和运维资料加工为可追溯制品；FastAPI 提供检索与问答；React/Next.js 前端提供证据工作台。

源码与运行数据严格分离。普通 Git 只保存代码、配置、测试、制品注册表和必要文档；语料、SQLite、向量索引及生成报告由服务器制品库按 release 管理。

## 快速入口

- [架构](docs/architecture.md)
- [RAG 五阶段流水线](docs/pipeline.md)
- [数据与制品](docs/data-artifacts.md)
- [运维与部署](docs/operations.md)
- [工程治理](docs/governance.md)
- [里程碑](docs/milestones.md)
- [变更记录](CHANGELOG.md)
- [架构决策](docs/adr/README.md)

## 稳定工作流

```bash
make bootstrap
make test
make build
```

发布与部署入口：

```bash
make release ARGS=<code-release-id>
make deploy ARGS="<code-release-dir> <artifact-release-dir>"
make rollback
```

真实制品测试必须显式指定已登记 release，并且只能在隔离副本或 Linux overlay 中运行：

```bash
BGPKB_RELEASE_ID=2026-07-10-93a4c97 \
BGPKB_DATA_DIR=/srv/bgpkb/artifacts/releases/2026-07-10-93a4c97/data \
make test-artifacts
```

数据候选统一使用五阶段入口；完整契约见 [RAG 五阶段流水线](docs/pipeline.md)：

```bash
make source-ingest CANDIDATE_DIR=/absolute/path/to/candidate
make canonicalize CANDIDATE_DIR=/absolute/path/to/candidate
make semantic-build CANDIDATE_DIR=/absolute/path/to/candidate
make publish-index CANDIDATE_DIR=/absolute/path/to/candidate
make verify-release CANDIDATE_DIR=/absolute/path/to/candidate
```

## 项目边界

- 不在仓库保存密钥、密码、私钥或 token。
- 不把大规模语料、数据库、向量索引和生成数据提交到普通 Git。
- 不在 API 层直接遍历数据文件；运行时通过制品访问边界读取。
- 发布必须同时记录代码提交、前端构建、制品 release id 和 `SHA256SUMS` 哈希。
