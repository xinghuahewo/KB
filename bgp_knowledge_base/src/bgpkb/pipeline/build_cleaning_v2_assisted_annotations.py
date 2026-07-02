#!/usr/bin/env python3
"""为高风险验收集生成可人工抽查的 Codex 辅助标注。"""

import argparse
import json
from pathlib import Path

from bgpkb import paths
from bgpkb.cleaning_v2.contracts import atomic_write_json
from bgpkb.cleaning_v2.evaluation import build_assisted_annotation, load_annotations


DEFAULT_ANNOTATIONS = paths.REVIEW_INPUTS_DIR / "cleaning_v2_gold_annotations.json"
DEFAULT_PARSED_ROOT = paths.CORPUS_DIR / "parsed_v2"


def build_annotations(annotation_path=DEFAULT_ANNOTATIONS, parsed_root=DEFAULT_PARSED_ROOT):
    rows = load_annotations(annotation_path)
    result = []
    for row in rows:
        if row.get("verification_status") == "human_verified":
            result.append(row)
            continue
        parsed_path = Path(parsed_root) / f"{row['doc_id']}.json"
        document = json.loads(parsed_path.read_text(encoding="utf-8"))
        result.append(build_assisted_annotation(row, document))
    atomic_write_json(annotation_path, result, indent=2)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成清洗 v2 高风险集辅助标注")
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--parsed-root", type=Path, default=DEFAULT_PARSED_ROOT)
    args = parser.parse_args(argv)
    rows = build_annotations(args.annotations, args.parsed_root)
    print(
        f"标注记录 {len(rows)} 条；人工确认 {sum(row.get('verification_status') == 'human_verified' for row in rows)} 条；"
        f"Codex 辅助 {sum(row.get('annotation_method') == 'codex_assisted' for row in rows)} 条"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
