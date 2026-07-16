#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

from bgpkb import paths
from bgpkb.domain.evaluation_ownership import load_ownership, release_ownership_status
from bgpkb.domain.rag_quality_gates import evaluate_quality_metrics
from bgpkb.workflows import plan_incremental_run


REPORT = paths.report_path("release_readiness_report")
EVALUATION_EVIDENCE = paths.PUBLISHED_DIR / "rag_release_gate_evidence.json"
EVALUATION_OWNERSHIP = paths.CONFIG_DIR / "rag_eval_ownership.yaml"


def load_json(path):
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def check(name, ok, evidence, detail):
    return {
        "name": name,
        "status": "pass" if ok else "fail",
        "evidence": evidence,
        "detail": detail,
    }


def release_quality_checks(*, ownership_status, evaluation_evidence):
    owner_ready = ownership_status.get("status") == "ready"
    owner_status = "pass" if owner_ready else "skipped_blocking"
    evidence_status = evaluation_evidence.get("status")
    if not evaluation_evidence or evidence_status == "skipped_blocking":
        real_eval_status = "skipped_blocking"
    elif evidence_status == "passed":
        real_eval_status = "pass"
    else:
        real_eval_status = "fail"
    quality_decision = (
        evaluate_quality_metrics(evaluation_evidence.get("metrics", {}))
        if evaluation_evidence
        else None
    )
    quality_status = (
        "skipped_blocking"
        if quality_decision is None
        else ("pass" if quality_decision["status"] == "passed" else "fail")
    )
    return [
        {
            "name": "rag_gold_ownership",
            "status": owner_status,
            "evidence": ["metadata/config/rag_eval_ownership.yaml"],
            "detail": (
                "owner 与 reviewer 已登记。"
                if owner_ready
                else f"{ownership_status.get('reason', 'evaluation_owner_unassigned')}; "
                f"datasets={ownership_status.get('datasets', [])}"
            ),
        },
        {
            "name": "real_rag_evaluation",
            "status": real_eval_status,
            "evidence": ["data/published/rag_release_gate_evidence.json"],
            "detail": (
                f"status={evidence_status}"
                if evaluation_evidence
                else "真实 reranker/DeepSeek 发布评测证据缺失。"
            ),
        },
        {
            "name": "rag_quality_thresholds",
            "status": quality_status,
            "evidence": [
                "metadata/config/rag_quality_gates_v1.yaml",
                "data/published/rag_release_gate_evidence.json",
            ],
            "detail": (
                "真实评测证据缺失，无法计算版本化阈值。"
                if quality_decision is None
                else (
                    f"policy={quality_decision['policy_version']}; "
                    f"failures={[item['rule_id'] for item in quality_decision['failures']]}"
                )
            ),
        },
    ]


def build_checks():
    config = plan_incremental_run.load_config()
    policy = paths.report_policy()
    manifest = load_json(paths.PUBLISHED_DIR / "manifest.json")
    integrity = load_json(paths.PUBLISHED_DIR / "integrity_summary.json")
    readiness = load_json(paths.PUBLISHED_DIR / "readiness_summary.json")
    bge = load_json(paths.PUBLISHED_DIR / "bge_m3_embedding_manifest.json")
    ownership_status = release_ownership_status(load_ownership(EVALUATION_OWNERSHIP))
    evaluation_evidence = load_json(EVALUATION_EVIDENCE)
    steps = config.get("steps", [])

    script_paths = [
        paths.PROJECT_ROOT / step["command"].replace("python3 -m ", "src/").replace(".", "/")
        for step in steps
        if step.get("command", "").startswith("python3 -m ")
    ]
    script_paths = [Path(str(path) + ".py") for path in script_paths]
    missing_scripts = [paths.rel(path) for path in script_paths if not path.exists()]
    unsafe_steps = [
        step["id"]
        for step in steps
        if step.get("safety", {}).get("network") != "disabled"
        or step.get("safety", {}).get("llm") != "disabled"
        or step.get("safety", {}).get("writes_main_knowledge") is not False
    ]

    checks = [
        check(
            "pipeline_dependency_config",
            config.get("version") == "knowledge_update_v1" and not missing_scripts and not unsafe_steps,
            ["metadata/config/pipeline_dependencies.yaml"],
            f"缺失脚本={missing_scripts}; 不安全步骤={unsafe_steps}",
        ),
        check(
            "report_policy_registration",
            {"release_notes", "release_readiness_report", "incremental_run_plan_report"} <= set(policy),
            ["metadata/config/report_policy.yaml"],
            "发布说明、发布就绪检查和增量计划报告已登记。",
        ),
        check(
            "published_manifest",
            manifest.get("corpus_version") == "v2" and manifest.get("hierarchy_integrity") == "pass",
            ["data/published/manifest.json"],
            f"corpus_version={manifest.get('corpus_version')}; hierarchy={manifest.get('hierarchy_integrity')}",
        ),
        check(
            "published_integrity",
            integrity.get("status") == "pass",
            ["data/published/integrity_summary.json", "data/reports/gates/published_integrity_report.md"],
            f"status={integrity.get('status', 'missing')}",
        ),
        check(
            "readiness_summary",
            readiness.get("status") in {"ready_deterministic", "ready", "pass"},
            ["data/published/readiness_summary.json", "data/reports/gates/readiness_report.md"],
            f"status={readiness.get('status', 'missing')}",
        ),
        check(
            "bge_m3_index",
            bge.get("status") == "complete" and bge.get("real_model_execution") is True,
            ["data/published/bge_m3_embedding_manifest.json"],
            f"status={bge.get('status', 'missing')}; provider={bge.get('provider', '')}",
        ),
        check(
            "release_notes",
            (paths.PUBLISHED_DIR / "release_notes.md").exists(),
            ["data/published/release_notes.md"],
            "发布说明存在。",
        ),
    ]
    checks.extend(
        release_quality_checks(
            ownership_status=ownership_status,
            evaluation_evidence=evaluation_evidence,
        )
    )
    return checks


def render_report(checks):
    ok = all(item["status"] == "pass" for item in checks)
    lines = [
        "# 发布就绪检查报告",
        "",
        "## 范围",
        "",
        "本检查入口面向 CI，限定为非联网、非 LLM、非主知识写入的发布前检查。",
        "它只读取配置和已发布制品，生成中文门禁报告。",
        "",
        "## 摘要",
        "",
        f"- 运行时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 总体状态：{'通过' if ok else '失败'}",
        f"- 检查数：{len(checks)}",
        "",
        "## 检查结果",
        "",
        "| 检查 | 状态 | 证据 | 说明 |",
        "| --- | --- | --- | --- |",
    ]
    for item in checks:
        evidence = "<br>".join(f"`{path}`" for path in item["evidence"])
        lines.append(f"| `{item['name']}` | {item['status']} | {evidence} | {item['detail']} |")
    lines.extend([
        "",
        "## 运行边界",
        "",
        "- 不下载来源。",
        "- 不调用 embedding、reranker 或 LLM 服务。",
        "- 不写入 `data/knowledge/entities`、`data/knowledge/relationships` 或人工复核输入。",
    ])
    return "\n".join(lines).rstrip() + "\n"


def main():
    checks = build_checks()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(checks), encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(paths.PROJECT_ROOT)}")
    if any(item["status"] != "pass" for item in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
