#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service import hybrid_retrieval  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="查询 BGP KB 混合检索框架。")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("search", "context-pack"):
        command = subparsers.add_parser(name)
        command.add_argument("query")
        command.add_argument("--top-k", type=int, default=8 if name == "context-pack" else 20)
        command.add_argument("--no-vector", action="store_true")
        command.add_argument("--json", action="store_true", help="保留兼容参数；输出始终为 JSON。")
    args = parser.parse_args()

    if args.command == "search":
        payload = hybrid_retrieval.search(
            args.query,
            limit=args.top_k,
            vector_enabled=not args.no_vector,
        )
    else:
        payload = hybrid_retrieval.context_pack(
            args.query,
            limit=args.top_k,
            vector_enabled=not args.no_vector,
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
