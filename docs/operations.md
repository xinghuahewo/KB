# 运维与部署

## 当前服务器

- SSH：`root@10.99.8.28`。
- 代码：`/home/wbt/DB`。
- 制品：`/srv/bgpkb/artifacts/releases/`。
- Python：`uv` 管理的项目虚拟环境。
- 常驻方式：现阶段保留 `screen`，不迁移 systemd。

VPN 或全局代理开启时使用：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28
```

## 服务契约

| 服务 | 地址/端口 | screen 会话 |
| --- | --- | --- |
| 静态前端 | `0.0.0.0:39280` | `bgpkb_frontend_wbt` |
| FastAPI | `0.0.0.0:39281` | `bgpkb_fastapi_wbt` |
| embedding | `10.99.8.28:8011` | 既有模型服务 |
| reranker | `10.99.8.28:8012` | 既有模型服务 |
| nginx | `http://10.99.8.28/` | 反代 `127.0.0.1:39280` |

FastAPI 启动必须设置 `BGP_RAG_REQUIRE_RERANKER=1`。会话库必须通过 `BGP_CHAT_DB_PATH` 指向代码和知识库 release 之外的持久路径，例如 `/srv/bgpkb/runtime/chat/chat_history.sqlite3`；`BGP_CHAT_CLIENT_SALT` 由外部环境文件提供且不得提交。所有密钥只从服务器环境变量读取。

nginx 对两个 SSE 入口直接反代到 `39281`，必须保留 `proxy_buffering off`、`proxy_cache off`、`X-Accel-Buffering: no` 和 `180s` 读写超时。其他请求仍由 `39280` 的静态前端代理转发。修改配置后先运行 `nginx -t`，成功后再 reload。

## 日常巡检

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'screen -ls | grep -E "bgpkb_(frontend|fastapi)_wbt"; \
   ss -ltnp | grep -E ":(39280|39281|8011|8012)"; \
   curl -fsS http://127.0.0.1:39281/health; echo; \
   curl -fsS http://127.0.0.1:39280/health; echo'
```

真实问答验收应确认：`answer_status=answered`、`vector_status=complete`、`rerank_status=complete`、`reranker_provider=local_http`、`degraded=False`。

`/health` 的 `chat_history` 节点还应满足：`writable=true`、`integrity_check=ok`、`schema_version=1`。会话库异常不得把只读知识库健康状态伪装成失败，但历史相关接口会返回 `503`。

## 会话库初始化、备份与恢复

首次启动或代码升级前执行幂等迁移：

```bash
cd /home/wbt/DB/current/backend
uv run python -m bgpkb.workflows.migrate_chat_database \
  --database /srv/bgpkb/runtime/chat/chat_history.sqlite3
```

在线备份必须调用待发布代码 release 内的稳定入口。该入口使用 Python 标准库
`sqlite3.Connection.backup()` 捕获 WAL 中已提交但尚未 checkpoint 的事务，先写同目录临时文件，
通过完整性、schema 和必要表检查后再以不覆盖方式原子落盘；目录权限固定为 `0700`，备份文件为
`0600`。不得直接复制在线主文件，也不依赖服务器安装 `sqlite3` CLI：

```bash
CHAT_DB=/srv/bgpkb/runtime/chat/chat_history.sqlite3
python3 /home/wbt/DB-code-releases/<新代码 release>/scripts/chat-database-maintenance \
  inspect --database "$CHAT_DB"
python3 /home/wbt/DB-code-releases/<新代码 release>/scripts/chat-database-maintenance \
  backup --database "$CHAT_DB" --backup-dir /srv/bgpkb/backups/chat
```

两个命令均输出不含密钥的 JSON 回执。`inspect` 或 `backup` 任一非零、`integrity_check` 非 `ok`、
`schema_version` 非 `1`、必要表缺失、目标已存在或权限设置失败，都必须停止部署。备份回执必须记录
路径、字节数和 SHA-256，供发布记录和人工回滚决策使用。

恢复前停止 FastAPI，保留故障库及其 `-wal`、`-shm` 文件，再把已校验备份复制到一个新路径。先用迁移命令验证新路径，随后只修改 `/etc/bgpkb/runtime.env` 中的 `BGP_CHAT_DB_PATH` 并重启。不要用回滚代码的方式覆盖会话库。

```bash
screen -S bgpkb_fastapi_wbt -X quit
install -m 600 /srv/bgpkb/backups/chat/<备份文件> \
  /srv/bgpkb/runtime/chat/chat_history-restored.sqlite3
