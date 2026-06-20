#!/usr/bin/env python3
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "datasets"
REPORT_DIR = ROOT / "reports" / "human_review_session_guides"
README = REPORT_DIR / "README.md"
DECISION_INPUT = "review_inputs/human_review_decisions.csv"


def load_jsonl(path):
    records = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def md_text(value):
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def md_list(values):
    if not values:
        return "- 无"
    return "\n".join(f"- `{value}`" for value in values)


def extracts_by_id():
    return {
        record.get("extract_id"): record
        for record in load_jsonl(DATASET_DIR / "human_review_evidence_extracts.jsonl")
        if record.get("extract_id")
    }


def session_records():
    records = load_jsonl(DATASET_DIR / "human_review_session_queue.jsonl")
    records.sort(key=lambda item: (item.get("session_order", 999999), item.get("within_session_order", 999999)))
    return records


def cleanup_old_session_files():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    for path in REPORT_DIR.glob("review_session_*.md"):
        path.unlink()


def write_readme(records):
    by_session = Counter(record.get("session_id", "unknown") for record in records)
    by_status = Counter(record.get("queue_status", "unknown") for record in records)
    lines = [
        "# 人工复核会话指南",
        "",
        "## 范围",
        "",
        "本目录从人工复核会话队列和证据摘录机械生成。它只把待复核实体按 session 展开为可读操作入口，不判断实体是否应批准或拒绝。",
        "",
        "## 使用方式",
        "",
        f"1. 打开一个 session 文件，从上到下核验实体、来源路径和摘录。",
        "2. 如需逐 session 填写参考，可打开 `review_inputs/human_review_session_decision_templates/` 中对应模板。",
        f"3. 人工判断后，在 `{DECISION_INPUT}` 中填写 `entity_id`、`review_decision`、`reviewer`、`reviewed_at` 和 `decision_note`。",
        "4. 若需要语义判断或 LLM，填写 `needs_semantic_review` 或保持 `unreviewed`，不要在流水线中自动判定。",
        "5. 填写后运行 `python3 scripts/build_human_review_decision_audit.py` 审计，再按需显式应用。",
        "",
        "## 摘要",
        "",
        f"- 队列记录数：{len(records)}",
        f"- session 数：{len(by_session)}",
        f"- 人工决策输入：`{DECISION_INPUT}`",
        "",
        "## 按队列状态统计",
        "",
    ]
    for status, count in sorted(by_status.items()):
        lines.append(f"- {status}：{count}")
    lines.extend(["", "## Session 文件", ""])
    for session_id, count in sorted(by_session.items()):
        lines.append(f"- `{session_id}.md`：{count} 条")
    lines.extend([
        "",
        "## 跳过事项",
        "",
        "- 未自动批准、拒绝或改写实体。",
        "- 未判断摘录是否足以支持实体字段。",
        "- 未调用 LLM，也不下载新来源。",
    ])
    README.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_session_file(session_id, records, extracts):
    path = REPORT_DIR / f"{session_id}.md"
    status_counts = Counter(record.get("queue_status", "unknown") for record in records)
    lines = [
        f"# {session_id} 人工复核指南",
        "",
        "## 范围",
        "",
        "本文件只展开该 session 的人工复核入口。摘录来自现有 chunk 样例和机械词项匹配，不代表自动批准依据。",
        "",
        "## 摘要",
        "",
        f"- 条目数：{len(records)}",
        f"- 人工决策输入：`{DECISION_INPUT}`",
    ]
    for status, count in sorted(status_counts.items()):
        lines.append(f"- {status}：{count}")
    lines.append("")

    for record in records:
        title = md_text(record.get("display_name", "")) or record.get("entity_id", "")
        lines.extend([
            f"## {record.get('within_session_order')}. {title}",
            "",
            f"- 实体 ID：`{record.get('entity_id')}`",
            f"- 实体类型：{record.get('entity_type')}",
            f"- 队列状态：`{record.get('queue_status')}`",
            f"- 当前实体状态：`{record.get('review_status')}`",
            f"- 当前人工决策：`{record.get('review_decision')}`",
            f"- 人工决策输入：`{record.get('decision_input_path')}`",
            f"- 下一步：{md_text(record.get('next_step', ''))}",
            "",
            "### 来源引用",
            "",
            md_list(record.get("source_refs", [])),
            "",
            "### cleaned 路径",
            "",
            md_list(record.get("cleaned_paths", [])),
            "",
            "### parsed 路径",
            "",
            md_list(record.get("parsed_paths", [])),
            "",
            "### Top 摘录",
            "",
        ])
        for extract_id in record.get("top_extract_ids", []):
            extract = extracts.get(extract_id, {})
            if not extract:
                lines.append(f"- `{extract_id}`：缺失")
                continue
            terms = ", ".join(extract.get("matched_terms", [])[:10]) or "无"
            section_path = " / ".join(extract.get("section_path", [])) or "无"
            lines.extend([
                f"#### `{extract_id}`",
                "",
                f"- chunk：`{extract.get('chunk_id', '')}`",
                f"- 文档：`{extract.get('doc_id', '')}`",
                f"- source_ref：`{extract.get('source_ref', '')}`",
                f"- section_path：{md_text(section_path)}",
                f"- match_score：{extract.get('match_score', 0)}",
                f"- matched_terms：{md_text(terms)}",
                "",
                "> " + md_text(extract.get("excerpt", "")),
                "",
            ])
        lines.extend([
            "### 复核边界",
            "",
            "- 只根据人工打开的来源和摘录做核验。",
            "- 若需要解释、归纳或判断证据强度，记录为 `needs_semantic_review` 或保持 `unreviewed`。",
            "- 本指南不自动产生 approved/rejected 决策。",
            "",
        ])
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    records = session_records()
    extracts = extracts_by_id()
    cleanup_old_session_files()
    write_readme(records)
    grouped = defaultdict(list)
    for record in records:
        grouped[record.get("session_id", "unknown")].append(record)
    for session_id, session_items in sorted(grouped.items()):
        write_session_file(session_id, session_items, extracts)
    print(f"Wrote {README.relative_to(ROOT)}")
    print(f"Wrote {len(grouped)} session guides in {REPORT_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
