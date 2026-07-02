"""分级清洗、逐次转换审计和复核隔离。"""

import copy
from dataclasses import dataclass, field
import hashlib
import json
import re
import unicodedata

from bgpkb.cleaning_v2.heading_hierarchy import infer_heading_hierarchy


GENERATED_BY = "src/bgpkb/cleaning_v2/transformations.py"


@dataclass(frozen=True)
class CleaningRule:
    rule_id: str
    version: str
    level: str
    options: dict = field(default_factory=dict)


def _snapshot(blocks):
    return [{"block_id": row.get("block_id"), "cleaned_text": row.get("cleaned_text", ""), "heading_level": row.get("heading_level"), "table": row.get("table")} for row in blocks]


def _record(rule, before, after, block_ids, operation, confidence=1.0, evidence=None):
    payload = json.dumps([rule.rule_id, rule.version, block_ids, before, after], ensure_ascii=False, sort_keys=True, default=str)
    return {
        "transformation_id": "transformation_v2_" + hashlib.sha256(payload.encode()).hexdigest(),
        "rule_id": rule.rule_id, "rule_version": rule.version, "rule_level": rule.level,
        "operation": operation, "input_block_ids": block_ids, "output_block_ids": block_ids,
        "before": before, "after": after,
        "evidence": evidence or {"rule_options": rule.options},
        "confidence": confidence, "generated_by": GENERATED_BY,
    }


def _normalize(text):
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def _apply_structural(blocks, rule):
    changed = []
    if rule.rule_id == "remove_repeated_header_footer":
        groups = {}
        for row in blocks:
            if row.get("block_type") in {"page_header", "page_footer"}:
                groups.setdefault(row.get("cleaned_text", ""), []).append(row)
        for rows in groups.values():
            if len({row.get("page_number") for row in rows}) >= 2:
                for row in rows:
                    row["cleaned_text"] = ""
                    changed.append(row)
    elif rule.rule_id == "correct_heading_level":
        by_id = {row.get("block_id"): row for row in blocks}
        for block_id, level in rule.options.get("levels", {}).items():
            if block_id in by_id and by_id[block_id].get("heading_level") != level:
                by_id[block_id]["heading_level"] = level
                changed.append(by_id[block_id])
    elif rule.rule_id == "merge_cross_page_paragraph":
        for left, right in zip(blocks, blocks[1:]):
            if left.get("block_type") == right.get("block_type") == "paragraph" and left.get("continues_to_next"):
                left_text = left.get("cleaned_text", "")
                separator = "" if left_text.endswith("-") else " "
                left["cleaned_text"] = left_text.removesuffix("-") + separator + right.get("cleaned_text", "")
                right["cleaned_text"] = ""
                changed.extend([left, right])
    elif rule.rule_id == "merge_cross_page_table":
        for left, right in zip(blocks, blocks[1:]):
            if left.get("block_type") == right.get("block_type") == "table" and right.get("continues_from_previous"):
                if left.get("table", {}).get("columns") == right.get("table", {}).get("columns"):
                    left["table"]["rows"] += right["table"].get("rows", 0)
                    left["table"]["cells"].extend(copy.deepcopy(right["table"].get("cells", [])))
                    right["cleaned_text"] = ""
                    changed.extend([left, right])
    return list({row["block_id"]: row for row in changed}.values())


def apply_rules(raw_blocks, rules, config):
    del config
    cleaned = copy.deepcopy(raw_blocks)
    transformations = []
    review_items = []
    for rule in rules:
        if rule.level not in {"lossless", "structural", "semantic"}:
            raise ValueError(f"unknown rule level: {rule.level}")
        if rule.level == "semantic":
            review_items.append({"rule_id": rule.rule_id, "block_id": cleaned[0]["block_id"] if cleaned else "", "review_status": "pending_review", "reason": "semantic_change_forbidden"})
            continue
        before = _snapshot(cleaned)
        if rule.level == "lossless" and rule.rule_id == "unicode_whitespace":
            changed = []
            for row in cleaned:
                normalized = _normalize(row.get("cleaned_text", ""))
                if normalized != row.get("cleaned_text", ""):
                    row["cleaned_text"] = normalized
                    changed.append(row)
        elif rule.level == "structural" and rule.rule_id == "infer_heading_hierarchy":
            candidates = infer_heading_hierarchy(
                cleaned, source_format=str(rule.options.get("source_format", ""))
            )
            by_id = {row.get("block_id"): row for row in cleaned}
            changed = []
            applied_candidates = []
            applied_source_ids = set()
            for candidate in candidates:
                source_block_id = candidate["source_block_id"]
                if source_block_id in applied_source_ids or source_block_id not in by_id:
                    continue
                row = by_id[source_block_id]
                desired_type = "heading" if candidate["promoted"] else row.get("block_type")
                desired = (
                    desired_type,
                    candidate["level"],
                    candidate["parent_block_id"],
                    candidate["text"],
                )
                current = (
                    row.get("block_type"),
                    row.get("heading_level"),
                    row.get("parent_block_id"),
                    row.get("cleaned_text"),
                )
                if desired != current:
                    row["block_type"] = desired_type
                    row["heading_level"] = candidate["level"]
                    row["parent_block_id"] = candidate["parent_block_id"]
                    row["cleaned_text"] = candidate["text"]
                    changed.append(row)
                    applied_candidates.append(candidate)
                applied_source_ids.add(source_block_id)
            structural_evidence = {
                "rule_options": rule.options,
                "candidates": applied_candidates,
            }
        else:
            changed = _apply_structural(cleaned, rule)
        if not changed:
            continue
        after = _snapshot(cleaned)
        ids = [row["block_id"] for row in changed]
        transformations.append(
            _record(
                rule,
                before,
                after,
                ids,
                rule.rule_id,
                1.0 if rule.level == "lossless" else 0.9,
                evidence=structural_evidence
                if rule.level == "structural" and rule.rule_id == "infer_heading_hierarchy"
                else None,
            )
        )
        if rule.level == "structural":
            for row in changed:
                row["review_status"] = "pending_review"
            review_items.append({"rule_id": rule.rule_id, "block_id": ids[0], "review_status": "pending_review", "reason": "structural_change_requires_review"})
    return {"cleaned_blocks": cleaned, "transformations": transformations, "review_items": review_items}


def _risk_reasons(block):
    reasons = []
    if block.get("review_status") not in {"approved", "auto_approved"}:
        reasons.append(block.get("review_status", "pending_review"))
    issues = block.get("quality", {}).get("issues", [])
    reasons.extend(issue for issue in issues if issue in {"fallback_parser", "low_confidence_ocr"})
    return list(dict.fromkeys(reasons))


def build_review_queue(blocks):
    return [{"block_id": row["block_id"], "review_status": "pending_review", "reasons": _risk_reasons(row)} for row in blocks if _risk_reasons(row)]


def publishable_blocks(blocks):
    return [row for row in blocks if row.get("review_status") in {"approved", "auto_approved"} and not _risk_reasons(row)]