BGP_CHAT_DB_PATH=/srv/bgpkb/runtime/chat/chat_history-restored.sqlite3 \
  uv run python -m bgpkb.workflows.migrate_chat_database
```

代码回滚与会话库回滚相互独立：前端或 FastAPI 版本失败时，切回上一代码 generation，仍保留当前会话库；只有确认 schema 不兼容或数据损坏时才切换到已校验的会话备份。当前代码会拒绝打开高于自身支持版本的 schema，防止旧代码误写新库。

## Docling 路由

- 镜像：`bgpkb-docling-v2:2.107.0-cu128`。
- 镜像 ID：`sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2`。
- 运行矩阵：Python 3.11、Docling 2.107.0、PyTorch 2.10.0+cu128、CUDA 12.8。
- 服务器：`root@10.99.8.28`，4 × NVIDIA GeForce RTX 2080 Ti，每卡 11264 MiB，驱动 545.23.08，Docker 29.1.3。
- 默认 GPU：GPU 1，参数 `--device nvidia.com/gpu=1`。
- 必须 `--network none`；不启动 HTTP API 或常驻服务。
- GPU 0 未经检查不得使用；GPU 2/3 使用前重新执行 `nvidia-smi`。
- 构建文件：`/srv/bgpkb/docling-build`；模型：`/srv/bgpkb/docling-models`。

五阶段候选的 Docling 重处理默认关闭。确认候选计划确有待处理来源后，使用：

```bash
make canonicalize CANDIDATE_DIR=<候选目录> \
  PIPELINE_ARGS="<冻结输入参数> --docling-execution-mode remote"
```

该参数是 Docling 作业的显式授权开关；`--plan-only` 和默认 `disabled` 均不得启动作业。
生产 runner 先把策略目标 `10.99.8.28` 与本机地址做失败关闭判定：流水线已在该主机运行时
直接调用锁定命令；从外部运行时固定使用
`ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28`。
不得通过 SSH 自连、复制密钥或修改服务器配置解决执行面问题。local 与 remote 两种执行面
必须产生等价命令，并在转换前完成以下失败关闭检查：

1. GPU 1 存在且没有计算进程；不得仅凭显存数字推断空闲。
2. 本地镜像 ID 与策略中的不可变 digest 完全一致。
3. 临时容器使用 `--device nvidia.com/gpu=1 --network none`。
4. CUDA 实际可用，离线环境有效，5 个锁定模型的实际 SHA-256 全部匹配。
5. source snapshot 在转换前后 hash 不变，所有 payload 和 Canonical 输出均位于候选目录。

宿主只把计划声明且 hash 匹配的普通文件复制到候选
`.pipeline/tmp/docling/run-*/input`：拒绝 symlink、hardlink、重复目标和路径越界，目录为
`0555`、文件为 `0444`，原始 `0600` 输入保持不变。容器只读挂载该 input，并分别挂载
最小 writable output/work/cache；不得读写挂载整个候选。宿主在容器结束后复核 source
binding、文件类型、payload hash 和路径，再原子物化正式 payload 目录及回执。成功、失败
或受控中断均清理 `run-*`，失败不得留下正式 payload manifest。

执行记录位于候选 `.pipeline/logs/canonicalize/`，运行时和 5 模型证据位于
`data/manifests/docling_runtime_evidence_v1.json`。任一文档失败、回执缺失、hash 不符或
路径越界时，不得继续 `semantic-build`。长任务应查看容器进程、GPU 1、日志和已完成文档计数；
耗时本身不是失败依据。

模型必须先离线预取并通过 `verify_offline_runtime.py` 校验，再作为独立构建上下文注入镜像；生产阶段不得下载模型：

```bash
docker buildx build \
  --build-context model_assets=/srv/bgpkb/docling-models \
  --build-arg DEBIAN_MIRROR=<可选镜像地址> \
  -t bgpkb-docling-v2:2.107.0-cu128 \
  backend/deploy/docling
