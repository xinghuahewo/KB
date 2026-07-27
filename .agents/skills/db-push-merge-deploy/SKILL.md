---
name: db-push-merge-deploy
description: 编排 DB 仓库从本地提交到 GitHub PR、CI 合并、不可变代码 release 上传和 10.99.8.28 生产部署的完整流程。用户要求“推送”“合并”“部署”“发布到服务器”“同步 main”或检查发布/回滚状态时使用；默认只发布代码并保持当前知识库制品，不用于构建或切换新的数据制品。
---

# DB 推送、合并与部署

把发布视为一条失败关闭的单写入工作流。复用仓库已有发布脚本，不在临时 SSH 命令中重新实现指针切换或回滚状态机。

## 选择运行模式

- 用户只要求检查、计划、预检或确认是否已同步时，保持只读，不推送、不合并、不部署。
- 用户明确要求“推送、合并和部署”时，视为已授权完成当前作用域内的分支推送、PR 合并和代码生产部署，不重复索要相同授权。
- 通用的“部署”默认沿用服务器当前 `current-artifact`，只切换代码。只有用户明确指定新 artifact release 时，才进入数据制品发布流程。
- 修改 `/etc/bgpkb/runtime.env`、nginx、端口、screen 名称、GPU/模型服务，恢复会话库，重写 Git 历史或删除不可变 release，必须另行取得明确授权。

## 使用发布子智能体

若当前任务尚未运行在 `db-release-deployer` 自定义子智能体中，创建且只创建一个该类型的子智能体承接所有写操作，并等待其完成。主智能体负责说明范围、接收阶段结果和最终汇总；不得让多个智能体并行修改 Git、GitHub 或服务器。

## 开始前读取

1. 读取仓库根目录 `AGENTS.md`。
2. 读取 `docs/governance.md`、`docs/operations.md`、`docs/data-artifacts.md` 和 `docs/pipeline.md` 的发布相关章节。
3. 读取 [references/release-contract.md](references/release-contract.md) 获取固定路径、门禁和验收矩阵。
4. 使用 `scripts/preflight.py` 做确定性预检；上传 release 时只使用 `scripts/upload_code_release.py`。

## 工作流

### 1. 确认变更边界

- 检查 `git status --short --branch`、当前分支、远端地址和 diff。
- 只处理用户当前任务中的文件。存在来源不明或无关修改时停止，不覆盖、不暂存、不清理。
- 若修改位于 `main`，先创建 `codex/` 分支；禁止直接推送 `main`。
- 运行 `git fetch --prune origin` 后检查 `main...origin/main`。本地 `main` 只能 `--ff-only` 跟随远端，禁止把陈旧本地 `main` 合入远端。

### 2. 本地验证并提交

- 按变更风险运行针对性测试，再运行 `make test`、`make build`、`openspec validate --all --strict --no-interactive` 和 `git diff --check`。
- 测试或构建后再次确认工作树状态；生成物不得意外进入提交。
- 显式暂存作用域内文件，不使用 `git add .`。
- 创建聚焦提交后运行：

```bash
python3 .agents/skills/db-push-merge-deploy/scripts/preflight.py --phase publish
```

### 3. 推送、PR、CI 与合并

- 只推送当前 `codex/**` 分支并创建 ready PR。
- 等待 push 和 pull_request 两类 `verify` 检查全部成功。
- 合并前核对 expected head SHA、可合并状态、必需检查和未解决审查对话；任一条件不满足即停止。
- 默认按当前仓库惯例 squash merge；不得绕过分支保护、不得 force push。
- 合并后执行 `git fetch origin main`，切回 `main` 并 `git merge --ff-only origin/main`，记录最终完整 SHA。

### 4. 从合并提交构建不可变代码 release

- 只从与 `origin/main` 完全一致的干净 `main` 构建。
- release id 使用可读前缀和最终短 SHA，例如 `<scope>-<short-sha>`。
- 在本地临时 release 根运行仓库稳定入口：

```bash
BGPKB_CODE_RELEASES_DIR=/tmp/bgpkb-code-releases \
  make release ARGS=<release-id>
```

- `make release` 必须完成全量测试、构建、Git archive、完整提交 SHA 和前端 SHA-256 记录。
- 先运行上传工具的默认演练，再显式执行：

```bash
python3 .agents/skills/db-push-merge-deploy/scripts/upload_code_release.py \
  /tmp/bgpkb-code-releases/<release-id>
python3 .agents/skills/db-push-merge-deploy/scripts/upload_code_release.py \
  /tmp/bgpkb-code-releases/<release-id> --execute
```

上传工具必须使用唯一临时目录、全树 SHA-256 复核和原子改名；远端同名 release 已存在时失败，不覆盖。

### 5. 生产预检、备份与迁移

- 运行：

```bash
python3 .agents/skills/db-push-merge-deploy/scripts/preflight.py --phase deploy
```

- 记录当前代码、当前 artifact、previous 代码/制品、screen、端口和健康状态。
- 从 `/etc/bgpkb/runtime.env` 只读取所需路径，不输出文件内容或任何密钥。
- 按 `docs/operations.md` 使用 SQLite `.backup` 为独立会话库创建一致性备份，并验证 `integrity_check=ok`。
- 使用新代码 release 的迁移入口对同一会话库执行幂等迁移；不得把会话库复制进代码或 artifact release。
- 代码部署默认解析并沿用当前 artifact。若用户指定新 artifact，必须先通过注册表、`SHA256SUMS`、SQLite、向量/fast index、真实 artifact test 和回滚对检查。

### 6. 部署与验收

- 只调用新代码 release 自带的稳定入口：

```bash
bash <remote-code-release>/scripts/deploy \
  <remote-code-release> <artifact-release>
```

- 该入口负责检查回滚点、同步锁定依赖、验证 artifact、原子切换 generation、重启 screen、健康检查和失败自动回滚。
- 部署后至少核对：`current`/`current-artifact`、两个 screen、39280/39281/8011/8012、前后端 health、`degraded=false`、知识库 `integrity_check=ok`、会话库 `writable=true`。
- 执行一次真实 RAG；涉及流式或前端时，进一步验证 SSE headers、至少两个 `answer_delta` 先于 `done`、阶段耗时、历史恢复、复制和证据定位。
- 健康或验收失败时先确认自动回滚结果。旧版本仍不健康则立即停止并报告，不在生产目录临时修补代码。

### 7. 交付发布回执

最终必须报告：

- PR URL、合并方式和最终 `main` SHA；
- 代码 release id、前端 SHA-256、artifact release id 与清单 SHA-256；
- 会话备份路径、部署时间、线上 current/previous；
- CI、本地测试、artifact gate、健康、真实 RAG/SSE/浏览器验收结果；
- 自动回滚是否触发，以及精确的人工回滚入口。

不要把密钥、token、完整环境文件或私有凭据写入回执。

## 失败关闭条件

遇到以下任一情况不得继续：工作树含无关修改；本地 `main` 无法快进；CI 未完成或失败；PR 不可合并或仍有未解决对话；release 不是最终合并 SHA；目标 release 已存在；任一 manifest/hash 不匹配；artifact 未登记或门禁失败；previous 代码/制品不存在；会话备份失败；运行环境缺失；自动回滚后服务仍不健康。
