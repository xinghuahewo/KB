#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
ENTITY_DIR = paths.ENTITIES_DIR
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("human_review_decision_apply_report")
JSONL_OUTPUT = DATASET_DIR / "human_review_decision_apply_preview.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_decision_apply_preview.csv"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_preview_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_preview_csv(records):
    fields = [
        "preview_id",
        "record_type",
        "run_mode",
        "entity_id",
        "entity_file",
        "from_status",
        "to_status",
        "application_status",
        "can_apply",
        "needs_llm",
        "count",
        "message",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def applicable_decisions():
    decisions = {}
    skipped = Counter()
    for record in load_jsonl(DATASET_DIR / "human_review_decision_audit.jsonl"):
        entity_id = record.get("entity_id")
        target = record.get("target_review_status")
        if (
            entity_id
            and record.get("can_apply") is True
            and record.get("needs_llm") is not True
            and record.get("application_status") == "ready_to_apply"
            and target in {"approved", "rejected"}
        ):
            decisions[entity_id] = record
        else:
            skipped[record.get("application_status", "unknown")] += 1
    return decisions, skipped


def apply_decisions(decisions, write=False):
    updated = []
    unchanged = []
    missing = set(decisions)
    by_file = defaultdict(int)
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        records = load_jsonl(path)
        changed = False
        for record in records:
            entity_id = record.get("id")
            decision = decisions.get(entity_id)
            if not decision:
                continue
            missing.discard(entity_id)
            target = decision["target_review_status"]
            current = record.get("review_status", "")
            if current == target:
                unchanged.append(entity_id)
                continue
            updated.append({
                "entity_id": entity_id,
                "entity_file": path.relative_to(ROOT).as_posix(),
                "from": current,
                "to": target,
            })
            by_file[path.relative_to(ROOT).as_posix()] += 1
            if write:
                record["review_status"] = target
                changed = True
        if write and changed:
            write_jsonl(path, records)
    return updated, unchanged, sorted(missing), by_file


def write_report(decision_count, skipped, updated, unchanged, missing, by_file, write=False):
    lines = [
        "# 人工复核决策应用报告",
        "",
        "## 范围",
        "",
        "本脚本只处理 `data/derived/datasets/human_review_decision_audit.jsonl` 中已审计为 `ready_to_apply`、`can_apply=true` 且不需要 LLM 的 `approved/rejected` 决策。",
        "",
        "默认模式为 dry-run；只有传入 `--write` 才会修改 `data/knowledge/entities/*.jsonl`。",
        "",
        "## 摘要",
        "",
        f"- 运行模式：{'write' if write else 'dry-run'}",
        f"- 可应用决策数：{decision_count}",
        f"- {'实际更新' if write else '将更新'}实体数：{len(updated)}",
        f"- 已是目标状态的实体数：{len(unchanged)}",
        f"- 未找到实体数：{len(missing)}",
        f"- JSONL 输出：`data/derived/datasets/human_review_decision_apply_preview.jsonl`",
        f"- CSV 输出：`data/derived/datasets/human_review_decision_apply_preview.csv`",
        "",
        "## 按文件更新数",
        "",
    ]
    if by_file:
        for path, count in sorted(by_file.items()):
            lines.append(f"- `{path}`：{count}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 跳过的审计状态", ""])
    if skipped:
        for status, count in sorted(skipped.items()):
            lines.append(f"- {status}：{count}")
    else:
        lines.append("- 无")
    lines.extend(["", "## 本次更新预览", ""])
    if updated:
        for item in updated:
            lines.append(f"- `{item['entity_id']}`：{item['from']} -> {item['to']}（{item['entity_file']}）")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未应用 `needs_semantic_review`，因为该状态需要语义流程或 LLM。",
        "- 未应用 `needs_source` 或 `unreviewed`。",
        "- 本脚本不会下载来源，也不会判断证据是否充分。",
        "- 未传入 `--write` 时，不修改任何实体文件。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_preview_records(decision_count, skipped, updated, unchanged, missing, write=False):
    run_mode = "write" if write else "dry_run"
    records = [
        {
            "preview_id": "apply_preview_summary",
            "record_type": "summary",
            "run_mode": run_mode,
            "entity_id": "",
            "entity_file": "",
            "from_status": "",
            "to_status": "",
            "application_status": "summary",
            "can_apply": False,
            "needs_llm": False,
            "count": decision_count,
            "message": f"可应用决策数：{decision_count}；{'实际更新' if write else '将更新'}实体数：{len(updated)}。",
            "generated_by": "src/bgpkb/pipeline/apply_human_review_decisions.py",
        }
    ]
    for status, count in sorted(skipped.items()):
        records.append({
            "preview_id": f"apply_preview_skipped_{status}",
            "record_type": "skipped_status",
            "run_mode": run_mode,
            "entity_id": "",
            "entity_file": "",
            "from_status": "",
            "to_status": "",
            "application_status": status,
            "can_apply": False,
            "needs_llm": status == "blocked_by_llm",
            "count": count,
            "message": f"审计状态 `{status}` 未被应用。",
            "generated_by": "src/bgpkb/pipeline/apply_human_review_decisions.py",
        })
    for index, item in enumerate(updated, start=1):
        records.append({
            "preview_id": f"apply_preview_candidate_{index:05d}",
            "record_type": "update_candidate" if not write else "updated_entity",
            "run_mode": run_mode,
            "entity_id": item["entity_id"],
            "entity_file": item["entity_file"],
            "from_status": item["from"],
            "to_status": item["to"],
            "application_status": "ready_to_apply",
            "can_apply": True,
            "needs_llm": False,
            "count": 1,
            "message": f"{'已更新' if write else '将更新'} {item['entity_id']}：{item['from']} -> {item['to']}。",
            "generated_by": "src/bgpkb/pipeline/apply_human_review_decisions.py",
        })
    for index, entity_id in enumerate(unchanged, start=1):
        records.append({
            "preview_id": f"apply_preview_unchanged_{index:05d}",
            "record_type": "unchanged_entity",
            "run_mode": run_mode,
            "entity_id": entity_id,
            "entity_file": "",
            "from_status": "",
            "to_status": "",
            "application_status": "ready_to_apply",
            "can_apply": True,
            "needs_llm": False,
            "count": 1,
            "message": f"{entity_id} 已是目标状态。",
            "generated_by": "src/bgpkb/pipeline/apply_human_review_decisions.py",
        })
    for index, entity_id in enumerate(missing, start=1):
        records.append({
            "preview_id": f"apply_preview_missing_{index:05d}",
            "record_type": "missing_entity",
            "run_mode": run_mode,
            "entity_id": entity_id,
            "entity_file": "",
            "from_status": "",
            "to_status": "",
            "application_status": "ready_to_apply",
            "can_apply": True,
            "needs_llm": False,
            "count": 1,
            "message": f"{entity_id} 在 data/knowledge/entities/*.jsonl 中未找到。",
            "generated_by": "src/bgpkb/pipeline/apply_human_review_decisions.py",
        })
    return records


def main():
    parser = argparse.ArgumentParser(description="Apply audited human review decisions.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Actually modify data/knowledge/entities/*.jsonl. Without this flag the script only writes a dry-run report.",
    )
    args = parser.parse_args()
    decisions, skipped = applicable_decisions()
    updated, unchanged, missing, by_file = apply_decisions(decisions, write=args.write)
    preview_records = build_preview_records(len(decisions), skipped, updated, unchanged, missing, write=args.write)
    write_preview_jsonl(preview_records)
    write_preview_csv(preview_records)
    write_report(len(decisions), skipped, updated, unchanged, missing, by_file, write=args.write)
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    if args.write:
        print(f"Updated entities: {len(updated)}")
    else:
        print(f"Dry-run update candidates: {len(updated)}")


if __name__ == "__main__":
    main()
