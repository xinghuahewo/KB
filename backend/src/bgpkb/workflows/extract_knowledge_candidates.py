"""显式启用、只生成待审核记录的知识候选抽取工作流。"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
from typing import Any

import yaml

from bgpkb import paths
from bgpkb.domain.knowledge_candidates import normalize_model_suggestion
from bgpkb.infrastructure.llm_client import DeepSeekClient


CONFIG_PATH = paths.CONFIG_DIR / "knowledge_candidate_extraction_v1.yaml"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _jsonl_text(records: list[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )


def _atomic_replace_outputs(outputs: list[tuple[Path, str]]) -> None:
    staged: list[tuple[Path, Path]] = []
    try:
        for destination, text in outputs:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=destination.parent,
                prefix=f".{destination.name}.",
                delete=False,
            ) as handle:
                temporary = Path(handle.name)
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((temporary, destination))
        for temporary, destination in staged:
            os.replace(temporary, destination)
    finally:
        for temporary, _ in staged:
            temporary.unlink(missing_ok=True)


def _deterministic_suggestions(
    evidence: list[dict[str, Any]], provider_config: dict[str, Any]
) -> list[dict[str, Any]]:
    suggestions = []
    for term_config in provider_config.get("terms", []):
        term = str(term_config.get("term", "")).strip()
        if not term:
            continue
        matching_evidence_ids = sorted(
            record["evidence_id"]
            for record in evidence
            if term.casefold()
            in str(record.get("content") or record.get("retrieval_text") or "").casefold()
        )
        if not matching_evidence_ids:
            continue
        payload = {
            "type": "entity",
            "entity_kind": str(term_config.get("entity_kind", "concept")),
            "canonical_name": term,
        }
        aliases = sorted(
            {
                str(alias).strip()
                for alias in term_config.get("aliases", [])
                if str(alias).strip()
            }
        )
        if aliases:
            payload["aliases"] = aliases
        suggestions.append(
            {
                "candidate_type": "entity",
                "payload": payload,
                "evidence_ids": matching_evidence_ids,
                "confidence": 1.0,
                "reason": f"版本化确定性术语规则命中 `{term}`。",
            }
        )
    return suggestions


def _parse_llm_response(content: Any) -> tuple[list[Any], list[dict[str, Any]]]:
    try:
        payload = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        return [], [{"candidate_index": -1, "error_code": "invalid_json"}]
    if (
        not isinstance(payload, dict)
        or set(payload) != {"candidates"}
        or not isinstance(payload["candidates"], list)
    ):
        return [], [{"candidate_index": -1, "error_code": "invalid_envelope"}]
    return payload["candidates"], []


def _validate_evidence_batch(evidence: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for record in evidence:
        evidence_id = record.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise ValueError("evidence_id 缺失")
        if evidence_id in evidence_by_id:
            raise ValueError(f"evidence_id 重复：{evidence_id}")
        evidence_by_id[evidence_id] = record
    return evidence_by_id


def run_candidate_extraction(
    root: Path,
    config: dict[str, Any],
    *,
    provider: str | None = None,
    client: Any = None,
) -> dict[str, Any]:
    """运行候选抽取；跳过状态不会读取模型或覆盖任何既有输出。"""
    root = Path(root)
    provider = provider or config.get("default_provider", "disabled")
    if provider == "disabled":
        return {
            "status": "skipped",
            "provider": provider,
            "reason": "provider_not_enabled",
        }
    provider_config = config.get("providers", {}).get(provider)
    if provider_config is None or provider not in {"deterministic", "deepseek"}:
        raise ValueError(f"未知知识候选 provider：{provider}")

    if provider == "deepseek":
        api_key_env = provider_config.get("api_key_env", "DEEPSEEK_API_KEY")
        if not os.environ.get(api_key_env):
            return {
                "status": "skipped",
                "provider": provider,
                "reason": "missing_api_key",
            }

    evidence = _read_jsonl(root / config["inputs"]["evidence"])
    evidence_by_id = _validate_evidence_batch(evidence)
    model_revision = provider_config["model_revision"]
    prompt_version = provider_config["prompt_version"]
    errors: list[dict[str, Any]] = []

    if provider == "deterministic":
        suggestions = _deterministic_suggestions(evidence, provider_config)
    else:
        active_client = client or DeepSeekClient.from_env()
        response = active_client.generate_knowledge_candidates(evidence, prompt_version)
        if not response.get("ok"):
            return {
                "status": "skipped",
                "provider": provider,
                "reason": response.get("error_code", "model_unavailable"),
            }
        model_revision = response.get("model") or model_revision
        suggestions, errors = _parse_llm_response(response.get("content"))

    candidates = []
    for index, suggestion in enumerate(suggestions):
        candidate, validation_errors = normalize_model_suggestion(
            suggestion,
            evidence_by_id=evidence_by_id,
            provider=provider,
            model_revision=model_revision,
            prompt_version=prompt_version,
        )
        if validation_errors:
            errors.append(
                {
                    "candidate_index": index,
                    "error_code": "invalid_candidate",
                    "validation_errors": validation_errors,
                }
            )
        else:
            candidates.append(candidate)

    candidates.sort(key=lambda record: record["candidate_id"])
    errors.sort(key=lambda record: (record.get("candidate_index", -1), record["error_code"]))
    report = {
        "version": config["version"],
        "status": "generated",
        "provider": provider,
        "model_revision": model_revision,
        "prompt_version": prompt_version,
        "evidence_count": len(evidence),
        "candidate_count": len(candidates),
        "error_count": len(errors),
        "message": "仅生成待人工审核候选，未修改正式知识或检索资格。",
    }
    outputs = config["outputs"]
    _atomic_replace_outputs(
        [
            (root / outputs["candidates"], _jsonl_text(candidates)),
            (root / outputs["candidate_errors"], _jsonl_text(errors)),
            (
                root / outputs["report"],
                json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            ),
        ]
    )
    return {
        "status": "generated",
        "provider": provider,
        "candidate_count": len(candidates),
        "error_count": len(errors),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成证据绑定的待审核知识候选")
    parser.add_argument("--provider", choices=("deterministic", "deepseek"))
    parser.add_argument("--root", type=Path, default=paths.PROJECT_ROOT)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    result = run_candidate_extraction(
        args.root, config, provider=args.provider
    )
    if result["status"] == "skipped":
        print(f"知识候选抽取已跳过：{result['reason']}；既有候选保持不变。")
    else:
        print(
            f"生成 {result['candidate_count']} 条待审核知识候选，"
            f"隔离 {result['error_count']} 条无效输出。"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
