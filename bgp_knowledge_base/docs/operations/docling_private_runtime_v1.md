# Docling 私有 GPU 运行环境 v1

## 目标服务器事实

本基线采集于 2026-07-01，目标为独立 Linux x86_64 GPU 服务器：

- GPU：NVIDIA TITAN RTX，24576 MiB 显存。
- NVIDIA 驱动：570.133.07。
- Docker：Docker 28.0.4，Server API 1.48。
- 容器 runtime：已安装 `nvidia` runtime，默认 runtime 保持 `runc`。
- 运行方式：仅批处理，不启动 HTTP API；生产容器使用 `--gpus all --network none`。

## 锁定版本矩阵

| 层次 | 锁定版本 | 选择依据 |
| --- | --- | --- |
| Python | Python 3.11 | Docling 2.107.0 要求 Python 3.10 及以上；3.11 兼顾依赖成熟度与维护周期。 |
| Docling | Docling 2.107.0 | 2026-06-24 发布的正式版本，依赖由 hash lock 固定。 |
| PyTorch | PyTorch 2.10.0 + cu128 | 官方 CUDA 12.8 Linux x86_64 wheel，固定为 `torch==2.10.0+cu128`。 |
| CUDA | CUDA 12.8 | NVIDIA 570.133.07 高于 CUDA 12.8 Update 1 的最低 Linux 驱动 570.124.06。 |
| OCR | RapidOCR 3.9.0 / PP-OCRv4 | Docling 标准安装的本地 OCR 路径，保留中英文模型，不调用外部服务。 |
| 容器 | `python:3.11.15-slim-bookworm` | CUDA 用户态库由 cu128 wheel 锁定，宿主只提供 NVIDIA 驱动与容器 runtime。 |

参考：

- Docling 安装说明：https://docling-project.github.io/docling/getting_started/installation/
- Docling 离线模型说明：https://docling-project.github.io/docling/usage/advanced_options/
- NVIDIA CUDA 12.8.1 发布说明：https://docs.nvidia.com/cuda/archive/12.8.1/cuda-toolkit-release-notes/
- PyTorch CUDA 12.8 wheel 索引：https://download.pytorch.org/whl/cu128/

## 构建与供应链证据

联网构建阶段执行以下动作：

1. 使用 `requirements.lock` 和 `--require-hashes` 安装全部 Python 依赖。
2. 使用锁定 Docling 下载默认模型，并按 `model_manifest.json` 复核目录级 SHA-256。
3. 生成 CycloneDX SBOM 与 Python 许可证清单。
4. 构建结束后记录镜像 digest；模型文件不进入 Git。

模型目录摘要使用 `sha256-tree-v1`：忽略下载器 `.cache`，按相对路径排序，把相对路径、文件大小和文件 SHA-256 顺序写入总 SHA-256。上游模型内容漂移会直接使镜像构建失败。

## 构建命令

```bash
docker build \
  --pull \
  --tag bgpkb-docling-v2:2.107.0-cu128 \
  --file bgp_knowledge_base/deploy/docling/Dockerfile \
  bgp_knowledge_base

docker image inspect bgpkb-docling-v2:2.107.0-cu128 \
  --format '{{json .RepoDigests}}'
```

## 断网预检

```bash
docker run --rm \
  --gpus all \
  --network none \
  bgpkb-docling-v2:2.107.0-cu128
```

预检必须同时满足：CUDA 可用、GPU 名称可读、全部模型存在且 hash 一致、离线环境变量正确。任何检查失败时，命令以非零状态退出，并且不得读取正式语料。

## 运行边界

- 生产不挂载 Hugging Face 缓存，不允许运行时下载模型。
- `HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1` 和 `DOCLING_ARTIFACTS_PATH` 由镜像固定。
- 模型升级必须更新版本、实际 hash、许可证清单和镜像 digest，并重新执行断网 fixture 验收。
- 当前不启用 VLM、图片语义解释、远程 OCR、Docling Serve 或任何 HTTP API。
