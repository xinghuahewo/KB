#!/usr/bin/env python3
"""生成仅供人工审核的标准语义映射候选。"""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

import yaml

from bgpkb import paths
from bgpkb.service import llm_client


CONFIG_RELATIVE_PATH = Path("metadata/config/standard_exports.yaml")
RELATIONSHIPS_RELATIVE_PATH = Path("data/knowledge/relationships/relationships.jsonl")
REPORT_RELATIVE_PATH = Path("data/generated/reports/review/standard_mapping_candidate_report.md")
ALLOWED_CANDIDATE_FIELDS = {
    "candidate_id",
    "candidate_type",
    "local_value",
    "suggested_mapping",
    "source_refs",
    "input_fingerprint",
    "evidence_summary",
    "confidence",
    "reason",
    "provider",
    "model",
    "prompt_version",
    "generated_at",
    "status",
}
REQUIRED_CANDIDATE_FIELDS = ALLOWED_CANDIDATE_FIELDS - {"evidence_summary", "generated_at"}
CURIE_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z][A-Za-z0-9_-]*$")
FINGERPRINT_PATTERN = re.compile(r"^[a-f0-9]{64}$")
MODEL_SUGGESTION_FIELDS = {
    "candidate_type", "local_value", "suggested_mapping", "source_refs",
    "evidence_summary", "confidence", "reason",
}
MODEL_REQUIRED_FIELDS = MODEL_SUGGESTION_FIELDS - {"evidence_summary"}


def collect_unmapped_relations(relationships, relation_mappings):
    """聚合关系数据中确实出现、但配置尚未映射的关系。"""
    grouped = defaultdict(list)
    for relationship in relationships:
        relation = relationship.get("relation", "")
        if relation and relation not in relation_mappings:
            grouped[relation].append(relationship)

    items = []
    for relation in sorted(grouped):
        rows = sorted(
            grouped[relation],
            key=lambda row: (
                row.get("src_id", ""), row.get("dst_id", ""),
                json.dumps(row, ensure_ascii=False, sort_keys=True),
            ),
        )
        examples = [
            {
                key: row[key]
                for key in (
                    "src_id", "src_type", "relation", "dst_id", "dst_type", "source_refs", "confidence"
                )
                if key in row
            }
            for row in rows
        ]
        items.append({
            "candidate_type": "relation",
            "local_value": relation,
            "source_refs": sorted({
                source_ref
                for row in rows
                for source_ref in row.get("source_refs", [])
                if source_ref
            }),
            "evidence_summary": f"本地关系数据中出现 {len(rows)} 条 `{relation}` 关系。",
            "examples": examples,
        })
    return items


