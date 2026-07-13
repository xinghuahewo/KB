#!/usr/bin/env python3
"""根据实时显存与项目策略选择两个不同的 GPU。"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


NVIDIA_SMI_COMMAND = [
    "nvidia-smi",
    "--query-gpu=index,memory.total,memory.used",
    "--format=csv,noheader,nounits",
]


def parse_gpus(output):
    result = []
    for line in output.splitlines():
        index, total, used = (int(part.strip()) for part in line.split(","))
        result.append({"index": index, "total_mib": total, "used_mib": used})
    return result


def select_devices(gpus, policy):
    by_index = {gpu["index"]: {**gpu, "free_mib": gpu["total_mib"] - gpu["used_mib"]} for gpu in gpus}
    embedding_min = policy["embedding"]["min_free_mib"]
    reranker_min = policy["reranker"]["min_free_mib"]
    pairs = []
    for embedding in policy["allowed_indices"]:
        for reranker in policy["allowed_indices"]:
            if embedding == reranker or embedding not in by_index or reranker not in by_index:
                continue
            embedding_headroom = by_index[embedding]["free_mib"] - embedding_min
            reranker_headroom = by_index[reranker]["free_mib"] - reranker_min
            if embedding_headroom < 0 or reranker_headroom < 0:
                continue
            pairs.append((
                min(embedding_headroom, reranker_headroom),
                embedding_headroom + reranker_headroom,
                -embedding,
                -reranker,
                embedding,
                reranker,
            ))
    if not pairs:
        return None
    best = max(pairs)
    return {"embedding": best[4], "reranker": best[5]}


def run(policy_path, env_path, command_runner=None):
    policy_path = Path(policy_path)
    env_path = Path(env_path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    runner = command_runner or (lambda command: subprocess.check_output(command, text=True))
    try:
        gpus = parse_gpus(runner(NVIDIA_SMI_COMMAND))
    except Exception as exc:
        print(json.dumps({
            "错误": f"nvidia-smi 实时检查失败: {exc}",
            "allowed_indices": policy["allowed_indices"],
            "embedding_min_free_mib": policy["embedding"]["min_free_mib"],
            "reranker_min_free_mib": policy["reranker"]["min_free_mib"],
        }, ensure_ascii=False), file=sys.stderr)
        return 2
    selection = select_devices(gpus, policy)
    if selection is None:
        candidates = []
        for gpu in gpus:
            if gpu["index"] in policy["allowed_indices"]:
                candidates.append({**gpu, "free_mib": gpu["total_mib"] - gpu["used_mib"]})
        print(json.dumps({
            "错误": "没有满足不同设备与显存阈值的 GPU 配对",
            "候选": candidates,
            "embedding_min_free_mib": policy["embedding"]["min_free_mib"],
            "reranker_min_free_mib": policy["reranker"]["min_free_mib"],
        }, ensure_ascii=False), file=sys.stderr)
        return 2
    content = (
        f"EMBEDDING_GPU_CDI=nvidia.com/gpu={selection['embedding']}\n"
        f"RERANKER_GPU_CDI=nvidia.com/gpu={selection['reranker']}\n"
        f"EMBEDDING_GPU_INDEX={selection['embedding']}\n"
        f"RERANKER_GPU_INDEX={selection['reranker']}\n"
    )
    env_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=env_path.parent, prefix=f"{env_path.name}.", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, env_path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", type=Path, default=Path(__file__).with_name("gpu_policy.json"))
    parser.add_argument("--output", "--env", dest="output", type=Path, default=Path(__file__).with_name(".env"))
    args = parser.parse_args()
    raise SystemExit(run(args.policy, args.output))


if __name__ == "__main__":
    main()
