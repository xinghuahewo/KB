#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
DATASET_DIR = paths.DATASETS_DIR
SESSION_TEMPLATE_DIR = paths.REVIEW_INPUTS_DIR / "human_review_session_decision_templates"
DECISION_INPUT = paths.REVIEW_INPUTS_DIR / "human_review_decisions.csv"

FIELDS = [
    "entity_id",
    "review_decision",
    "reviewer",
    "reviewed_at",
    "decision_note",
]
ALLOWED_DECISIONS = {"approved", "rejected", "needs_source", "needs_semantic_review"}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def queue_by_entity():
    return {
        record.get("entity_id"): record
        for record in load_jsonl(DATASET_DIR / "human_review_session_queue.jsonl")
        if record.get("entity_id")
    }


def template_paths(args):
    paths = []
    for raw_path in args.templates:
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        paths.append(path)
    if args.session_id:
        paths.append(SESSION_TEMPLATE_DIR / f"{args.session_id}_decisions_template.csv")
    if args.all_sessions:
        paths.extend(sorted(SESSION_TEMPLATE_DIR.glob("review_session_*_decisions_template.csv")))
    seen = set()
    unique = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return unique


def read_existing_decisions():
    decisions = {}
    if not DECISION_INPUT.exists():
        return decisions
    with DECISION_INPUT.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row_number, row in enumerate(reader, start=2):
            entity_id = (row.get("entity_id") or "").strip()
            decision = (row.get("review_decision") or "").strip()
            if not entity_id or not decision or decision == "unreviewed":
                continue
            decisions[entity_id] = {
                "entity_id": entity_id,
                "review_decision": decision,
                "reviewer": (row.get("reviewer") or "").strip(),
                "reviewed_at": (row.get("reviewed_at") or "").strip(),
                "decision_note": (row.get("decision_note") or "").strip(),
                "source": "existing",
                "row_number": row_number,
            }
    return decisions


def read_template_decisions(paths, queue_entities):
    decisions = {}
    errors = []
    scanned_rows = 0
    for path in paths:
        if not path.exists():
            errors.append(f"{path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path}: 文件不存在")
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row_number, row in enumerate(reader, start=2):
                scanned_rows += 1
                entity_id = (row.get("entity_id") or "").strip()
                decision = (row.get("review_decision") or "").strip()
                if not entity_id and not decision:
                    continue
                if not entity_id:
                    errors.append(f"{path.name}:{row_number}: 缺少 entity_id")
                    continue
                if not decision or decision == "unreviewed":
                    continue
                if decision not in ALLOWED_DECISIONS:
                    errors.append(f"{path.name}:{row_number}: review_decision `{decision}` 不在允许范围内")
                    continue
                if entity_id not in queue_entities:
                    errors.append(f"{path.name}:{row_number}: entity_id `{entity_id}` 不在会话队列中")
                    continue
                row_session_id = (row.get("session_id") or "").strip()
                expected_session_id = queue_entities[entity_id].get("session_id", "")
                if row_session_id and row_session_id != expected_session_id:
                    errors.append(f"{path.name}:{row_number}: entity_id `{entity_id}` session_id 不一致")
                    continue
                new_decision = {
                    "entity_id": entity_id,
                    "review_decision": decision,
                    "reviewer": (row.get("reviewer") or "").strip(),
                    "reviewed_at": (row.get("reviewed_at") or "").strip(),
                    "decision_note": (row.get("decision_note") or "").strip(),
                    "source": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(),
                    "row_number": row_number,
                }
                existing = decisions.get(entity_id)
                if existing and any(existing[field] != new_decision[field] for field in FIELDS):
                    errors.append(f"{path.name}:{row_number}: entity_id `{entity_id}` 在模板输入中存在冲突")
                    continue
                decisions[entity_id] = new_decision
    return decisions, errors, scanned_rows


def merge_decisions(existing, incoming, replace):
    merged = dict(existing)
    conflicts = []
    added = []
    replaced = []
    unchanged = []
    for entity_id, decision in sorted(incoming.items()):
        current = existing.get(entity_id)
        if current is None:
            merged[entity_id] = decision
            added.append(entity_id)
            continue
        if all(current.get(field, "") == decision.get(field, "") for field in FIELDS):
            unchanged.append(entity_id)
            continue
        if replace:
            merged[entity_id] = decision
            replaced.append(entity_id)
        else:
            conflicts.append(entity_id)
    return merged, {
        "added": added,
        "replaced": replaced,
        "unchanged": unchanged,
        "conflicts": conflicts,
    }


def write_decisions(decisions):
    DECISION_INPUT.parent.mkdir(parents=True, exist_ok=True)
    with DECISION_INPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for entity_id in sorted(decisions):
            row = decisions[entity_id]
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def print_summary(paths, scanned_rows, incoming, merge_result, errors, write_enabled, replace):
    payload = {
        "templates": [path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix() for path in paths],
        "scanned_rows": scanned_rows,
        "incoming_decisions": len(incoming),
        "added": len(merge_result["added"]),
        "replaced": len(merge_result["replaced"]),
        "unchanged": len(merge_result["unchanged"]),
        "conflicts": len(merge_result["conflicts"]),
        "errors": len(errors),
        "write_enabled": write_enabled,
        "replace_enabled": replace,
        "decision_input": DECISION_INPUT.relative_to(ROOT).as_posix(),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        print("\n错误：")
        for error in errors:
            print(f"- {error}")
    if merge_result["conflicts"]:
        print("\n冲突：")
        for entity_id in merge_result["conflicts"]:
            print(f"- {entity_id}")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description="将逐 session 决策模板中的非空人工决策显式合并到主人工决策 CSV。默认 dry-run，不写文件。"
    )
    parser.add_argument("templates", nargs="*", help="一个或多个 session 决策模板 CSV 路径。")
    parser.add_argument("--session-id", help="导入指定 session 的模板，例如 review_session_001。")
    parser.add_argument("--all-sessions", action="store_true", help="扫描所有 session 模板。")
    parser.add_argument("--write", action="store_true", help="实际写入 data/review_inputs/human_review_decisions.csv。")
    parser.add_argument("--replace", action="store_true", help="允许覆盖主决策 CSV 中同一 entity_id 的不同决策。")
    return parser


def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    paths = template_paths(args)
    if not paths:
        parser.error("需要提供模板路径、--session-id 或 --all-sessions。")
    queue_entities = queue_by_entity()
    existing = read_existing_decisions()
    incoming, errors, scanned_rows = read_template_decisions(paths, queue_entities)
    merged, merge_result = merge_decisions(existing, incoming, args.replace)
    if merge_result["conflicts"]:
        errors.append("存在主决策 CSV 冲突；如确认要覆盖，请显式传入 --replace。")
    if args.write and not errors:
        write_decisions(merged)
    print_summary(paths, scanned_rows, incoming, merge_result, errors, args.write and not errors, args.replace)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
