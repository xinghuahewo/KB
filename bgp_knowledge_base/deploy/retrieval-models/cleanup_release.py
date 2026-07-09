#!/usr/bin/env python3
"""显式、安全地删除非 live 的检索模型 release。"""

import argparse
import os
from pathlib import Path
import re
import shutil


RELEASE_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def cleanup_release(
    release_id,
    releases_root=Path("/srv/bgpkb/retrieval-releases"),
    live_app=Path("/srv/bgpkb/retrieval-models"),
    live_models=Path("/srv/bgpkb/retrieval-models-models"),
):
    if not RELEASE_PATTERN.fullmatch(release_id or ""):
        return 2
    root = Path(releases_root).resolve()
    lexical_candidate = root / release_id
    if not os.path.lexists(lexical_candidate):
        return 2
    candidate = lexical_candidate.resolve()
    if candidate.parent != root or candidate != lexical_candidate:
        return 2
    live_targets = []
    for link in (live_app, live_models):
        if os.path.lexists(link):
            live_targets.append(Path(link).resolve())
    if any(candidate == target or candidate in target.parents for target in live_targets):
        return 2
    shutil.rmtree(candidate)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-id", required=True)
    args = parser.parse_args()
    raise SystemExit(cleanup_release(args.release_id))


if __name__ == "__main__":
    main()
