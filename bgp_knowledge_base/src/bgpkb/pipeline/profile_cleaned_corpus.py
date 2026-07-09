#!/usr/bin/env python3
"""生成 parsed、cleaned 与 chunks 三层语料的确定性质量画像。"""

from collections import Counter, defaultdict
import argparse
import fnmatch
import json
import os
from pathlib import Path
import re
import tempfile
import unicodedata

import yaml

from bgpkb import paths


CONFIG_PATH = paths.CONFIG_DIR / "corpus_profiling.yaml"
DATASET_PATH = paths.DATASETS_DIR / "corpus_profile.jsonl"
REPORT_PATH = paths.GENERATED_REPORTS_DIR / "corpus" / "corpus_profile_report.md"
GENERATED_BY = "src/bgpkb/pipeline/profile_cleaned_corpus.py"
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s+(.*)|\s*)$")


def load_config(config_path=CONFIG_PATH):
    return yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))


def _relative(path, root):
    try:
        return Path(path).relative_to(root).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _excluded(path, base_dir, patterns):
    relative = path.relative_to(base_dir).as_posix()
    for pattern in patterns:
        if fnmatch.fnmatch(relative, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(path.name, pattern[3:]):
            return True
    return False


def load_parsed_documents(parsed_dir, config, root):
    documents = defaultdict(list)
    for path in sorted(Path(parsed_dir).rglob("*.json")):
        if _excluded(path, Path(parsed_dir), config.get("exclude_globs", [])):
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"无法解析 parsed 文档 {path}: {exc}") from exc
        doc_id = payload.get("doc_id")
        if not isinstance(doc_id, str) or not doc_id:
            raise ValueError(f"parsed 文档缺少有效 doc_id: {path}")
        documents[doc_id].append({"path": _relative(path, root), "payload": payload})
    return documents


def load_cleaned_documents(cleaned_dir, config, root):
    documents = defaultdict(list)
    for path in sorted(Path(cleaned_dir).rglob("*.md")):
        if _excluded(path, Path(cleaned_dir), config.get("exclude_globs", [])):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"无法读取 cleaned 文档 {path}: {exc}") from exc
        relative = path.relative_to(cleaned_dir).as_posix()
        doc_id = config.get("cleaned_doc_id_overrides", {}).get(relative, path.stem)
        documents[doc_id].append({"path": _relative(path, root), "content": content})
    return documents


def load_chunks(chunk_dir, config, root):
    documents = defaultdict(list)
    for path in sorted(Path(chunk_dir).rglob("*.jsonl")):
        if _excluded(path, Path(chunk_dir), config.get("exclude_globs", [])):
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise ValueError(f"无法读取 chunk 文件 {path}: {exc}") from exc
        for line_number, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"无法解析 chunk {path}:{line_number}: {exc}") from exc
            doc_id = row.get("doc_id")
            if not isinstance(doc_id, str) or not doc_id:
                raise ValueError(f"chunk 缺少有效 doc_id: {path}:{line_number}")
            documents[doc_id].append({"path": _relative(path, root), "payload": row})
    return documents


