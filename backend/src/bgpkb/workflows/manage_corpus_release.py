#!/usr/bin/env python3
"""显式切换清洗语料版本或执行 v1 回滚。"""

import argparse
import json
from pathlib import Path

from bgpkb import paths
from bgpkb.ingestion.cleaning_v2.release import rollback_to_v1, switch_release


DEFAULT_POINTER = paths.CONFIG_DIR / "corpus_release_pointer.json"
DEFAULT_V1 = paths.PUBLISHED_DIR / "corpus_releases" / "v1" / "manifest.json"
DEFAULT_V2 = paths.PUBLISHED_DIR / "corpus_releases" / "v2" / "manifest.json"
DEFAULT_GATE = paths.DATASETS_DIR / "cleaning_v2_release_gate.json"


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="显式切换 v2 或执行经过验证的 v1 回滚")
    parser.add_argument("--target", choices=["v1", "v2"], required=True)
    parser.add_argument("--pointer", type=Path, default=DEFAULT_POINTER)
    parser.add_argument("--v1-manifest", type=Path, default=DEFAULT_V1)
    parser.add_argument("--v2-manifest", type=Path, default=DEFAULT_V2)
    parser.add_argument("--gate", type=Path, default=DEFAULT_GATE)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    if args.target == "v2":
        result = switch_release(
            args.pointer, _load(args.v2_manifest), gate_result=_load(args.gate), reason=args.reason
        )
    else:
        result = rollback_to_v1(args.pointer, _load(args.v1_manifest), reason=args.reason)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
