# DB 发布契约

本文件补充发布编排所需的固定事实；权威运行说明仍以仓库 `docs/` 和实际脚本为准。若两者不一致，先停止并按仓库脚本与当前服务器状态核实，不沿用本文件的旧值。

## 固定目标

| 项目 | 当前值 |
| --- | --- |
| GitHub 仓库 | `xinghuahewo/KB` |
| 生产 SSH | `root@10.99.8.28` |
| 部署根 | `/home/wbt/DB` |
| 代码 release 根 | `/home/wbt/DB-code-releases` |
| artifact 根 | `/srv/bgpkb/artifacts/releases` |
| 会话库默认路径 | `/srv/bgpkb/runtime/chat/chat_history.sqlite3` |
| 外置运行环境 | `/etc/bgpkb/runtime.env` |
| 前端/FastAPI | `39280` / `39281` |
| embedding/reranker | `8011` / `8012` |
| screen | `bgpkb_frontend_wbt` / `bgpkb_fastapi_wbt` |

SSH 固定禁用代理跳转：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28
```

## 阶段门禁

| 阶段 | 必须成立 | 证据 |
| --- | --- | --- |
| 提交前 | 变更有明确归属，测试与构建成功 | `git status`、测试日志 |
| 推送前 | `codex/**` 分支、工作树干净、GitHub 已认证 | `preflight.py --phase publish` |
| 合并前 | push/PR CI 均成功，可合并，无未解决对话 | PR 状态和 expected head SHA |
| release 前 | 本地 `main == origin/main` | 完整 Git SHA |
| 上传后 | manifest、前端 hash、全树 hash 一致 | 上传工具 JSON 回执 |
| 切换前 | previous 有效，artifact 已验证，会话库直接检查及备份完整 | 生产预检与稳定备份入口 JSON 回执 |
| 切换后 | 指针、screen、四端口、health 正常 | 线上巡检输出 |
| 产品验收 | 真实问答成功；相关变更的 SSE/UI 行为正常 | API/浏览器验收摘要 |

## GitHub 编排

优先使用已连接的 GitHub 工具创建 PR、读取合并状态和执行合并；使用 `gh` 等待 Actions 或补足连接器未覆盖的状态。

```bash
git fetch --prune origin
git push --set-upstream origin HEAD
gh pr checks <pr-number> --watch --fail-fast
gh pr view <pr-number> \
  --json state,mergeable,mergeStateStatus,statusCheckRollup,reviewDecision,url
```

合并时绑定 expected head SHA。合并后只能：

```bash
git fetch origin main
git switch main
git merge --ff-only origin/main
```

禁止直接推送 `main`、force push、非 fast-forward 更新或使用陈旧本地 `main` 覆盖远端。

## 代码与 artifact 边界

- 通用代码部署沿用当前 `current-artifact`，不重建、不修改、不重新登记 artifact。
- 新 artifact 必须来自独立候选目录，完成 `verify-release`，且所有真实门禁均为 pass；`skipped_blocking` 仍是失败。
- `canonicalize` 需要 Docling 重处理时，必须通过稳定入口显式设置
  `--docling-execution-mode remote`。计划、payload、运行时证据、严格 Canonical、manifest、
  日志、临时目录和缓存均只能写候选；旧 release、`current`、`previous` 与冻结 snapshot
  保持只读。默认模式和 `--plan-only` 不得启动 SSH、Docker 或 GPU 作业。
- 远端 Docling 必须使用固定无代理 SSH、锁定镜像 digest、GPU 1 和 `--network none`，
  并在执行前通过 GPU 空闲、CUDA、离线环境与 5 模型 hash 预检。任一文档失败、source/output
  hash 不符、路径越界或 manifest 集合不闭合都必须停止发布。
- 代码 release 与 artifact 必须成对记录，但不得交叉拼接未经验证的新旧版本。
- release 目录不可变；修复必须产生新提交和新 release id。

## 会话库与回滚

- 会话库位于代码和 artifact release 之外，部署前使用 SQLite 在线备份 API，不能直接复制在线主文件。
- 会话库门禁不依赖当前服务版本的 health 字段；`preflight.py` 必须调用
  `scripts/chat-database-maintenance inspect` 做直接只读检查。备份只调用新代码 release 内的
  `scripts/chat-database-maintenance backup`，由 Python `sqlite3.Connection.backup()` 捕获 WAL，
  验证完整性、schema 和必要表后原子落盘，不依赖 `sqlite3` CLI。
- 代码回滚不回滚会话库。只有确认 schema 不兼容或数据损坏并取得明确授权后，才恢复会话备份。
- `scripts/deploy` 在重启或基础健康检查失败时自动交换回 previous 代码/制品对；随后仍要核对实际指针和旧版本健康。
- 人工回滚稳定入口：`make rollback`，必须从当前激活代码或明确的已验证 release 执行。

## 变更范围对应验收

- 仅文档或元数据：CI、release manifest、基础 health。
- 后端 API/RAG：增加真实 DeepSeek 问答，检查 answered、rerank complete、local_http、非降级。
- SSE：检查 `Content-Type: text/event-stream`、`X-Accel-Buffering: no`、sequence、多个 delta 先于 done、timings。
- 前端：使用真实浏览器验证目标视口、刷新恢复、历史切换、复制反馈和证据定位；HTML 必须
  `Cache-Control: no-store`，条件请求不得返回 `304`，当前 HTML 引用的 CSS/JS 必须全部 `200`。
- nginx：必须先 `nginx -t`，再 reload；未经用户明确授权不得修改。
