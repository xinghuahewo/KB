from pathlib import Path

from bgpkb import paths


DESIGN = (
    paths.PROJECT_ROOT
    / "docs/superpowers/specs/2026-07-02-stage-b-hierarchical-retrieval-design.md"
)
PLAN = (
    paths.PROJECT_ROOT
    / "docs/superpowers/plans/2026-07-02-stage-b-hierarchical-retrieval-implementation.md"
)
CONFIG = paths.CONFIG_DIR / "rag_retrieval.yaml"
AGENTS = paths.PROJECT_ROOT.parent / "AGENTS.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_current_server_routing_documents_do_not_retain_retired_server_assumptions():
    current_routing_documents = (CONFIG, DESIGN, PLAN)
    retired_markers = (
        "10.109.242.145",
        "10.29.98.116",
        "nic@",
        "TITAN RTX",
        "--gpus all",
        "/home/nic",
    )

    for path in current_routing_documents:
        content = read(path)
        for marker in retired_markers:
            assert marker not in content, f"{path} 仍包含旧路由标记：{marker}"

    agents = read(AGENTS)
    for expected in (
        "root@10.99.8.28",
        "/srv/bgpkb",
        "nvidia.com/gpu=1",
        "GPU 2",
        "GPU 3",
        "nvidia-smi",
    ):
        assert expected in agents


def test_stage_b_design_documents_new_server_and_gpu_safety_boundaries():
    design = read(DESIGN)

    for expected in (
        "root@10.99.8.28",
        "4 × NVIDIA GeForce RTX 2080 Ti",
        "11264 MiB",
        "/srv/bgpkb/retrieval-models",
        "/srv/bgpkb/retrieval-models-models",
        "nvidia.com/gpu=",
        "GPU 2",
        "GPU 3",
        "运行前",
        "GPU 0",
        "GPU 1",
        "API",
    ):
        assert expected in design
    assert "两个独立 Docker 容器" in design
    assert "单张 GPU" in design


def test_stage_b_plan_requires_selector_generated_distinct_cdi_devices():
    plan = read(PLAN)

    for expected in (
        "root@10.99.8.28",
        "http://10.99.8.28:8011/v1/embeddings",
        "http://10.99.8.28:8012/v1/rerank",
        "/srv/bgpkb/retrieval-models",
        "/srv/bgpkb/retrieval-models-models",
        "deploy/retrieval-models/select_gpu_devices.py",
        "nvidia-smi",
        "nvidia.com/gpu=",
        "docker compose up -d --pull never",
        "linux/amd64",
    ):
        assert expected in plan

    task_4 = plan.split("### 任务 4：", 1)[1].split("### 任务 5：", 1)[0]
    for expected in (
        "deploy/retrieval-models/gpu_policy.json",
        '"allowed_indices": [2, 3]',
        '"embedding_min_free_mib": 8192',
        '"reranker_min_free_mib": 8192',
        "nvidia-smi --query-gpu=index,memory.total,memory.used --format=csv,noheader,nounits",
        "free = total - used",
        "free 降序、index 升序",
        "Embedding 先取第一张",
        "Reranker 再取第二张",
        "--policy gpu_policy.json --output .env",
        "exit 0",
        "exit 2",
        "旧 `.env` 字节不变",
        "EMBEDDING_GPU_CDI=nvidia.com/gpu=<i>",
        "RERANKER_GPU_CDI=nvidia.com/gpu=<i>",
        "EMBEDDING_GPU_INDEX=<i>",
        "RERANKER_GPU_INDEX=<i>",
    ):
        assert expected in task_4
    for expected in ("排序", "阈值", "不同 GPU", "失败不覆盖旧 `.env`", "精确四行"):
        assert expected in task_4
    assert "GPU 0" in task_4 and "GPU 1" in task_4
    assert "候选卡的 total、used、free、角色阈值和失败原因" in task_4
    assert "Compose 使用 `EMBEDDING_GPU_CDI` 与 `RERANKER_GPU_CDI`" in task_4
    assert "deploy/retrieval-models/deploy_release.py" in task_4
    assert "失败前不得触碰 live link" in task_4
    assert "Compose 失败" in task_4 and "恢复旧 link" in task_4

    task_10 = plan.split("### 任务 10：", 1)[1]
    for expected in (
        "set -euo pipefail",
        'RELEASE_ID="$(shasum -a 256 deploy/retrieval-models/model_manifest.lock.json',
        'REMOTE_STAGE="/srv/bgpkb/retrieval-releases/.incoming-$RELEASE_ID"',
        'REMOTE_RELEASE="/srv/bgpkb/retrieval-releases/$RELEASE_ID"',
        "'$REMOTE_STAGE/app' '$REMOTE_STAGE/models'",
        "'$REMOTE_RELEASE/app'",
        "$REMOTE_RELEASE/models",
        "--policy gpu_policy.json --output .env",
        "deploy_release.py",
        "docker compose up -d --pull never",
        "旧 release 清理",
        "独立显式命令",
    ):
        assert expected in task_10
    deployment_step = task_10.split("**步骤 4：", 1)[1].split("**步骤 5：", 1)[0]
    assert deployment_step.index("nvidia-smi") < deployment_step.index("select_gpu_devices.py")
    assert deployment_step.index("select_gpu_devices.py") < deployment_step.index("deploy_release.py")
    assert "rsync --delete" not in task_10
    assert "临时目录" in task_10 and "rename" in task_10
    assert "manifest/hash/GPU prestart" in task_10
