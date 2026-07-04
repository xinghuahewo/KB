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
    for expected in ("GPU 2", "GPU 3", ".env", "原子", "两张", "不同"):
        assert expected in task_4
    assert "GPU 0" in task_4 and "GPU 1" in task_4
    assert "不足两张" in task_4 and "API" in task_4
    assert "两个独立 CDI 设备变量" in task_4
    assert "EMBEDDING_GPU_DEVICE" in task_4
    assert "RERANKER_GPU_DEVICE" in task_4

    task_10 = plan.split("### 任务 10：", 1)[1]
    assert task_10.index("nvidia-smi") < task_10.index("select_gpu_devices.py")
    assert task_10.index("select_gpu_devices.py") < task_10.index("docker compose up -d --pull never")
    assert "只从 GPU 2、GPU 3" in task_10
    assert "不得自动使用 GPU 0 或 GPU 1" in task_10
    assert "已空闲" not in task_10
