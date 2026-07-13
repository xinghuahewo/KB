#!/usr/bin/env python3
import csv
import json
from collections import Counter
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
ENTITY_DIR = paths.ENTITIES_DIR
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("human_review_field_checklist_report")
JSONL_OUTPUT = DATASET_DIR / "human_review_field_checklist.jsonl"
CSV_OUTPUT = DATASET_DIR / "human_review_field_checklist.csv"

DECISION_INPUT_PATH = "data/review_inputs/human_review_decisions.csv"
GENERATED_BY = "src/bgpkb/pipeline/build_human_review_field_checklist.py"
SKIPPED_FIELDS = {"id", "entity_type", "review_status"}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entities_by_id():
    entities = {}
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        for record in load_jsonl(path):
            entity_id = record.get("id")
            if entity_id:
                entities[entity_id] = {
                    "record": record,
                    "entity_file": path.relative_to(ROOT).as_posix(),
                }
    return entities


def display_name_for(entity):
    for field in ("name", "paper", "applies_to", "id"):
        value = entity.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return entity.get("id", "")


def stable_field_token(field_name):
    chars = []
    for char in field_name.lower():
        if char.isalnum():
            chars.append(char)
        else:
            chars.append("_")
    return "".join(chars).strip("_") or "field"


def value_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def value_preview(value):
    text = value_json(value)
    if len(text) <= 240:
        return text
    return text[:237] + "..."


def prompt_for(field_name):
    if field_name == "source_refs":
        return "核对 source_refs 是否都是当前实体字段的直接或必要来源；缺少直接证据时保持 pending 或标记 needs_source。"
    if field_name in {"limitations", "possible_false_positives", "checks"}:
        return "核对该限制或误报边界是否被来源直接支持；需要归纳判断时标记 needs_semantic_review。"
    if field_name in {"definition", "description", "meaning", "problem", "process", "output"}:
        return "核对该文字字段是否能在来源或摘录中找到直接支撑；不能直接确认时不要批准。"
    return "核对该字段值是否被来源路径和摘录直接支持；需要解释或归纳时记录为 needs_semantic_review。"


def build_records():
    entities = load_entities_by_id()
    queue_records = load_jsonl(DATASET_DIR / "human_review_session_queue.jsonl")
    queue_records.sort(key=lambda item: (item.get("global_review_order", 999999), item.get("entity_id", "")))
    records = []
    for queue in queue_records:
        entity_id = queue.get("entity_id", "")
        entity_info = entities.get(entity_id, {})
        entity = entity_info.get("record", {})
        field_names = [field for field in sorted(entity) if field not in SKIPPED_FIELDS]
        for index, field_name in enumerate(field_names, start=1):
            value = entity.get(field_name)
            records.append({
                "field_check_id": f"field_check_{entity_id}_{index:03d}_{stable_field_token(field_name)}",
                "session_id": queue.get("session_id", ""),
                "session_order": queue.get("session_order", 0),
                "within_session_order": queue.get("within_session_order", 0),
                "global_review_order": queue.get("global_review_order", 0),
                "field_order": index,
                "entity_id": entity_id,
                "entity_type": queue.get("entity_type", ""),
                "display_name": queue.get("display_name") or display_name_for(entity),
                "entity_file": entity_info.get("entity_file", ""),
                "field_name": field_name,
                "field_value_json": value_json(value),
                "field_value_preview": value_preview(value),
                "verification_prompt": prompt_for(field_name),
                "decision_input_path": DECISION_INPUT_PATH,
                "review_decision": "unreviewed",
                "needs_llm": False,
                "generated_by": GENERATED_BY,
            })
    return records


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "field_check_id",
        "session_id",
        "session_order",
        "within_session_order",
        "global_review_order",
        "field_order",
        "entity_id",
        "entity_type",
        "display_name",
        "entity_file",
        "field_name",
        "field_value_json",
        "field_value_preview",
        "verification_prompt",
        "decision_input_path",
        "review_decision",
        "needs_llm",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_report(records):
    by_type = Counter(record["entity_type"] for record in records)
    by_field = Counter(record["field_name"] for record in records)
    by_session = Counter(record["session_id"] for record in records)
    entity_count = len({record["entity_id"] for record in records})
    lines = [
        "# 人工复核逐字段清单报告",
        "",
        "## 范围",
        "",
        "本报告把待人工复核实体的结构化字段机械展开为逐字段核验清单。它只展示字段和值，不判断字段是否被来源支持，不调用 LLM，也不修改实体状态。",
        "",
        "## 摘要",
        "",
        f"- 字段核验项数：{len(records)}",
        f"- 覆盖实体数：{entity_count}",
        f"- JSONL 输出：`data/derived/datasets/human_review_field_checklist.jsonl`",
        f"- CSV 输出：`data/derived/datasets/human_review_field_checklist.csv`",
        f"- 人工决策输入：`{DECISION_INPUT_PATH}`",
        "",
        "## 按实体类型统计",
        "",
    ]
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend(["", "## 高频字段", ""])
    for field_name, count in by_field.most_common(20):
        lines.append(f"- {field_name}：{count}")
    lines.extend(["", "## 按 session 统计", ""])
    for session_id, count in sorted(by_session.items()):
        lines.append(f"- {session_id}：{count}")
    lines.extend([
        "",
        "## 前 20 个核验项",
        "",
        "| Session | 实体 | 字段 | 值预览 | 提示 |",
        "| --- | --- | --- | --- | --- |",
    ])
    for record in records[:20]:
        preview = record["field_value_preview"].replace("|", "\\|")
        prompt = record["verification_prompt"].replace("|", "\\|")
        lines.append(
            f"| `{record['session_id']}` | `{record['entity_id']}` | `{record['field_name']}` | {preview} | {prompt} |"
        )
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未判断字段是否被来源充分支持。",
        "- 未自动批准、拒绝或改写实体。",
        "- 需要解释、归纳或证据强度判断时，仍按规则记录为 `needs_semantic_review` 或保持 `unreviewed`。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = build_records()
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