def build_input_fingerprint(item, prompt_version):
    """对候选的完整输入证据和 prompt 版本计算 SHA-256。"""
    payload = {
        "candidate_type": item.get("candidate_type"),
        "local_value": item.get("local_value"),
        "source_refs": sorted(item.get("source_refs", [])),
        "evidence_summary": item.get("evidence_summary", ""),
        "examples": item.get("examples", []),
        "prompt_version": prompt_version,
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_candidate_id(candidate_type, local_value, suggested_mapping, input_fingerprint):
    """构造包含完整输入指纹的稳定候选 ID。"""
    safe_local = re.sub(r"[^A-Za-z0-9_-]+", "_", local_value).strip("_") or "value"
    mapping_digest = hashlib.sha256(suggested_mapping.encode("utf-8")).hexdigest()[:16]
    return f"standard_mapping__{candidate_type}__{safe_local}__{mapping_digest}__{input_fingerprint}"


def _camel_case(local_value):
    head, *tail = local_value.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


def _build_candidate(item, config, provider, model, suggested_mapping, confidence, reason, generated_at):
    policy = config["model_policy"]
    prompt_version = policy["prompt_version"]
    fingerprint = build_input_fingerprint(item, prompt_version)
    candidate = {
        "candidate_id": build_candidate_id(
            item["candidate_type"], item["local_value"], suggested_mapping, fingerprint
        ),
        "candidate_type": item["candidate_type"],
        "local_value": item["local_value"],
        "suggested_mapping": suggested_mapping,
        "source_refs": list(item.get("source_refs", [])),
        "input_fingerprint": fingerprint,
        "evidence_summary": item.get("evidence_summary", ""),
        "confidence": confidence,
        "reason": reason,
        "provider": provider,
        "model": model,
        "prompt_version": prompt_version,
        "generated_at": generated_at,
        "status": "pending_review",
    }
    return candidate


def build_mock_candidates(items, config, generated_at=None):
    """离线生成确定性的项目词汇回退候选。"""
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    candidates = []
    for item in sorted(items, key=lambda row: (row["candidate_type"], row["local_value"])):
        mapping = f"bgpkb:{_camel_case(item['local_value'])}"
        candidates.append(_build_candidate(
            item,
            config,
            provider="mock",
            model="deterministic-mock-v1",
            suggested_mapping=mapping,
            confidence=max(0.75, config["model_policy"].get("minimum_confidence", 0.5)),
            reason="未发现确定性外部词汇映射，建议保留项目受控谓词并提交人工审核。",
            generated_at=generated_at,
        ))
    return candidates


def validate_candidate(candidate, config, items):
    """严格校验候选契约及其与当前批次输入的一致性，返回错误码列表。"""
    if not isinstance(candidate, dict):
        return ["candidate_type"]
    errors = []
    extra_fields = set(candidate) - ALLOWED_CANDIDATE_FIELDS
    if extra_fields:
        errors.append("additional_property")
    for field in sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate)):
        errors.append(f"missing_{field}")

    candidate_type = candidate.get("candidate_type")
    if candidate_type not in {"entity_type", "field", "relation"}:
        errors.append("candidate_type")
    local_value = candidate.get("local_value")
    if not isinstance(local_value, str) or not local_value:
        errors.append("local_value")

    batch_items = {
        (item.get("candidate_type"), item.get("local_value")): item
        for item in items
    }
    item = batch_items.get((candidate_type, local_value))
    if item is None and "local_value" not in errors:
        errors.append("local_value")

    mapping = candidate.get("suggested_mapping")
    if not isinstance(mapping, str) or not CURIE_PATTERN.fullmatch(mapping):
        errors.append("suggested_mapping")
    elif mapping.split(":", 1)[0] not in config["model_policy"].get("allowed_target_prefixes", []):
        errors.append("unknown_prefix")

    source_refs = candidate.get("source_refs")
    if (
        not isinstance(source_refs, list)
        or not source_refs
        or any(not isinstance(ref, str) or not ref for ref in source_refs)
        or len(source_refs) != len(set(source_refs))
    ):
        errors.append("source_refs")
    elif item is not None and source_refs != sorted(item.get("source_refs", [])):
        errors.append("source_refs")

    confidence = candidate.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        errors.append("confidence_type")
    elif not 0 <= confidence <= 1:
        errors.append("confidence_range")
    elif confidence < config["model_policy"].get("minimum_confidence", 0):
        errors.append("minimum_confidence")

    for field in ("reason", "provider", "model", "prompt_version"):
        if not isinstance(candidate.get(field), str) or not candidate.get(field):
            errors.append(field)
    for field in ("evidence_summary", "generated_at"):
        if field in candidate and not isinstance(candidate[field], str):
            errors.append(field)
    if candidate.get("provider") not in config["model_policy"].get("allowed_providers", []):
        errors.append("provider")
    expected_prompt = config["model_policy"].get("prompt_version")
    if candidate.get("prompt_version") != expected_prompt:
        errors.append("prompt_version")
    if candidate.get("status") != "pending_review":
        errors.append("status")

    fingerprint = candidate.get("input_fingerprint")
    if not isinstance(fingerprint, str) or not FINGERPRINT_PATTERN.fullmatch(fingerprint):
        errors.append("input_fingerprint")
    elif item is not None and fingerprint != build_input_fingerprint(item, expected_prompt):
        errors.append("input_fingerprint")

    candidate_id = candidate.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id:
        errors.append("candidate_id")
    elif isinstance(fingerprint, str) and fingerprint not in candidate_id:
        errors.append("candidate_id")
    elif (
        item is not None
        and isinstance(mapping, str)
        and isinstance(fingerprint, str)
        and candidate_id != build_candidate_id(candidate_type, local_value, mapping, fingerprint)
    ):
        errors.append("candidate_id")

    return list(dict.fromkeys(errors))