def _body_text(content):
    lines = []
    for line in content.splitlines():
        if HEADING_RE.match(line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _paragraphs(body):
    return [item.strip() for item in re.split(r"\n\s*\n", body) if item.strip()]


def _heading_metrics(parsed_entries):
    headings = []
    empty_count = 0
    section_count = 0
    for entry in parsed_entries:
        sections = entry["payload"].get("sections", [])
        if not isinstance(sections, list):
            raise ValueError(f"parsed sections 必须是数组: {entry['path']}")
        section_count += len(sections)
        for section in sections:
            heading = section.get("heading", "") if isinstance(section, dict) else ""
            if not isinstance(heading, str) or not heading.strip():
                empty_count += 1
            else:
                headings.append(heading.strip())
    counts = Counter(headings)
    duplicate_count = sum(count for count in counts.values() if count > 1)
    return section_count, empty_count, duplicate_count


def _abnormal_symbol_count(body):
    return sum(
        1
        for char in body
        if char != "�" and not char.isspace() and unicodedata.category(char).startswith("C")
    )


def _build_metrics(parsed_entries, cleaned_entries, chunk_entries, config):
    bodies = [_body_text(entry["content"]) for entry in cleaned_entries]
    body = "\n\n".join(part for part in bodies if part)
    paragraphs = _paragraphs(body)
    section_count, empty_heading_count, duplicate_heading_count = _heading_metrics(parsed_entries)
    replacement_count = body.count("�")
    abnormal_count = _abnormal_symbol_count(body)
    table_config = config["table_detection"]
    table_lines = sum(
        1 for line in body.splitlines()
        if line.count("|") >= table_config["minimum_pipe_count"]
    )
    character_count = len(body)
    return {
        "character_count": character_count,
        "paragraph_count": len(paragraphs),
        "average_paragraph_chars": round(
            sum(len(item) for item in paragraphs) / len(paragraphs), 6
        ) if paragraphs else 0.0,
        "section_count": section_count,
        "chunk_count": len(chunk_entries),
        "replacement_character_count": replacement_count,
        "suspected_table_line_count": table_lines,
        "abnormal_symbol_count": abnormal_count,
        "abnormal_symbol_ratio": round(abnormal_count / character_count, 6) if character_count else 0.0,
        "empty_heading_count": empty_heading_count,
        "duplicate_heading_count": duplicate_heading_count,
    }


def _classify_issues(doc_id, parsed_entries, cleaned_entries, chunk_entries, metrics, config):
    blocking = []
    warnings = []
    if len(parsed_entries) > 1 or len(cleaned_entries) > 1:
        blocking.append("duplicate_doc_id")
    if cleaned_entries and metrics["character_count"] == 0:
        blocking.append("empty_cleaned_content")
    if chunk_entries and not parsed_entries and not cleaned_entries:
        blocking.append("orphan_chunk_document")
    if metrics["replacement_character_count"]:
        blocking.append("replacement_character")

    if not parsed_entries:
        warnings.append("missing_parsed")
    if not cleaned_entries:
        warnings.append("missing_cleaned")
    if not chunk_entries:
        warnings.append("missing_chunks")
    thresholds = config["thresholds"]
    if cleaned_entries and metrics["character_count"] < thresholds["short_document_chars"]:
        warnings.append("short_document")
    if metrics["character_count"] > thresholds["long_document_chars"]:
        warnings.append("long_document")
    if metrics["suspected_table_line_count"] >= config["table_detection"]["minimum_table_rows"]:
        warnings.append("suspected_table")
    if (
        metrics["abnormal_symbol_count"]
        and metrics["abnormal_symbol_ratio"] >= thresholds["abnormal_symbol_ratio"]
    ):
        warnings.append("abnormal_symbols")
    if metrics["empty_heading_count"]:
        warnings.append("empty_heading")
    if metrics["duplicate_heading_count"]:
        warnings.append("duplicate_heading")
    return sorted(blocking), sorted(warnings)


def build_corpus_profiles(parsed_dir, cleaned_dir, chunk_dir, config, root=None):
    root = Path(root or paths.PROJECT_ROOT)
    parsed = load_parsed_documents(parsed_dir, config, root)
    cleaned = load_cleaned_documents(cleaned_dir, config, root)
    chunks = load_chunks(chunk_dir, config, root)
    doc_ids = sorted(set(parsed) | set(cleaned) | set(chunks))
    profiles = []
    for doc_id in doc_ids:
        parsed_entries = parsed.get(doc_id, [])
        cleaned_entries = cleaned.get(doc_id, [])
        chunk_entries = chunks.get(doc_id, [])
        metrics = _build_metrics(parsed_entries, cleaned_entries, chunk_entries, config)
        blocking, warnings = _classify_issues(
            doc_id, parsed_entries, cleaned_entries, chunk_entries, metrics, config
        )
        profiles.append({
            "doc_id": doc_id,
            "parsed_exists": bool(parsed_entries),
            "cleaned_exists": bool(cleaned_entries),
            "chunks_exist": bool(chunk_entries),
            "parsed_paths": sorted({entry["path"] for entry in parsed_entries}),
            "cleaned_paths": sorted({entry["path"] for entry in cleaned_entries}),
            "chunk_files": sorted({entry["path"] for entry in chunk_entries}),
            "metrics": metrics,
            "blocking_issues": blocking,
            "warnings": warnings,
            "generated_by": GENERATED_BY,
        })
    return profiles


def _jsonl_text(records):
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )


