import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "deploy/retrieval-models/select_gpu_devices.py"


def load_module():
    spec = importlib.util.spec_from_file_location("gpu_selector", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selector_swaps_roles_to_satisfy_asymmetric_thresholds():
    module = load_module()
    gpus = [
        {"index": 0, "total_mib": 11000, "used_mib": 0},
        {"index": 1, "total_mib": 11000, "used_mib": 0},
        {"index": 2, "total_mib": 11000, "used_mib": 2000},
        {"index": 3, "total_mib": 11000, "used_mib": 4000},
    ]
    policy = {
        "allowed_indices": [2, 3],
        "embedding": {"min_free_mib": 6000},
        "reranker": {"min_free_mib": 8000},
    }

    assert module.select_devices(gpus, policy) == {"embedding": 3, "reranker": 2}


def test_selector_uses_documented_ordering_and_never_uses_zero_or_one():
    module = load_module()
    gpus = [
        {"index": 0, "total_mib": 20000, "used_mib": 0},
        {"index": 1, "total_mib": 20000, "used_mib": 0},
        {"index": 2, "total_mib": 10000, "used_mib": 1000},
        {"index": 3, "total_mib": 10000, "used_mib": 1000},
    ]
    policy = {
        "allowed_indices": [2, 3],
        "embedding": {"min_free_mib": 8192},
        "reranker": {"min_free_mib": 8192},
    }

    assert module.select_devices(gpus, policy) == {"embedding": 2, "reranker": 3}


def test_success_writes_exact_four_lines_atomically(tmp_path):
    module = load_module()
    env_path = tmp_path / ".env"
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps({
        "allowed_indices": [2, 3],
        "embedding": {"min_free_mib": 8192},
        "reranker": {"min_free_mib": 8192},
    }))

    code = module.run(
        policy_path,
        env_path,
        command_runner=lambda command: "2, 11264, 1000\n3, 11264, 1000\n",
    )

    assert code == 0
    assert env_path.read_bytes() == (
        b"EMBEDDING_GPU_CDI=nvidia.com/gpu=2\n"
        b"RERANKER_GPU_CDI=nvidia.com/gpu=3\n"
        b"EMBEDDING_GPU_INDEX=2\n"
        b"RERANKER_GPU_INDEX=3\n"
    )


def test_failure_keeps_old_env_and_reports_every_candidate(tmp_path, capsys):
    module = load_module()
    env_path = tmp_path / ".env"
    old = b"DO_NOT_CHANGE\n"
    env_path.write_bytes(old)
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps({
        "allowed_indices": [2, 3],
        "embedding": {"min_free_mib": 8192},
        "reranker": {"min_free_mib": 8192},
    }))

    code = module.run(
        policy_path,
        env_path,
        command_runner=lambda command: "2, 11264, 5000\n3, 11264, 6000\n",
    )

    assert code == 2
    assert env_path.read_bytes() == old
    error = capsys.readouterr().err
    for value in ("2", "3", "11264", "5000", "6000", "8192", "free_mib"):
        assert value in error
    assert list(tmp_path.glob(".env.*")) == []


def test_nvidia_smi_failure_returns_two_and_keeps_old_env(tmp_path, capsys):
    module = load_module()
    env_path = tmp_path / ".env"
    env_path.write_bytes(b"OLD\n")
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps({
        "allowed_indices": [2, 3],
        "embedding": {"min_free_mib": 8192},
        "reranker": {"min_free_mib": 8192},
    }))

    code = module.run(
        policy_path, env_path,
        command_runner=lambda command: (_ for _ in ()).throw(RuntimeError("nvidia-smi failed")),
    )

    assert code == 2
    assert env_path.read_bytes() == b"OLD\n"
    assert "nvidia-smi" in capsys.readouterr().err
