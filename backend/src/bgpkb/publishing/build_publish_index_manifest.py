"""构建并验证 publish-index 候选闭包 manifest。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from bgpkb import paths
from bgpkb.publishing.publish_index_closure import (
    PublishIndexClosureError,
    verify_publish_index_manifest,
    write_publish_index_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="构建 publish-index 完整制品闭包")
    parser.add_argument("--data-dir", type=Path, default=paths.DATA_DIR)
    parser.add_argument("--release-id", default=os.environ.get("BGPKB_RELEASE_ID", ""))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    release_id = args.release_id or args.data_dir.resolve().parent.name
    try:
        manifest = write_publish_index_manifest(
            args.data_dir,
            release_id=release_id,
        )
        result = verify_publish_index_manifest(args.data_dir, manifest)
    except PublishIndexClosureError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
