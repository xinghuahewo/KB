#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.service import retrieval_framework


def search(query, limit=10):
    return retrieval_framework.search(query, limit=limit)


def context_pack(query, limit=8):
    return retrieval_framework.context_pack(query, limit=limit)


def main():
    parser = argparse.ArgumentParser(description="Query the offline RAG retrieval framework.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=10)
    pack_parser = subparsers.add_parser("context-pack")
    pack_parser.add_argument("query")
    pack_parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    if args.command == "search":
        payload = search(args.query, limit=args.limit)
    else:
        payload = context_pack(args.query, limit=args.limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
