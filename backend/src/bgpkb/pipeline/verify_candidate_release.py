"""verify-release 最终统一门禁 CLI。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from bgpkb import paths
from bgpkb.workflows.release_verification import verify_candidate_release


def _models_from_environment() -> dict[str, dict[str, str]]:
    return {
        "embedding": {
            "model": os.environ.get("BGP_EMBEDDING_MODEL", "BAAI/bge-m3"),
            "revision": os.environ.get("BGP_EMBEDDING_MODEL_REVISION", ""),
        },
        "reranker": {
            "model": os.environ.get("BGP_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"),
            "revision": os.environ.get("BGP_RERANKER_MODEL_REVISION", ""),
        },
        "llm": {
            "model": os.environ.get("BGP_LLM_MODEL", "deepseek-chat"),
            "revision": os.environ.get("BGP_LLM_MODEL_REVISION", ""),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="执行候选 release 统一发布门禁")
    parser.add_argument("--data-dir", type=Path, default=paths.DATA_DIR)
    parser.add_argument("--code-commit", default=os.environ.get("BGPKB_CODE_COMMIT", ""))
    parser.add_argument(
        "--prompt-version",
        default=os.environ.get("BGP_GROUNDED_PROMPT_VERSION", ""),
    )
    parser.add_argument("--ownership", type=Path, default=paths.CONFIG_DIR / "rag_eval_ownership.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_candidate_release(
        data_dir=args.data_dir,
        expected_code_commit=args.code_commit,
        expected_models=_models_from_environment(),
        expected_prompt_version=args.prompt_version,
        ownership_path=args.ownership,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
