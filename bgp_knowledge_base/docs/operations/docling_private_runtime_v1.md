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

构建准备与镜像构建阶段执行以下动作：

1. 使用 `requirements.lock` 和 `--require-hashes` 安装全部 Python 依赖。
2. 在可联网的受控准备机使用锁定 Docling 预取默认模型，并按 `model_manifest.json` 复核目录级 SHA-256。
3. 把已验证的只读模型目录作为 Docker 命名构建上下文 `model_assets` 注入镜像；镜像构建本身不访问 Hugging Face。
4. 生成 CycloneDX SBOM 与 Python 许可证清单。
5. 构建结束后记录镜像 digest；模型文件不进入 Git。

模型目录摘要使用 `sha256-tree-v1`：忽略下载器 `.cache`，按相对路径排序，把相对路径、文件大小和文件 SHA-256 顺序写入总 SHA-256。上游模型内容漂移会直接使镜像构建失败。

## 构建命令

```bash
python bgp_knowledge_base/deploy/docling/verify_offline_runtime.py \
  --manifest bgp_knowledge_base/deploy/docling/model_manifest.json \
  --model-root /srv/bgpkb/docling-models \
  --skip-gpu \
  --skip-offline

docker build \
  --pull \
  --network host \
  --build-arg DEBIAN_MIRROR=https://mirrors.ustc.edu.cn \
  --build-context model_assets=/srv/bgpkb/docling-models \
  --tag bgpkb-docling-v2:2.107.0-cu128 \
  --file bgp_knowledge_base/deploy/docling/Dockerfile \
  bgp_knowledge_base

docker image inspect bgpkb-docling-v2:2.107.0-cu128 \
  --format '{{json .RepoDigests}}'
```

`DEBIAN_MIRROR` 是可选构建参数；不传时继续使用 Debian 官方源。在官方源延迟较高的网络中，可显式指定可审计的 Debian 镜像站；该参数同时作用于 builder 和 runtime 阶段。

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

## 2026-07-01 实机验收证据

- 镜像 ID：`sha256:4b33c39c5766c3a24496f3b8f4e559dd53f80b82755dc24ab253c9ec00682a16`。
- 镜像运行用户：`docling`；镜像大小：11,262,041,042 字节。
- 断网参数：`--network none`；GPU 参数：`--gpus all`。
- GPU 证据：NVIDIA TITAN RTX，CUDA 12.8，PyTorch 2.10.0+cu128，总显存 25,189,023,744 字节。
- 模型证据：`model_manifest.json` 登记的 5 个模型目录实际摘要全部与期望摘要一致。
- 输入 fixture：`data/sources/raw/cases/cert_eu_china_telecom_route_leak_2019.pdf`，SHA-256 为 `8a01ee709853c923ce3fb84f4c6f3fb8c3f2ede858803f3e4baff56cfe145b08`。
- 输出 fixture：Docling JSON 共 23 个文本 Block、20,467 字节，SHA-256 为 `aa96eb79141ff797516acfcf391c924ae1f200f7d46e73ac958aa879c41d8f18`。

RapidOCR 必须显式配置 `backend="torch"`。实机日志确认检测、方向分类和识别模型均使用 GPU 0；不得使用 CLI 的默认 ONNX backend，因为本锁定环境有意不引入第二套 `onnxruntime` 推理运行时。
