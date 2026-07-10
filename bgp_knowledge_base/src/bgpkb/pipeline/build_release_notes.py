#!/usr/bin/env python3
import json
from collections import Counter
from datetime import datetime

from bgpkb import paths


OUTPUT = paths.PUBLISHED_DIR / "release_notes.md"


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _counter_table(counter, key_label, value_label):
    lines = [f"| {key_label} | {value_label} |", "| --- | ---: |"]
    if not counter:
        lines.append("| 无 | 0 |")
    else:
        for key, value in sorted(counter.items()):
            lines.append(f"| `{key}` | {value} |")
    return lines


def build_notes():
    manifest = load_json(paths.PUBLISHED_DIR / "manifest.json")
    integrity = load_json(paths.PUBLISHED_DIR / "integrity_summary.json")
    readiness = load_json(paths.PUBLISHED_DIR / "readiness_summary.json")
    bge = load_json(paths.PUBLISHED_DIR / "bge_m3_embedding_manifest.json")
    sources = load_jsonl(paths.PUBLISHED_DIR / "source_catalog.jsonl")
    entities = load_jsonl(paths.PUBLISHED_DIR / "entity_catalog.jsonl")
    chunks = load_jsonl(paths.PUBLISHED_DIR / "chunk_catalog.jsonl")
    lifecycle_actions = load_jsonl(paths.DATASETS_DIR / "lifecycle_action_queue.jsonl")

    source_types = Counter(row.get("source_type", "") for row in sources)
    entity_types = Counter(row.get("entity_type", "") for row in entities)
    entity_review = Counter(row.get("review_status", "") for row in entities)
    chunk_source_types = Counter(row.get("source_type", "") for row in chunks)
    chunk_review = Counter(row.get("review_status", "") for row in chunks)
    action_types = Counter(row.get("action_type", "") for row in lifecycle_actions)
    counts = manifest.get("counts", {})

    lines = [
        "# 发布说明",
        "",
        "## 范围",
        "",
        "本文件由 `src/bgpkb/pipeline/build_release_notes.py` 从当前发布快照机械生成。",
        "它不联网、不调用 LLM、不修改实体、关系、chunk 或人工复核输入。",
        "",
        "## 发布快照",
        "",
        f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 语料版本：`{manifest.get('corpus_version', '')}`",
        f"- 输入快照：`{manifest.get('corpus_input_snapshot', '')}`",
        f"- 来源数：{counts.get('sources', len(sources))}",
        f"- 实体数：{counts.get('entities', len(entities))}",
        f"- Chunk 数：{counts.get('chunks', len(chunks))}",
        f"- 关系数：{counts.get('relationships', 0)}",
        "",
        "## 实体变化",
        "",
        "当前没有基线对比文件，因此本节记录当前实体快照分布，后续可由增量计划或历史 release notes 计算差异。",
        "",
        *(_counter_table(entity_types, "实体类型", "数量")),
        "",
        "### 复核状态",
        "",
        *(_counter_table(entity_review, "review_status", "数量")),
        "",
        "## 来源变化",
        "",
        "当前记录来源 catalog 的类型分布和处理状态，用于发布审查。",
        "",
        *(_counter_table(source_types, "source_type", "数量")),
        "",
        "## Chunk 变化",
        "",
        "当前记录 chunk catalog 的类型分布、复核状态和层级完整性。",
        "",
        *(_counter_table(chunk_source_types, "source_type", "数量")),
        "",
        "### Chunk 复核状态",
        "",
        *(_counter_table(chunk_review, "review_status", "数量")),
        "",
        "## 质量状态",
        "",
        f"- 发布完整性：`{integrity.get('status', 'unknown')}`",
        f"- 知识库就绪度：`{readiness.get('status', 'unknown')}`",
        f"- 层级完整性：`{manifest.get('hierarchy_integrity', 'unknown')}`",
        f"- BGE-M3 索引状态：`{bge.get('status', 'unknown')}`",
        f"- BGE-M3 输入数量：{bge.get('input_count', 0)}",
        f"- 生命周期更新行动数：{len(lifecycle_actions)}",
        "",
        "### 生命周期行动类型",
        "",
        *(_counter_table(action_types, "action_type", "数量")),
        "",
        "## 发布边界",
        "",
        "- 增量计划只建议受影响步骤，不替代全量发布门禁。",
        "- CI readiness 入口只运行非联网、非 LLM、非主知识写入检查。",
        "- 人工复核决策仍必须通过 validation、audit、dry-run 和显式 `--write` 闸门。",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(build_notes(), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(paths.PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
