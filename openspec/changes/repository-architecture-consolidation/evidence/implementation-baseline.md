# 仓库整理实施基线

记录日期：2026-07-13。

## 代码与制品

- 整理前代码提交：`ceda9ace8de75cd8a7a8033504b7f8a2a14b6c1e`。
- 本地冻结标签：`archive/pre-repository-consolidation-20260713`（尚未推送）。
- 当前制品：`2026-07-10-93a4c97`。
- 制品目录：`/srv/bgpkb/artifacts/releases/2026-07-10-93a4c97/`。
- `SHA256SUMS`：1293 行，清单 SHA-256 为 `97400ef06e8ef20c3d363918b79d2540d4e513e6fe5be4ea9e84e9c870f9a04b`。
- 远端实测：1293/1293 文件哈希通过，SQLite `PRAGMA integrity_check=ok`，BGE-M3 索引状态 `complete`、维度 1024。

## 干净克隆门禁

- 原始后端基线：383 通过、44 失败、2 跳过；失败来自已外置但仍被默认测试隐式读取的运行制品。
- 分层后统一 `make test`：后端 404 通过、2 跳过、46 项显式分流；前端 21/21 通过。
- 统一 `make build`：Python sdist/wheel 与 Next.js 生产构建通过。
- Git 历史扫描未发现超过 1 MiB 的 blob；工作树只跟踪 `data/README.md` 等制品边界说明，不跟踪语料、SQLite 或向量索引。

## 线上只读健康基线

- `http://127.0.0.1:39281/health`：服务版本 `0.1.0`，数据库存在，完整性为 `ok`。
- `http://127.0.0.1:39280/health`：返回相同健康状态。
- FastAPI OpenAPI：标题“BGP 知识库服务”，版本 `0.1.0`，22 个 path。
- 本阶段未切换 screen 会话、端口、代码路径或制品指针。

## 制品测试安全事件与恢复

- 首次远端 artifact gate 直接使用不可变 release，历史生成型测试改写了 `artifact_manifest.csv` 和 `artifact_manifest.jsonl`；发现后立即终止临时 pytest。
- 被改写版本保存于 `/tmp/bgpkb-artifact-gate-mutated-20260713/`，用于后续审计。
- 从原始工作树找到与 `SHA256SUMS` 预期完全一致的两份文件，经哈希预检后原子恢复。
- 恢复后重新验证 1293/1293 文件全部匹配，线上服务与制品指针未切换。
- 门禁契约已改为强制 `BGPKB_DATA_DIR`（不可变源）与 `BGPKB_ARTIFACT_TEST_DIR`（隔离测试工作区）双目录，禁止再次直接测试源 release。

## 已确认的迁移决策

- `.claude/commands/opsx/` 作为 Claude 命令入口保留；与 `.codex/skills/` 重复的 `.claude/skills/` 在文档收敛 PR 中去重。
- 旧后端和前端绝对路径兼容一个正式发布周期，随后经完整门禁移除。
- 本次不引入异地备份系统；当前同机不可变 release、哈希和回滚能力保留，异地备份作为后续运维风险项，由项目维护者负责安排不同故障域目标。
- `main` 分支保护仍需仓库管理员在首个 PR 合入前验证；未验证前不进行目录迁移或合并。