def render_profile_report(profiles, ocr_assessments=None):
    blocking_counts = Counter(
        issue for profile in profiles for issue in profile["blocking_issues"]
    )
    warning_counts = Counter(
        warning for profile in profiles for warning in profile["warnings"]
    )
    blocking_total = sum(blocking_counts.values())
    warning_total = sum(warning_counts.values())
    lines = [
        "# 语料质量画像报告",
        "",
        "## 摘要",
        "",
        f"- 结论：{'阻断' if blocking_total else '通过'}",
        f"- 文档画像：{len(profiles)} 条",
        f"- 确定性阻断问题：{blocking_total} 条",
        f"- 非阻断告警：{warning_total} 条",
        f"- 模型评估状态：{'未运行' if ocr_assessments is None else '已生成'}",
        "- 模型风险不参与确定性质量门禁，也不会修改主知识数据。",
        "",
        "## 阶段覆盖",
        "",
        "| 阶段 | 文档数 |",
        "| --- | ---: |",
        f"| parsed | {sum(1 for row in profiles if row['parsed_exists'])} |",
        f"| cleaned | {sum(1 for row in profiles if row['cleaned_exists'])} |",
        f"| chunks | {sum(1 for row in profiles if row['chunks_exist'])} |",
        "",
        "## 确定性阻断问题",
        "",
    ]
    if blocking_counts:
        for issue, count in sorted(blocking_counts.items()):
            lines.append(f"- `{issue}`：{count} 条")
    else:
        lines.append("- 无")
    lines.extend(["", "## 非阻断告警", ""])
    if warning_counts:
        for warning, count in sorted(warning_counts.items()):
            lines.append(f"- `{warning}`：{count} 条")
    else:
        lines.append("- 无")
    lines.extend([
        "",
        "## 文档明细",
        "",
        "| doc_id | 字符数 | section | chunk | 阻断 | 告警 |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ])
    for profile in profiles:
        metrics = profile["metrics"]
        lines.append(
            f"| `{profile['doc_id']}` | {metrics['character_count']} | "
            f"{metrics['section_count']} | {metrics['chunk_count']} | "
            f"{', '.join(profile['blocking_issues']) or '无'} | "
            f"{', '.join(profile['warnings']) or '无'} |"
        )
    lines.extend(["", "## 可选 OCR 模型评估", ""])
    if ocr_assessments is None:
        lines.append("- 未运行；真实 Provider 必须显式启用。")
    elif not ocr_assessments:
        lines.append("- 已运行，但没有可评估文档。")
    else:
        status_counts = Counter(row["status"] for row in ocr_assessments)
        risk_counts = Counter(row["risk_level"] for row in ocr_assessments)
        providers = sorted({row["provider"] for row in ocr_assessments})
        models = sorted({row["model"] for row in ocr_assessments})
        prompt_versions = sorted({row["prompt_version"] for row in ocr_assessments})
        lines.extend([
            f"- Provider：{', '.join(providers)}",
            f"- Model：{', '.join(models)}",
            f"- Prompt version：{', '.join(prompt_versions)}",
            f"- 状态：{json.dumps(dict(sorted(status_counts.items())), ensure_ascii=False)}",
            f"- 风险：{json.dumps(dict(sorted(risk_counts.items())), ensure_ascii=False)}",
            "- 所有风险结论仅供人工复核，不参与确定性门禁。",
        ])
    return "\n".join(lines).rstrip() + "\n"


def _stage_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent,
        prefix=f".{path.name}.", delete=False,
    )
    try:
        with handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        return Path(handle.name)
    except Exception:
        Path(handle.name).unlink(missing_ok=True)
        raise


def _atomic_write_many(contents):
    staged = []
    try:
        for target, text in contents:
            staged.append((Path(target), _stage_text(target, text)))
        for target, staged_path in staged:
            os.replace(staged_path, target)
    finally:
        for _, staged_path in staged:
            staged_path.unlink(missing_ok=True)


def write_profile_outputs(profiles, dataset_path=DATASET_PATH, report_path=REPORT_PATH, ocr_assessments=None):
    _atomic_write_many([
        (dataset_path, _jsonl_text(profiles)),
        (report_path, render_profile_report(profiles, ocr_assessments=ocr_assessments)),
    ])


def run_profiling(
    parsed_dir=paths.PARSED_DIR,
    cleaned_dir=paths.CLEANED_DIR,
    chunk_dir=paths.CHUNKS_DIR,
    config=None,
    dataset_path=DATASET_PATH,
    report_path=REPORT_PATH,
    root=paths.PROJECT_ROOT,
    ocr_assessments=None,
):
    config = config or load_config()
    profiles = build_corpus_profiles(parsed_dir, cleaned_dir, chunk_dir, config, root=root)
    write_profile_outputs(
        profiles, dataset_path=dataset_path, report_path=report_path,
        ocr_assessments=ocr_assessments,
    )
    return profiles


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成阶段 A 确定性语料质量画像")
    parser.add_argument("--config", default=str(CONFIG_PATH))
    args = parser.parse_args(argv)
    profiles = run_profiling(config=load_config(args.config))
    print(f"Wrote {DATASET_PATH.relative_to(paths.PROJECT_ROOT)}")
    print(f"Wrote {REPORT_PATH.relative_to(paths.PROJECT_ROOT)}")
    if any(profile["blocking_issues"] for profile in profiles):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
