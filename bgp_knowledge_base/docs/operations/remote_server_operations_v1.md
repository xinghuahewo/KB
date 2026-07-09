---
title: "远端服务器与前端部署操作手册 v1"
document_type: "运维操作手册"
purpose: "集中记录 10.99.8.28 的 SSH 连接、GPU 资源、Docling、阶段 B 检索模型服务、FastAPI 后端和静态前端部署操作。"
scope: "root@10.99.8.28 上与 BGP 知识库相关的运行、复核和部署操作"
status: "现行操作手册"
last_reviewed: "2026-07-09"
---
# 远端服务器与前端部署操作手册 v1

## 1. 适用范围

本文档是 `root@10.99.8.28` 上 BGP 知识库相关操作的统一入口，覆盖：

- SSH 连接与代理绕过。
- GPU 使用边界。
- Docling 离线批处理快速复核。
- 阶段 B embedding/reranker 常驻服务复核。
- BGP KB FastAPI 后端启动与健康检查。
- 对话前端静态 `dist/out` 构建、上传和 `screen` 后台运行。

当前 FastAPI 和静态前端均使用 `screen` 常驻运行；不迁移到 systemd。本文中的 `systemctl reload nginx` 仅用于 nginx 配置重载。

模型密钥、私钥、token、密码等凭据不得写入仓库；真实密钥只允许通过服务器环境变量或受控密钥管理方式注入。

## 2. SSH 连接

本地已设置到 `10.99.8.28` 的路由，并已配置免密 SSH 登录，可直接操控服务器。

在系统 VPN 或全局代理开启时，SSH 连接建议显式禁用本地 SSH 代理配置：

```bash
ssh -F /dev/null \
  -o ProxyCommand=none \
  -o ProxyJump=none \
  root@10.99.8.28 'hostname'
```

常用别名可放在本机 shell 配置中，但不要提交到仓库：

```bash
alias ssh-bgpkb='ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28'
```

快速连通性检查：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'hostname; uptime; whoami'
```

## 3. 服务器资源与端口

当前服务器事实：

- 操作系统：Ubuntu `22.04.5 LTS`，Linux `5.15.0-94-generic`，`amd64`。
- GPU：4 × `NVIDIA GeForce RTX 2080 Ti`，单卡显存 `11264 MiB`。
- NVIDIA 驱动：`545.23.08`。
- Docker Engine：`29.1.3`。
- NVIDIA CDI：`nvidia.com/gpu=0..3` 和 `nvidia.com/gpu=all`。

项目端口约定：

| 端口 | 服务 | 当前用途 |
| ---: | --- | --- |
| 80 | nginx | 裸 IP 入口，Host 为 `10.99.8.28` 时反向代理到本机 `127.0.0.1:39280`。 |
| 39281 | BGP KB FastAPI | 知识库只读后端，前端同源代理默认转发到本机 `127.0.0.1:39281`。 |
| 8011 | embedding | `BAAI/bge-m3` 私有 embedding 服务。 |
| 8012 | reranker | `BAAI/bge-reranker-v2-m3` 私有 reranker 服务。 |
| 39280 | 静态前端 | `chat_frontend/out` 静态页面 + Python 同源代理。 |

注意：服务器 `3000` 端口已被其他服务占用；当前前后端使用非常规端口 `39280/39281`。旧 `3001` 前端会话已停止。

查看端口和后台会话：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'screen -ls; ss -ltnp | grep -E ":(80|39280|39281|8011|8012)" || true'
```

## 4. GPU 使用边界

GPU 路由规则：

- Docling 离线批处理默认使用 GPU 1。
- 阶段 B retrieval 模型服务当前使用 GPU 2 和 GPU 3。
- GPU 0 在迁移验收时被其他任务占用；未经检查不得调度到 GPU 0。
- 每次运行前必须用 `nvidia-smi` 重新确认实时空闲状态，不把历史空闲状态当作永久事实。

GPU 复核命令：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv,noheader'
```

## 5. Docling 离线批处理复核

Docling 详细基线见 [Docling 私有 GPU 运行环境 v1](docling_private_runtime_v1.md)。这里仅保留日常操作入口。

已验证镜像：

```text
bgpkb-docling-v2:2.107.0-cu128
```

快速断网预检：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'docker run --rm --device nvidia.com/gpu=1 --network none bgpkb-docling-v2:2.107.0-cu128'
```

运行边界：

- 使用 SSH + Docker 离线批处理，不启动 Docling HTTP API。
- Docker 通过 CDI 参数 `--device nvidia.com/gpu=1` 暴露单张 GPU，不使用 `--gpus all`。
- 生产运行使用 `--network none`，不得运行时下载模型。
- 持久化路径：
  - `/srv/bgpkb/docling-build`
  - `/srv/bgpkb/docling-models`

## 6. 阶段 B 检索模型服务复核

阶段 B 详细交付说明见 [阶段 B 层级检索 v1](../stages/stage_b_hierarchical_retrieval_v1.md)。这里保留日常服务复核。

当前 Docker Compose project：

```text
bgpkb-retrieval-models
```

服务矩阵：

| 服务 | 端口 | 模型 | GPU |
| --- | ---: | --- | --- |
| embedding | 8011 | `BAAI/bge-m3` | GPU 2 |
| reranker | 8012 | `BAAI/bge-reranker-v2-m3` | GPU 3 |

健康检查：

```bash
curl --fail http://10.99.8.28:8011/health
curl --fail http://10.99.8.28:8012/health
```

