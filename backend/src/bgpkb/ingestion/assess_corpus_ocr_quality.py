#!/usr/bin/env python3
"""以可选 Provider 生成与确定性画像隔离的 OCR 质量评估。"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from bgpkb import paths
from bgpkb.ingestion import profile_cleaned_corpus as profiling
from bgpkb.infrastructure.corpus_ocr_provider import (
    DeepSeekCorpusOcrProvider,
    DisabledCorpusOcrProvider,
    MockCorpusOcrProvider,
)


OUTPUT_PATH = paths.DATASETS_DIR / "corpus_ocr_assessments.jsonl"
GENERATED_BY = "src/bgpkb/pipeline/assess_corpus_ocr_quality.py"
RISK_LEVELS = {"low", "medium", "high"}
MODEL_FIELDS = {"risk_level", "reason", "recommendation"}


def sample_document(text, max_chars):
    text = text.strip()
    if len(text) <= max_chars:
        return text
    if max_chars < 3:
        return text[:max_chars]
    head_size = max_chars // 3
    middle_size = max_chars // 3
    tail_size = max_chars - head_size - middle_size
    middle_start = max(0, (len(text) - middle_size) // 2)
    return text[:head_size] + text[middle_start:middle_start + middle_size] + text[-tail_size:]


def input_fingerprint(doc_id, sample, prompt_version):
    payload = json.dumps({
        "doc_id": doc_id,
        "sample": sample,
        "prompt_version": prompt_version,
    }, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _base_record(doc_id, fingerprint, provider, generated_at):
    return {
        "assessment_id": f"corpus_ocr__{doc_id}__{fingerprint}",
        "doc_id": doc_id,
        "input_fingerprint": fingerprint,
        "status": "skipped",
        "risk_level": "unknown",
        "reason": "",
        "recommendation": "",
        "provider": provider.name,
        "model": provider.model,
        "prompt_version": "",
        "generated_at": generated_at,
        "error_code": "",
        "generated_by": GENERATED_BY,
    }


def _parse_response(response):
    if not response.get("ok"):
        return None, response.get("error_code") or "request_failed"
    try:
        payload = json.loads(response.get("content", ""))
    except (TypeError, json.JSONDecodeError):
        return None, "invalid_response"
    if not isinstance(payload, dict) or set(payload) != MODEL_FIELDS:
        return None, "invalid_response"
    if payload.get("risk_level") not in RISK_LEVELS:
        return None, "invalid_response"
    if any(not isinstance(payload.get(field), str) or not payload[field].strip() for field in ("reason", "recommendation")):
        return None, "invalid_response"
    return payload, None


def _preserve_completed(new_record, existing_index):
    key = (new_record["doc_id"], new_record["input_fingerprint"])
    existing = existing_index.get(key)
    if new_record["status"] != "completed" and existing and existing.get("status") == "completed":
        return existing
    return new_record


def assess_documents(documents, config, provider, generated_at=None, existing_records=None):
    generated_at = generated_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    prompt_version = config["prompt_version"]
    existing_index = {
        (row.get("doc_id"), row.get("input_fingerprint")): row
        for row in (existing_records or [])
    }
    processed = 0
    total_chars = 0
    records = []
    for doc_id in sorted(documents):
        sample = sample_document(documents[doc_id], config["max_chars_per_document"])
        fingerprint = input_fingerprint(doc_id, sample, prompt_version)
        record = _base_record(doc_id, fingerprint, provider, generated_at)
        record["prompt_version"] = prompt_version
        if processed >= config["max_documents"] or total_chars + len(sample) > config["max_total_input_chars"]:
            record["error_code"] = "budget_exceeded"
            records.append(_preserve_completed(record, existing_index))
            continue
        processed += 1
        total_chars += len(sample)
        response = provider.assess({
            "doc_id": doc_id,
            "sample": sample,
            "input_fingerprint": fingerprint,
        }, prompt_version)
        payload, error_code = _parse_response(response)
        record["provider"] = response.get("provider") or provider.name
        record["model"] = response.get("model") or provider.model
        if error_code:
            record["status"] = "skipped" if error_code in {
                "missing_api_key", "provider_disabled", "budget_exceeded"
            } else "failed"
            record["error_code"] = error_code
        else:
            record.update(payload)
            record["status"] = "completed"
        records.append(_preserve_completed(record, existing_index))
    return sorted(records, key=lambda row: row["doc_id"])


def load_existing(path=OUTPUT_PATH):
    path = Path(path)
    if not path.exists():
        return []
    records = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"无法解析既有 OCR 评估 {path}:{line_number}: {exc}") from exc
    return records


def load_cleaned_texts(config):
    entries = profiling.load_cleaned_documents(paths.CLEANED_DIR, config, paths.PROJECT_ROOT)
    return {
        doc_id: "\n\n".join(item["content"] for item in rows)
        for doc_id, rows in entries.items()
    }


def write_outputs(records, output_path=OUTPUT_PATH):
    profiles = []
    if profiling.DATASET_PATH.exists():
        profiles = [
            json.loads(line)
            for line in profiling.DATASET_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    contents = [(output_path, profiling._jsonl_text(records))]
    if profiles:
        contents.extend([
            (profiling.DATASET_PATH, profiling._jsonl_text(profiles)),
            (profiling.REPORT_PATH, profiling.render_profile_report(profiles, records)),
        ])
    profiling._atomic_write_many(contents)


def provider_for(name):
    if name == "mock":
        return MockCorpusOcrProvider()
    if name == "deepseek":
        return DeepSeekCorpusOcrProvider()
    if name == "disabled":
        return DisabledCorpusOcrProvider()
    raise ValueError(f"Unsupported OCR provider: {name}")


def run_assessment(provider_name="disabled", generated_at=None):
    config = profiling.load_config()
    assessment_config = config["ocr_assessment"]
    if provider_name not in {"disabled", *assessment_config["allowed_providers"]}:
        raise ValueError(f"Provider 未在配置白名单中: {provider_name}")
    provider = provider_for(provider_name)
    records = assess_documents(
        load_cleaned_texts(config), assessment_config, provider,
        generated_at=generated_at, existing_records=load_existing(),
    )
    write_outputs(records)
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成可选 OCR 质量评估")
    parser.add_argument("--provider", choices=["disabled", "mock", "deepseek"], default="disabled")
    parser.add_argument("--generated-at")
    args = parser.parse_args(argv)
    records = run_assessment(args.provider, generated_at=args.generated_at)
    counts = {status: sum(1 for row in records if row["status"] == status) for status in ("completed", "failed", "skipped")}
    print(f"Wrote {OUTPUT_PATH.relative_to(paths.PROJECT_ROOT)}")
    print(f"completed={counts['completed']} failed={counts['failed']} skipped={counts['skipped']}")


if __name__ == "__main__":
    main()
