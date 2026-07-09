# 项目记忆

## 文档语言

- 生成的文档始终使用中文。

## Docling 私有服务器资源

以下信息于 2026-07-04 验证，用于 BGP 知识库的离线 Docling 批处理。

### 连接

- SSH 目标：`root@10.99.8.28`。
- 本地已设置到 `10.99.8.28` 的路由，并已配置免密 SSH 登录；可通过 SSH 直接操控该服务器。
- 在系统 VPN 或全局代理开启时，SSH 连接建议显式禁用 SSH 代理配置：`ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 ...`。
- 当前未登记必需的 SSH 源地址绑定；不得沿用旧服务器的 `10.29.98.116` 路由假设。
- 不在仓库中记录密码、私钥、token 或其他凭据。

### 项目计算路由

- Docling 离线批处理默认路由到 `root@10.99.8.28` 的 GPU 1。
- Docker 通过 CDI 参数 `--device nvidia.com/gpu=1` 暴露单张 GPU，不使用 `--gpus all`。
- GPU 0 在迁移验收时已被其他任务占用；未经检查不得调度 Docling 到 GPU 0。
- GPU 2 和 GPU 3 可作候选，但每次运行前必须用 `nvidia-smi` 重新确认空闲状态。
- 本项目不依赖 Docling HTTP API；计算路由是 SSH + Docker 离线批处理。

### 硬件与驱动

- 操作系统：Ubuntu `22.04.5 LTS`，Linux `5.15.0-94-generic`，`amd64`。
- GPU：4 × `NVIDIA GeForce RTX 2080 Ti`。
- 单卡显存：`11264 MiB`。
- NVIDIA 驱动：`545.23.08`；服务器不重置、不升级驱动。

### Docker 与 GPU 运行时

- Docker Engine：`29.1.3`。
- Docker API：`1.52`。
- Docker Buildx：`0.17.1`。
- 可用 runtime：`io.containerd.runc.v2`、`runc`；默认 runtime 为 `runc`。
- NVIDIA Container Toolkit 以 CDI 登记 `nvidia.com/gpu=0..3` 和 `nvidia.com/gpu=all`。

### Docling 离线基线

- 已验证镜像：`bgpkb-docling-v2:2.107.0-cu128`。
- 镜像 ID：`sha256:273131691988d0b069c158fea9d5ea9aa597d5cc095288c3ee0baed315fc24f2`。
- PyTorch：`2.10.0+cu128`。
- CUDA 运行时：`12.8`。
- 5 个锁定模型的 SHA-256 已验证匹配。
- 已在 GPU 1 和 `--network none` 下通过 GPU、CUDA 实际运算、模型哈希和离线启动预检。
- SBOM 和 Python 许可证清单已随镜像生成并验证存在。
- 运行面仅使用批处理命令，不启动 HTTP API 或常驻服务。

### 当前持久化部署路径

- 构建文件：`/srv/bgpkb/docling-build`。
- 模型文件：`/srv/bgpkb/docling-models`。

## BGP 知识库远端交互式部署

以下信息于 2026-07-09 验证，用于 BGP 知识库前端和 FastAPI 问答服务。

### 部署路径与运行方式

- 当前项目副本部署在 `root@10.99.8.28:/home/wbt/DB`。
- 知识库后端目录：`/home/wbt/DB/bgp_knowledge_base`。
- 对话前端目录：`/home/wbt/DB/chat_frontend`。
- 当前使用 `screen` 常驻运行，不迁移到 systemd。
- 远端 Python 环境使用 `uv` 管理，虚拟环境位于 `/home/wbt/DB/bgp_knowledge_base/.venv`。

### 服务端口

- 静态前端：`0.0.0.0:39280`，screen 会话名 `bgpkb_frontend_wbt`。
- FastAPI 后端：`0.0.0.0:39281`，screen 会话名 `bgpkb_fastapi_wbt`。
- nginx 裸 IP 入口：`http://10.99.8.28/` 反向代理到 `127.0.0.1:39280`。
- embedding 服务：`10.99.8.28:8011`，模型 `BAAI/bge-m3`。
- reranker 服务：`10.99.8.28:8012`，模型 `BAAI/bge-reranker-v2-m3`。
- 旧前端端口 `3001` 已停止；远端当前 FastAPI 不使用 `8000`。

### RAG 运行边界

- FastAPI 启动时设置 `BGP_RAG_REQUIRE_RERANKER=1`，前端问答默认要求真实 reranker。
- 当前端到端问答已验证：`answer_status=answered`、`vector_status=complete`、`rerank_status=complete`、`reranker_provider=local_http`、`degraded=False`。
- DeepSeek API 仍由后端环境变量读取；不得在仓库中记录真实密钥。

### 快速巡检命令

```bash
ssh -F /dev/null -o ProxyCommand=none -o ProxyJump=none root@10.99.8.28 \
  'screen -ls | grep -E "bgpkb_(frontend|fastapi)_wbt"; \
   ss -ltnp | grep -E ":(39280|39281|8011|8012)"; \
   curl -s http://127.0.0.1:39281/health; echo; \
   curl -s http://127.0.0.1:39280/health; echo'
```

### 快速验证命令

```bash
ssh root@10.99.8.28 \
  'nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv,noheader'
```

```bash
ssh root@10.99.8.28 \
  'docker run --rm --device nvidia.com/gpu=1 --network none bgpkb-docling-v2:2.107.0-cu128'
```