```

不需要 Debian 镜像时省略 `--build-arg DEBIAN_MIRROR=`，保持 Dockerfile 默认软件源。

## 部署顺序

1. 检查磁盘、GPU、端口、screen 和回滚版本。
2. 按 [RAG 五阶段流水线](pipeline.md) 完成候选构建和 `verify-release`，确认没有 `fail` 或 `skipped_blocking`。
3. 用明确 release id 执行 `verify-artifacts` 和 artifact gate，核对代码/制品成对回滚点。
4. 部署代码到版本目录，不覆盖当前运行目录。
5. 原子切换代码与制品指针，重启既有 screen 会话。
6. 验证前端、FastAPI、embedding、reranker 和真实问答。
7. 失败时执行统一 rollback，恢复上一代码和制品指针。

部署第 1 步必须同时记录当前 `BGP_CHAT_DB_PATH` 并生成一致性备份；部署第 5 步前先执行会话库迁移。回滚代码时不得删除、覆盖或随 release 移动独立会话库。

## 稳定入口与首次迁移

```bash
make release ARGS=<code-release-id>
make deploy ARGS="<code-release-dir> <artifact-release-dir>"
make rollback
```

默认部署根目录是 `/home/wbt/DB`，代码版本目录是 `/home/wbt/DB-code-releases`。部署状态分别记录当前/上一代码和制品版本。`bgp_knowledge_base` 与 `chat_frontend` 是指向 `current/backend`、`current/frontend` 的限期兼容链接，唯一真实源码位于版本目录。

代码、制品、部署状态和两个兼容路径都经由一个 `current-generation` 指针解析；部署只原子切换这个指针。`release` 只接受干净 Git commit，并从 `git archive` 导出源码；前端 `out/` 作为已验证构建产物单独加入，release 不复制工作树中的 `.env` 或其他未跟踪文件。

运行密钥和服务环境固定保存在仓库外 `/etc/bgpkb/runtime.env`，权限由服务器管理员控制。部署前必须确认该文件存在、可读，并至少保留现有 DeepSeek 和模型服务配置。

模型服务仅绑定服务器地址时，运行环境还应设置 `BGPKB_EMBEDDING_HEALTH_URL=http://10.99.8.28:8011/health` 和 `BGPKB_RERANKER_HEALTH_URL=http://10.99.8.28:8012/health`。重启与健康检查脚本都会读取同一个外置环境文件，避免切换成功后被 localhost 探测误判并回滚。

首次迁移必须先建立可回滚的旧版本，不能直接部署新版本：

1. 在移动任何目录前，从已提交的新代码运行 `make release ARGS=<candidate-id>`，得到 `/home/wbt/DB-code-releases/<candidate-id>`。
2. 确认 `/etc/bgpkb/runtime.env` 已从现有服务环境安全迁出并限制权限。
3. 将现有 `/home/wbt/DB` 整体移动为 `/home/wbt/DB-code-releases/legacy-<时间>`，保留其中的虚拟环境和前端 `out/index.html`。
4. 在该旧版本根目录建立 `backend -> bgp_knowledge_base`、`frontend -> chat_frontend` 两个链接。
5. 创建新的空 `/home/wbt/DB`，使用候选版本中的绝对脚本路径执行：`python3 /home/wbt/DB-code-releases/<candidate-id>/scripts/deployment.py bootstrap /home/wbt/DB <legacy-code-dir> /srv/bgpkb/artifacts/releases/<release-id>`。
6. 运行候选版本中的 `scripts/check-service-health`，确认旧服务仍然可用，再运行候选版本中的 `scripts/deploy` 部署新版本。

部署入口会在切换前执行 `check-rollback`；没有有效上一代码和制品版本时失败关闭。稳定运行一个发布周期且启动命令全部改用 `current/backend`、`current/frontend` 后，删除两个兼容链接。
