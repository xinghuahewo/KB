"""从 approved Canonical Block v2 确定性派生并评测迁移结果。"""

from __future__ import annotations

import copy
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata

from .section_hierarchy import build_hierarchy, render_table_markdown
from .transformations import publishable_blocks


def _render_block(block, assets_by_id):
    block_type = block.get("block_type")
    text = block.get("cleaned_text", "").strip()
    if not text and block_type not in {"table", "picture"}:
        return "", ""
    if block_type in {"title", "heading"}:
        level = max(1, min(6, int(block.get("heading_level") or (1 if block_type == "title" else 2))))
        return f"{'#' * level} {text}", text
    if block_type == "list_item":
        return f"- {text}", text
    if block_type == "code":
        return f"```\n{text}\n```", text
    if block_type == "formula":
        return f"$$\n{text}\n$$", text
    if block_type == "table":
        table_text = render_table_markdown(block.get("table") or {})
        return table_text, table_text
    if block_type == "picture":
        asset = next((assets_by_id.get(item) for item in block.get("asset_refs", []) if assets_by_id.get(item)), None)
        if not asset:
            return "", ""
        caption = asset.get("caption") or text or "图片"
        return f"![{caption}]({asset['path']})", caption
    return text, text


def build_derivatives(document, *, maximum_chunk_chars=1200):
    """在内存中构建派生物；不改变权威文档。"""
    document = copy.deepcopy(document)
    approved = publishable_blocks(document.get("blocks", []))
    hierarchy = build_hierarchy(document, maximum_chunk_chars=maximum_chunk_chars)
    approved_ids = {row["block_id"] for row in approved}
    assets_by_id = {row["asset_id"]: row for row in document.get("assets", [])}
    referenced_asset_ids = {
        asset_id for block in approved for asset_id in block.get("asset_refs", []) if asset_id in assets_by_id
    }
    assets = [copy.deepcopy(assets_by_id[item]) for item in sorted(referenced_asset_ids)]
    markdown_parts = []

    for block in approved:
        rendered, _ = _render_block(block, assets_by_id)
        if rendered:
            markdown_parts.append(rendered)
    markdown = "\n\n".join(part for part in markdown_parts if part).rstrip() + "\n"
    digest_payload = json.dumps(
        {
            "markdown": markdown,
            "assets": assets,
            "sections": hierarchy.sections,
            "chunks": hierarchy.chunks,
            "retrieval_excluded_blocks": hierarchy.excluded_blocks,
        },
        ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return {
        "doc_id": document["doc_id"],
        "markdown": markdown,
        "assets": assets,
        "sections": hierarchy.sections,
        "chunks": hierarchy.chunks,
        "retrieval_excluded_blocks": hierarchy.excluded_blocks,
        "approved_block_count": len(approved),
        "excluded_block_count": len(document.get("blocks", [])) - len(approved_ids),
        "content_digest": "sha256:" + hashlib.sha256(digest_payload).hexdigest(),
    }


def _write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _atomic_text(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def _atomic_bytes(path, content):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise


def derive_document(document, output_root, *, maximum_chunk_chars=1200):
    """使用临时目录原子发布单篇 Markdown、assets 和 chunks v2。"""
    result = build_derivatives(document, maximum_chunk_chars=maximum_chunk_chars)
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / result["doc_id"]
    temporary = Path(tempfile.mkdtemp(prefix=f".{result['doc_id']}.tmp-", dir=output_root))
    backup = output_root / f".{result['doc_id']}.backup"
    try:
        (temporary / "document.md").write_text(result["markdown"], encoding="utf-8")
        (temporary / "assets.json").write_text(
            json.dumps(result["assets"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        _write_jsonl(temporary / "chunks.jsonl", result["chunks"])
        (temporary / "derivation_manifest.json").write_text(
            json.dumps(
                {key: value for key, value in result.items() if key not in {"markdown", "assets", "sections", "chunks"}},
                ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            ) + "\n",
            encoding="utf-8",
        )
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            os.replace(target, backup)
        os.replace(temporary, target)
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if target.exists() and backup.exists():
            shutil.rmtree(target)
        if backup.exists():
            os.replace(backup, target)
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return result


def publish_derivatives(
    document, *, markdown_root, assets_root, chunks_root, maximum_chunk_chars=1200,
    asset_source_root=None,
):
    """按项目版本化目录发布三类只读派生产物。"""
    result = build_derivatives(document, maximum_chunk_chars=maximum_chunk_chars)
    doc_id = result["doc_id"]
    _atomic_text(Path(markdown_root) / f"{doc_id}.md", result["markdown"])
    _atomic_text(
        Path(assets_root) / doc_id / "assets.json",
        json.dumps(result["assets"], ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
    )
    if asset_source_root is not None:
        for asset in result["assets"]:
            relative = Path(asset["path"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"非法资产路径: {relative}")
            content = (Path(asset_source_root) / relative).read_bytes()
            expected_sha = asset.get("sha256")
            if expected_sha and hashlib.sha256(content).hexdigest() != expected_sha:
                raise ValueError(f"资产 hash 不匹配: {relative}")
            _atomic_bytes(Path(assets_root) / doc_id / relative, content)
    chunks_content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in result["chunks"]
    )
    _atomic_text(Path(chunks_root) / f"{doc_id}.jsonl", chunks_content)
    return result


def _plain_markdown(markdown):
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`|$*-]+", " ", text)
    return " ".join(text.split())


def _tokens(text):
    return re.findall(r"\w+", text, flags=re.UNICODE)


def _comparison_text(markdown):
    text = unicodedata.normalize("NFKC", markdown)
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    return _plain_markdown(text).casefold()


def _transformation_deletions(transformations):
    deleted = []
    for row in transformations:
        before = row.get("before")
        after = row.get("after")
        if isinstance(before, str) and isinstance(after, str) and before != after:
            deleted.append(before.replace(after, "", 1) if after and after in before else before)
        elif isinstance(before, list) and isinstance(after, list):
            after_by_id = {row.get("block_id"): str(row.get("cleaned_text", "")) for row in after}
            for snapshot in before:
                before_text = str(snapshot.get("cleaned_text", ""))
                after_text = after_by_id.get(snapshot.get("block_id"), "")
                if before_text != after_text:
                    deleted.append(
                        before_text.replace(after_text, "", 1)
                        if after_text and after_text in before_text
                        else before_text
                    )
    return [item for item in deleted if item]


def compare_v1_v2(v1_markdown, v2_document, v1_chunks, v2_chunks, transformations):
    v1_plain = _comparison_text(v1_markdown)
    v2_derivative = build_derivatives(v2_document)
    v2_plain = _comparison_text(v2_derivative["markdown"])
    v1_counts = Counter(_tokens(v1_plain))
    v2_counts = Counter(_tokens(v2_plain))
    removed_counts = v1_counts - v2_counts
    v1_weight = sum(len(token) * count for token, count in v1_counts.items())
    removed_nonspace = sum(len(token) * count for token, count in removed_counts.items())
    matching = 1.0 - removed_nonspace / v1_weight if v1_weight else 1.0
    attributable_counts = Counter()
    for item in _transformation_deletions(transformations):
        attributable_counts.update(_tokens(_comparison_text(item)))
    attributed = sum(
        len(token) * min(count, attributable_counts[token])
        for token, count in removed_counts.items()
    )
    v2_blocks = publishable_blocks(v2_document.get("blocks", []))
    v1_source_refs = {row.get("source_ref", "") for row in v1_chunks if row.get("source_ref")}
    v2_source_refs = {row.get("source_ref", "") for row in v2_chunks if row.get("source_ref")}
    return {
        "body": {
            "v1_character_count": len(v1_plain), "v2_character_count": len(v2_plain),
            "coverage_ratio": matching,
        },
        "titles": {"v1_count": len(re.findall(r"^#\s", v1_markdown, re.MULTILINE)), "v2_count": sum(row.get("block_type") == "title" for row in v2_blocks)},
        "sections": {"v1_count": len(re.findall(r"^#{1,6}\s", v1_markdown, re.MULTILINE)), "v2_count": sum(row.get("block_type") in {"title", "heading"} for row in v2_blocks)},
        "tables": {"v1_count": v1_markdown.count("| ---"), "v2_count": sum(row.get("block_type") == "table" for row in v2_blocks)},
        "pictures": {"v1_count": len(re.findall(r"!\[[^]]*\]\([^)]*\)", v1_markdown)), "v2_count": sum(row.get("block_type") == "picture" for row in v2_blocks)},
        "chunks": {"v1_count": len(v1_chunks), "v2_count": len(v2_chunks)},
        "source_refs": {"preserved_count": len(v1_source_refs & v2_source_refs), "missing": sorted(v1_source_refs - v2_source_refs), "added": sorted(v2_source_refs - v1_source_refs)},
        "removed_content": {"removed_char_count": removed_nonspace, "attributed_char_count": min(attributed, removed_nonspace), "unattributed_char_count": max(0, removed_nonspace - attributed)},
    }


def evaluate_migration_gates(
    document,
    diff,
    *,
    current_digest,
    repeated_digest=None,
    minimum_coverage=0.995,
    migration_decision=None,
):
    issues = []
    unattributed = int(diff.get("removed_content", {}).get("unattributed_char_count", 0))
    approved_difference = bool(
        migration_decision
        and migration_decision.get("decision") == "approved"
        and migration_decision.get("reason_code")
        and migration_decision.get("evidence", {}).get("v1_digest")
        and migration_decision.get("evidence", {}).get("v2_digest")
    )
    if diff.get("body", {}).get("coverage_ratio", 0) < minimum_coverage and unattributed and not approved_difference:
        issues.append("body_coverage_below_threshold")
    if unattributed and not approved_difference:
        issues.append("unattributed_content_removal")
    if document.get("parser_mode") == "fallback" and document.get("fallback_review_status") != "approved":
        issues.append("fallback_document")
    if repeated_digest is not None and current_digest != repeated_digest:
        issues.append("unstable_repeated_derivation")
    blocks = document.get("blocks", [])
    ids = [row.get("block_id") for row in blocks]
    if len(ids) != len(set(ids)):
        issues.append("duplicate_block_ids")
    if any("�" in row.get("cleaned_text", "") for row in blocks):
        issues.append("replacement_characters")
    if any(not row.get("provenance", {}).get("source_path") for row in blocks):
        issues.append("untraceable_blocks")
    if diff.get("body", {}).get("v2_character_count", 0) == 0:
        issues.append("empty_body")
    return {"passed": not issues, "blocking_issues": issues}
