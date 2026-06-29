#!/usr/bin/env python3
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
ENTITY_DIR = paths.ENTITIES_DIR
DATASET_DIR = paths.DATASETS_DIR
REPORT = paths.report_path("entity_review_packet_report")
JSONL_OUTPUT = DATASET_DIR / "entity_review_packets.jsonl"
CSV_OUTPUT = DATASET_DIR / "entity_review_packets.csv"

ENTITY_TYPE_ORDER = {
    "BGPConcept": 1,
    "RoutingMechanism": 2,
    "DataField": 3,
    "DataSource": 4,
    "AnomalyType": 5,
    "EvidenceTemplate": 6,
    "FalsePositivePattern": 7,
    "Case": 8,
    "PaperMethod": 9,
}


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def load_entities():
    records = []
    for path in sorted(ENTITY_DIR.glob("*.jsonl")):
        records.extend(load_jsonl(path))
    return records


def display_name_for(entity):
    for field in ("name", "paper", "applies_to", "id"):
        value = entity.get(field)
        if isinstance(value, str) and value.strip():
            return value
    return entity.get("id", "")


def review_bucket_for(non_manual_source_count, manual_note_source_count):
    if non_manual_source_count == 0:
        return "context_only_needs_authoritative_source"
    if manual_note_source_count == 0:
        return "ready_without_manual_note"
    return "ready_with_manual_note"


def suggested_action_for(bucket):
    if bucket == "context_only_needs_authoritative_source":
        return "仅有 context_2026 或 manual_note 来源，人工复核前应补充权威来源或保持 pending。"
    if bucket == "ready_without_manual_note":
        return "优先人工核验 data/corpus/cleaned/parsed/chunk 证据，确认后再决定 approved/rejected。"
    return "人工核验非 manual_note 来源；context_2026 只作为范围提示，不作为单独批准依据。"


def checklist_for(bucket):
    checklist = [
        "打开 cleaned_path 或 parsed_path，核对实体定义和关键字段是否被来源直接支持。",
        "检查 chunk_sample_ids 是否覆盖定义、适用范围、限制或误报边界。",
        "确认 source_refs 中每个来源是否仍应保留，缺少直接证据时保持 pending。",
    ]
    if bucket == "context_only_needs_authoritative_source":
        checklist.append("该实体缺少非 manual_note 来源，优先补充权威资料后再复核。")
    else:
        checklist.append("人工确认通过后，再把实体 review_status 从 pending 改为 approved。")
    return checklist


def load_evidence_by_entity():
    evidence_by_entity = defaultdict(list)
    for record in load_jsonl(DATASET_DIR / "entity_source_evidence.jsonl"):
        entity_id = record.get("entity_id")
        if entity_id:
            evidence_by_entity[entity_id].append(record)
    return evidence_by_entity


def unique_sorted(values):
    return sorted({value for value in values if value})


def build_packets():
    evidence_by_entity = load_evidence_by_entity()
    packets = []
    for entity in load_entities():
        entity_id = entity.get("id", "")
        evidence_records = evidence_by_entity.get(entity_id, [])
        non_manual_source_count = sum(
            1 for record in evidence_records
            if record.get("source_status") != "manual_note"
        )
        manual_note_source_count = sum(
            1 for record in evidence_records
            if record.get("source_status") == "manual_note"
        )
        bucket = review_bucket_for(non_manual_source_count, manual_note_source_count)
        chunk_sample_ids = []
        for record in evidence_records:
            chunk_sample_ids.extend(record.get("chunk_sample_ids", []))
        packet = {
            "packet_id": f"packet_{entity_id}",
            "review_order": 0,
            "entity_id": entity_id,
            "entity_type": entity.get("entity_type", ""),
            "display_name": display_name_for(entity),
            "review_status": entity.get("review_status", "pending"),
            "review_bucket": bucket,
            "source_refs": [str(ref) for ref in entity.get("source_refs", [])],
            "source_ref_count": len(entity.get("source_refs", [])),
            "non_manual_source_count": non_manual_source_count,
            "manual_note_source_count": manual_note_source_count,
            "evidence_record_count": len(evidence_records),
            "total_chunk_count": sum(record.get("chunk_count", 0) for record in evidence_records),
            "case_observation_count": sum(record.get("case_observation_count", 0) for record in evidence_records),
            "source_paths": unique_sorted(record.get("source_path", "") for record in evidence_records),
            "parsed_paths": unique_sorted(record.get("parsed_path", "") for record in evidence_records),
            "cleaned_paths": unique_sorted(record.get("cleaned_path", "") for record in evidence_records),
            "chunk_sample_ids": chunk_sample_ids[:30],
            "entity_payload": entity,
            "review_checklist": checklist_for(bucket),
            "suggested_action": suggested_action_for(bucket),
            "generated_by": "src/bgpkb/pipeline/build_entity_review_packets.py",
        }
        packets.append(packet)

    packets.sort(
        key=lambda item: (
            item["review_bucket"] == "context_only_needs_authoritative_source",
            item["review_bucket"] == "ready_with_manual_note",
            ENTITY_TYPE_ORDER.get(item["entity_type"], 99),
            item["display_name"].lower(),
            item["entity_id"],
        )
    )
    for index, packet in enumerate(packets, start=1):
        packet["review_order"] = index
    return packets


