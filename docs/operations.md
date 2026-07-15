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

FastAPI 启动必须设置 `BGP_RAG_REQUIRE_RERANKER=1`，密钥只从服务器环境变量读取。

## 日常巡检

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'screen -ls | grep -E "bgpkb_(frontend|fastapi)_wbt"; \
   ss -ltnp | grep -E ":(39280|39281|8011|8012)"; \
   curl -fsS http://127.0.0.1:39281/health; echo; \
   curl -fsS http://127.0.0.1:39280/health; echo'
```

真实问答验收应确认：`answer_status=answered`、`vector_status=complete`、`rerank_status=complete`、`reranker_provider=local_http`、`degraded=False`。

## Docling 路由

- 镜像：`bgpkb-docling-v2:2.107.0-cu128`。
- 镜像 ID：`sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2`。
- 运行矩阵：Python 3.11、Docling 2.107.0、PyTorch 2.10.0+cu128、CUDA 12.8。
- 服务器：`root@10.99.8.28`，4 × NVIDIA GeForce RTX 2080 Ti，每卡 11264 MiB，驱动 545.23.08，Docker 29.1.3。
- 默认 GPU：GPU 1，参数 `--device nvidia.com/gpu=1`。
- 必须 `--network none`；不启动 HTTP API 或常驻服务。
- GPU 0 未经检查不得使用；GPU 2/3 使用前重新执行 `nvidia-smi`。
- 构建文件：`/srv/bgpkb/docling-build`；模型：`/srv/bgpkb/docling-models`。

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