def _safe_error(index, error_code, validation_errors=None, candidate=None):
    error = {"candidate_index": index, "error_code": error_code}
    if validation_errors:
        error["validation_errors"] = validation_errors
    if isinstance(candidate, dict):
        for field in ("candidate_id", "candidate_type", "local_value"):
            if isinstance(candidate.get(field), str):
                error[field] = candidate[field]
    return error


def normalize_model_suggestion(raw, config, items, provider, model, generated_at):
    """校验模型的语义建议，并由系统补齐不可委托的治理字段。"""
    if not isinstance(raw, dict):
        return None, ["candidate_type"]
    errors = []
    if set(raw) - MODEL_SUGGESTION_FIELDS:
        errors.append("additional_property")
    for field in sorted(MODEL_REQUIRED_FIELDS - set(raw)):
        errors.append(f"missing_{field}")
    batch_items = {
        (item.get("candidate_type"), item.get("local_value")): item
        for item in items
    }
    item = batch_items.get((raw.get("candidate_type"), raw.get("local_value")))
    if item is None:
        errors.append("local_value")
        return None, list(dict.fromkeys(errors))
    if errors:
        return None, list(dict.fromkeys(errors))
    candidate = _build_candidate(
        item,
        config,
        provider=provider,
        model=model,
        suggested_mapping=raw.get("suggested_mapping"),
        confidence=raw.get("confidence"),
        reason=raw.get("reason"),
        generated_at=generated_at,
    )
    candidate["source_refs"] = raw.get("source_refs")
    validation_errors = validate_candidate(candidate, config, items)
    return (candidate if not validation_errors else None), validation_errors


def parse_structured_response(
    content, config, items, provider="deepseek", model="deepseek-chat", generated_at=None
):
    """只接受精确的 ``{"candidates": [...]}`` envelope，并隔离无效项。"""
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return [], [_safe_error(-1, "invalid_json")]
    if not isinstance(payload, dict) or set(payload) != {"candidates"} or not isinstance(payload["candidates"], list):
        return [], [_safe_error(-1, "invalid_envelope")]

    valid = []
    errors = []
    generated_at = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for index, suggestion in enumerate(payload["candidates"]):
        candidate, validation_errors = normalize_model_suggestion(
            suggestion, config, items, provider, model, generated_at
        )
        if validation_errors:
            errors.append(_safe_error(index, "invalid_candidate", validation_errors, suggestion))
        else:
            valid.append(candidate)
    valid.sort(key=lambda row: row["candidate_id"])
    return valid, errors


def _jsonl_text(records):
    return "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records)


def _stage_atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
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


def _replace_outputs(contents):
    staged = []
    try:
        for path, text in contents:
            staged.append((_stage_atomic_text(path, text), path))
        for temporary_path, destination in staged:
            os.replace(temporary_path, destination)
    finally:
        for temporary_path, _ in staged:
            temporary_path.unlink(missing_ok=True)


