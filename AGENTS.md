# 项目记忆

## 文档语言

- 生成的文档始终使用中文。

## Docling 私有服务器资源

以下信息于 2026-07-02 验证，用于 BGP 知识库的离线 Docling 批处理。

### 连接

- SSH 目标：`nic@10.109.242.145`。
- 本机路由需要时显式绑定源地址：`ssh -b 10.29.98.116 nic@10.109.242.145`。
- 当前环境已配置 SSH 免密登录。
- 不在仓库中记录密码、私钥、token 或其他凭据。

### 硬件与驱动

- 操作系统/架构：Linux `amd64`。
- GPU：`NVIDIA TITAN RTX`。
- 显存：`24576 MiB`。
- NVIDIA 驱动：`570.133.07`。

### Docker 与 GPU 运行时

- Docker Engine：`28.0.4`。
- Docker API：`1.48`。
- 可用 runtime：`io.containerd.runc.v2`、`nvidia`、`runc`。
- 默认 runtime：`runc`；GPU 任务必须显式使用 `--gpus all`。

### Docling 离线基线

- 已验证镜像：`bgpkb-docling-v2:2.107.0-cu128`。
- PyTorch：`2.10.0+cu128`。
- CUDA 运行时：`12.8`。
- 5 个锁定模型的 SHA-256 已验证匹配。
- 已在 `--network none` 下通过 GPU、模型哈希和离线启动预检。
- 运行面仅使用批处理命令，不启动 HTTP API 或常驻服务。

### 当前临时部署路径

- 部署文件：`/tmp/bgpkb-docling-v2`。
- 模型文件：`/tmp/bgpkb-docling-models`。
- `/tmp` 路径不是持久化保证；服务器重启或清理前，需要确认文件仍然存在。

### 快速验证命令

```bash
ssh -b 10.29.98.116 nic@10.109.242.145 \
  'nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader'
```

```bash
ssh -b 10.29.98.116 nic@10.109.242.145 \
  'docker run --rm --gpus all --network none bgpkb-docling-v2:2.107.0-cu128'
```