def write_jsonl(records):
    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    with JSONL_OUTPUT.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(records):
    fields = [
        "packet_id",
        "review_order",
        "entity_id",
        "entity_type",
        "display_name",
        "review_status",
        "review_bucket",
        "source_ref_count",
        "non_manual_source_count",
        "manual_note_source_count",
        "evidence_record_count",
        "total_chunk_count",
        "case_observation_count",
        "source_refs",
        "source_paths",
        "parsed_paths",
        "cleaned_paths",
        "chunk_sample_ids",
        "review_checklist",
        "suggested_action",
        "generated_by",
    ]
    with CSV_OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            row = dict(record)
            for field in ("source_refs", "source_paths", "parsed_paths", "cleaned_paths", "chunk_sample_ids", "review_checklist"):
                row[field] = "|".join(row[field])
            row.pop("entity_payload", None)
            writer.writerow(row)


def write_report(records):
    by_type = Counter(record["entity_type"] for record in records)
    by_bucket = Counter(record["review_bucket"] for record in records)
    pending_count = sum(1 for record in records if record["review_status"] == "pending")
    context_only = [
        record for record in records
        if record["review_bucket"] == "context_only_needs_authoritative_source"
    ]
    lines = [
        "# 实体人工复核包报告",
        "",
        "## 范围",
        "",
        "本报告从实体、实体复核队列和实体来源证据索引机械生成。它不判断实体是否正确，也不把实体改为 approved，只把人工复核需要打开的路径、chunk 样例和检查清单汇总到同一入口。",
        "",
        "## 摘要",
        "",
        f"- 复核包记录数：{len(records)}",
        f"- pending 记录数：{pending_count}",
        f"- JSONL 输出：`data/derived/datasets/entity_review_packets.jsonl`",
        f"- CSV 输出：`data/derived/datasets/entity_review_packets.csv`",
        f"- 仅含 manual_note/context 来源的记录数：{len(context_only)}",
        "",
        "## 按复核桶统计",
        "",
    ]
    for bucket, count in sorted(by_bucket.items()):
        lines.append(f"- {bucket}：{count}")
    lines.extend(["", "## 按实体类型统计", ""])
    for entity_type, count in sorted(by_type.items()):
        lines.append(f"- {entity_type}：{count}")
    lines.extend([
        "",
        "## 建议优先复核顺序前 30 条",
        "",
        "| 顺序 | 实体类型 | 实体 ID | 名称 | 复核桶 | 非 manual 来源 | manual 来源 | chunk 总数 |",
        "| ---: | --- | --- | --- | --- | ---: | ---: | ---: |",
    ])
    for record in records[:30]:
        lines.append(
            f"| {record['review_order']} | {record['entity_type']} | `{record['entity_id']}` | "
            f"{record['display_name']} | {record['review_bucket']} | "
            f"{record['non_manual_source_count']} | {record['manual_note_source_count']} | {record['total_chunk_count']} |"
        )
    lines.extend([
        "",
        "## 需要补权威来源的实体",
        "",
    ])
    if context_only:
        for record in context_only[:50]:
            lines.append(f"- `{record['entity_id']}`（{record['entity_type']}，{record['display_name']}）")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未从论文正文或案例正文新增结构化实体，因为这需要语义判断或 LLM 介入。",
        "- 未自动批准任何 pending 实体，因为批准需要人工确认来源是否直接支持实体字段。",
    ])
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = build_packets()
    write_jsonl(records)
    write_csv(records)
    write_report(records)
    print(f"Wrote {JSONL_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {CSV_OUTPUT.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