def build_report(provider, status, item_count, candidate_count, error_count):
    """生成中文候选批次报告。"""
    return "\n".join([
        "# 标准映射候选生成报告",
        "",
        "本报告仅记录待人工审核的语义映射候选；候选不会直接修改主实体、主关系或正式出口。",
        "",
        "## 生成摘要",
        "",
        f"- provider：`{provider}`",
        f"- 状态：`{status}`",
        f"- 未配置本地项：{item_count} 个",
        f"- 待人工审核候选：{candidate_count} 条",
        f"- 校验错误：{error_count} 条",
        "",
        "## 安全边界",
        "",
        "所有有效记录固定为 `pending_review`；模型原始响应、密钥和调用用量不会写入候选或错误数据集。",
        "",
    ])


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_generation(root, config, provider=None, client=None, generated_at=None):
    """运行一个候选批次；DeepSeek 缺密钥时不触碰任何既有输出。"""
    root = Path(root)
    policy = config["model_policy"]
    provider = provider or policy.get("default_provider", "mock")
    if provider not in policy.get("allowed_providers", []) or provider not in {"mock", "deepseek"}:
        raise ValueError(f"Unknown provider: {provider}")
    if provider == "deepseek" and not os.environ.get("DEEPSEEK_API_KEY"):
        return {"status": "skipped", "provider": provider, "reason": "missing_api_key"}

    relationships = _read_jsonl(root / RELATIONSHIPS_RELATIVE_PATH)
    items = collect_unmapped_relations(relationships, config.get("relation_mappings", {}))
    if provider == "mock":
        proposed = build_mock_candidates(items, config, generated_at=generated_at)
        candidates = []
        errors = []
        for index, candidate in enumerate(proposed):
            validation_errors = validate_candidate(candidate, config, items)
            if validation_errors:
                errors.append(_safe_error(index, "invalid_candidate", validation_errors, candidate))
            else:
                candidates.append(candidate)
    else:
        active_client = client or llm_client.DeepSeekClient.from_env()
        model_items = []
        for item in items:
            model_item = dict(item)
            fingerprint = build_input_fingerprint(item, policy["prompt_version"])
            model_item["input_fingerprint"] = fingerprint
            model_item["candidate_id"] = build_candidate_id(
                item["candidate_type"], item["local_value"], "", fingerprint
            )
            model_items.append(model_item)
        response = active_client.generate_standard_mapping_candidates(model_items, policy["prompt_version"])
        if not response.get("ok"):
            candidates = []
            errors = [_safe_error(-1, response.get("error_code", "provider_error"))]
        else:
            candidates, errors = parse_structured_response(
                response.get("content", ""), config, items,
                provider="deepseek", model=response.get("model", "deepseek-chat"),
                generated_at=generated_at,
            )

    candidates.sort(key=lambda row: row["candidate_id"])
    report = build_report(provider, "generated", len(items), len(candidates), len(errors))
    outputs = config["outputs"]
    _replace_outputs([
        (root / outputs["candidates"], _jsonl_text(candidates)),
        (root / outputs["candidate_errors"], _jsonl_text(errors)),
        (root / REPORT_RELATIVE_PATH, report),
    ])
    return {
        "status": "generated",
        "provider": provider,
        "item_count": len(items),
        "candidate_count": len(candidates),
        "error_count": len(errors),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成待人工审核的标准映射候选")
    parser.add_argument("--provider", choices=("mock", "deepseek"))
    parser.add_argument("--root", type=Path, default=paths.PROJECT_ROOT)
    parser.add_argument("--generated-at", help="测试或可复现批次使用的 ISO-8601 时间")
    args = parser.parse_args(argv)
    config = yaml.safe_load((args.root / CONFIG_RELATIVE_PATH).read_text(encoding="utf-8"))
    result = run_generation(
        args.root, config, provider=args.provider, generated_at=args.generated_at
    )
    if result["status"] == "skipped":
        print("跳过 DeepSeek 候选生成：未配置 DEEPSEEK_API_KEY；既有候选文件保持不变。")
    else:
        print(
            f"已生成 {result['candidate_count']} 条待审核候选，"
            f"记录 {result['error_count']} 条校验错误。"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