容器和 GPU 检查：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}" | grep -E "retrieval|8011|8012"; \
   nvidia-smi --query-gpu=index,name,memory.total,memory.used --format=csv,noheader,nounits'
```

注意：8011/8012 只负责 embedding 和 rerank；它们不是 RAG Answer HTTP 后端。前端问答仍需要 BGP KB FastAPI 在 39281 端口运行。

## 7. BGP KB FastAPI 后端

FastAPI 后端位于 `bgp_knowledge_base/src/bgpkb/service/`，默认读取知识库发布产物和 RAG 配置。

本地开发启动：

```bash
cd bgp_knowledge_base
uv sync
uv run uvicorn bgpkb.service.app:app --reload --host 127.0.0.1 --port 39281
```

远端常驻启动使用 `screen`，当前项目目录为 `/home/wbt/DB/bgp_knowledge_base`：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'cd /home/wbt/DB/bgp_knowledge_base && \
   uv sync && \
   screen -S bgpkb_fastapi_wbt -X quit 2>/dev/null || true && \
   screen -dmS bgpkb_fastapi_wbt bash -lc '"'"'cd /home/wbt/DB/bgp_knowledge_base && set -a; [ -f .env ] && . ./.env; set +a; export BGP_RAG_REQUIRE_RERANKER=1; uv run uvicorn bgpkb.service.app:app --host 0.0.0.0 --port 39281'"'"''
```

检查后端：

```bash
curl --fail http://10.99.8.28:39281/health
curl --fail -X POST http://10.99.8.28:39281/api/v1/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"什么是 BGP 路由泄露？","limit":8}'
```

如果只部署了静态前端而 39281 未启动，前端页面可以打开，但问答会返回后端不可用。

## 8. 静态前端构建与部署

前端项目位于仓库同级目录 `chat_frontend/`，当前部署形态是：

```text
Next.js static export out/
  + serve_static_with_proxy.py
  + screen 后台运行在 10.99.8.28:39280
  + /api/、/health、/sources/、/entities/、/search 同源代理到 127.0.0.1:39281
```

本地构建：

```bash
cd chat_frontend
corepack yarn build
```

打包上传：

```bash
cd chat_frontend
FRONTEND_DIR="$PWD"
COPYFILE_DISABLE=1 tar -czf /tmp/bgp_chat_frontend_dist.tgz \
  -C "$FRONTEND_DIR/out" . \
  -C "$FRONTEND_DIR/scripts" serve_static_with_proxy.py

scp -F /dev/null -o ProxyCommand=none -o ProxyJump=none \
  /tmp/bgp_chat_frontend_dist.tgz root@10.99.8.28:/home/wbt/DB/chat_frontend/
```

远端解包并重启前端：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'cd /home/wbt/DB/chat_frontend && \
   rm -rf out && mkdir -p out && \
   tar -xzf /home/wbt/DB/chat_frontend/bgp_chat_frontend_dist.tgz -C out && \
   chmod +x scripts/serve_static_with_proxy.py && \
   screen -S bgpkb_frontend_wbt -X quit 2>/dev/null || true && \
   screen -dmS bgpkb_frontend_wbt bash -lc '"'"'cd /home/wbt/DB/chat_frontend && BGP_RAG_BASE_URL=http://127.0.0.1:39281 ./scripts/serve_static_with_proxy.py --directory /home/wbt/DB/chat_frontend/out --port 39280 --host 0.0.0.0'"'"''
```

检查前端：

```bash
curl -I http://10.99.8.28:39280/
curl http://10.99.8.28:39280/health
```

浏览器访问：

```text
http://10.99.8.28/
http://10.99.8.28:39280/
```

`/health` 由静态前端代理到 FastAPI 后端；如果返回 `BGP FastAPI unavailable`，优先检查 39281 端口后端，而不是重启前端。

## 9. nginx 裸 IP 入口

`http://10.99.8.28/` 由 nginx 80 端口反向代理到本机 `127.0.0.1:39280`。配置文件：

```text
/etc/nginx/sites-available/bgpkb_frontend
/etc/nginx/sites-enabled/bgpkb_frontend
```

当前配置只匹配 `server_name 10.99.8.28`，不影响已有 `4321` Ollama 代理。

复核和重载：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'nginx -t && systemctl reload nginx && curl -I http://10.99.8.28/'
```

## 10. screen 管理

查看会话：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 'screen -ls'
```

进入前端会话：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28
screen -r bgpkb_frontend_wbt
```

进入后端会话：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28
screen -r bgpkb_fastapi_wbt
```

在 `screen` 内退出查看但保留后台运行：按 `Ctrl-a`，再按 `d`。

停止指定会话：

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'screen -S bgpkb_frontend_wbt -X quit'
```

## 11. 一键状态巡检

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'hostname; \
   echo "[screen]"; screen -ls || true; \
   echo "[ports]"; ss -ltnp | grep -E ":(80|39280|39281|8011|8012)" || true; \
   echo "[gpu]"; nvidia-smi --query-gpu=index,name,memory.used,memory.total --format=csv,noheader,nounits; \
   echo "[containers]"; docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "retrieval|8011|8012" || true'
```

本机健康检查：

```bash
curl --fail http://10.99.8.28/
curl --fail http://10.99.8.28:39280/
curl --fail http://10.99.8.28:8011/health
curl --fail http://10.99.8.28:8012/health
curl --fail http://10.99.8.28:39281/health
```

如果 39280 正常但 39281 不通，说明静态前端服务仍在，问答后端未运行或端口不可达。
