# 数据与制品

## 数据分类

- 源码资产：代码、配置、Schema、测试、文档，进入 Git。
- 构建输入：原始资料、人工复核输入，进入受控存储或构建工作区。
- 运行制品：SQLite、向量索引、catalog、证据数据集，进入不可变 release。
- 审计制品：质量报告、SBOM、许可证清单和验收证据，随 release 或发布记录保存。
- 临时产物：缓存、评测中间文件和测试 overlay，用后删除。

## 服务器布局

```text
/srv/bgpkb/artifacts/
  releases/<release-id>/
    SHA256SUMS
    data/
  current -> releases/<release-id>
  previous -> releases/<release-id>
```

常规 release id 采用 `YYYY-MM-DD-<source-commit>`；五阶段流水线候选可采用包含流水线名、版本号和 UTC 时间戳的稳定标识。release id 只能包含字母、数字、点、下划线和连字符，且首尾必须为字母或数字。仓库中的 `artifacts/releases.yaml` 只登记 release id、生成提交、文件数、清单哈希、绝对数据路径和状态，不保存制品本体。

## 运行时契约

`BGPKB_DATA_DIR` 必须指向某个 release 的 `data/`。artifact gate 还要求显式设置 `BGPKB_RELEASE_ID`，并使用与源 release 不重叠的隔离副本或 overlay。

```bash
BGPKB_DATA_DIR=/srv/bgpkb/artifacts/releases/<release-id>/data \
make verify-artifacts
```

候选构建必须先形成 `publish_index_manifest_v1.json`，再通过统一 `verify-release`；完整的候选目录、catalog/DB/FTS/embedding/fast index 闭包和失败关闭条件见 [RAG 五阶段流水线](pipeline.md)。正式 release 仍必须使 `SHA256SUMS` 与实际文件集合完全一致，并通过 SQLite、向量和 release 注册表校验。

部署 artifact 门禁按发布 schema 选择测试集：旧全量数据 release 运行 `artifact` 集成测试；`serving_sqlite_v1` 只读在线闭包运行 `serving_artifact` 健康、只读连接和可追溯检索测试。两类测试都先后校验源 release，且只在隔离 overlay 中执行，不得用旧全量目录假设否决或修改 serving bundle。

## 发布与回滚

发布四元组为：代码提交、前端构建标识、制品 release id、`SHA256SUMS` 哈希。部署切换代码和制品指针前必须通过校验；失败时保持 `current` 和线上会话不变。

回滚恢复上一代码构建与 `previous` 制品指针，不重建历史制品。任何需要修改既有 release 的操作都应创建新 release。

## 备份与保留

服务器管理员负责 release 目录备份。至少保留 current、previous 和一个已验证冻结版本；临时测试 overlay 不进入备份。
