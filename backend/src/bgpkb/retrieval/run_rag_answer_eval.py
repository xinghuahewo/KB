import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.infrastructure import llm_client
from bgpkb.retrieval import rag_answer  # noqa: E402


QUESTIONS_PATH = paths.DATASETS_DIR / "rag_answer_eval_questions.jsonl"
RESULTS_PATH = paths.DATASETS_DIR / "rag_answer_eval_results.jsonl"
REPORT_PATH = paths.report_path("rag_answer_eval_report")
TERM_ALIASES = {
    "hijack": ["hijack", "hijacking", "劫持"],
    "route leak": ["route leak", "route leaks", "路由泄露"],
    "flap": ["flap", "flapping", "震荡"],
    "semantics": ["semantics", "semantic", "语义"],
}


class StructureOnlyClient:
    model = "structure-check"
    model_revision = "structure-check-v1"
    provider = "offline_structure_check"
    evaluation_mode = "development_structure_only"
    release_eligible = False

    def generate_answer(self, query, context_items):
        evidence_text = " ".join(
            " ".join([
                item.get("title", ""),
                item.get("source_ref", ""),
                item.get("content_preview", ""),
            ])
            for item in context_items
        )
        return {
            "ok": True,
            "provider": "offline_structure_check",
            "model": self.model,
            "content": f"结构检查回答：{query}\n{evidence_text[:1000]}",
            "raw_usage": {},
        }

    def generate_grounded_answer(self, query, evidence, context_groups, repair=None):
        """仅验证结构的离线客户端；不得替代真实回答发布评测。"""
        if not evidence:
            grounded = {
                "schema_version": "grounded_answer_v1",
                "answer": "",
                "claims": [],
                "evidence_ids": [],
                "confidence": 0.0,
                "insufficient_evidence": True,
            }
        else:
            evidence_ids = [item["evidence_id"] for item in evidence]
            evidence_text = " ".join(
                " ".join([
                    item.get("title", ""),
                    item.get("source_ref", ""),
                    item.get("content", ""),
                ])
                for item in evidence
            )
            answer = f"结构检查回答：{query}\n{evidence_text[:1000]}"
            grounded = {
                "schema_version": "grounded_answer_v1",
                "answer": answer,
                "claims": [{
                    "schema_version": "grounded_claim_v1",
                    "claim_type": "factual",
                    "text": answer,
                    "evidence_ids": evidence_ids,
                    "confidence": 1.0,
                }],
                "evidence_ids": evidence_ids,
                "confidence": 1.0,
                "insufficient_evidence": False,
            }
        return {
            "ok": True,
            "provider": "offline_structure_check",
            "model": self.model,
            "content": json.dumps(grounded, ensure_ascii=False, sort_keys=True),
            "raw_usage": {},
        }


def load_questions(path=QUESTIONS_PATH):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def text_contains(text, term):
    haystack = text.lower()
    candidates = TERM_ALIASES.get(term.lower(), [term])
    return any(candidate.lower() in haystack for candidate in candidates)


def citation_source_refs(payload):
    return [item.get("source_ref", "") for item in payload.get("citations", [])]


def context_chunk_ids(payload):
    pack = payload.get("context_pack", {})
    unit_chunk_ids = {
        chunk_id
        for unit in pack.get("context_units", [])
        for chunk_id in unit.get("included_chunk_ids", [])
    }
    if unit_chunk_ids:
        return unit_chunk_ids
    return {item.get("chunk_id", "") for item in pack.get("results", [])}


def score_payload(question, payload):
    failed = []
    answer = payload.get("answer", "")
    citations = payload.get("citations", [])
    expected_status = question["expected_status"]

    if payload.get("answer_status") != expected_status:
        failed.append("answer_status_mismatch")
    if expected_status == "answered" and not answer:
        failed.append("missing_answer")
    if expected_status == "answered" and not citations:
        failed.append("missing_citations")
    if expected_status == "no_evidence" and payload.get("generated"):
        failed.append("unexpected_generation")
    if expected_status == "no_evidence" and citations:
        failed.append("unexpected_citations")

    chunk_ids = context_chunk_ids(payload)
    if any(citation.get("chunk_id", "") not in chunk_ids for citation in citations):
        failed.append("citation_not_in_context_pack")

    missing_terms = [term for term in question.get("must_have_terms", []) if not text_contains(answer, term)]
    if missing_terms:
        failed.append("must_have_terms_missing")
    forbidden_hits = [term for term in question.get("forbidden_terms", []) if text_contains(answer, term)]
    if forbidden_hits:
        failed.append("forbidden_terms_hit")

    expected_refs = question.get("expected_source_refs", [])
    source_refs = citation_source_refs(payload)
    matched_expected_refs = [
        expected for expected in expected_refs
        if any(expected in source_ref for source_ref in source_refs)
    ]

    guardrails = payload.get("guardrails", {})
    if guardrails.get("read_only") is not True:
        failed.append("guardrail_read_only_missing")
    if guardrails.get("local_model_enabled") is not False:
        failed.append("guardrail_local_model_boundary_missing")
    if guardrails.get("allows_knowledge_base_writes") is not False:
        failed.append("guardrail_write_boundary_missing")
    if guardrails.get("requires_citations") is not True:
        failed.append("guardrail_citation_requirement_missing")

    return {
        "question_id": question["question_id"],
        "query": question["query"],
        "expected_status": expected_status,
        "answer_status": payload.get("answer_status", ""),
        "decision": "pass" if not failed else "fail",
        "failed_checks": failed,
        "generated": payload.get("generated", False),
        "citation_count": len(citations),
        "citations_from_context_pack": "citation_not_in_context_pack" not in failed,
        "must_have_terms_missing": missing_terms,
        "forbidden_terms_hit": forbidden_hits,
        "expected_source_refs": expected_refs,
        "matched_expected_source_refs": matched_expected_refs,
        "model_provider": payload.get("model_provider", ""),
        "model": payload.get("model", ""),
        "answer_preview": answer[:260],
        "guardrails": guardrails,
    }


def _validate_release_client(client, *, required_model, required_model_revision):
    if getattr(client, "release_eligible", True) is not True:
        raise ValueError("结构检查客户端不能替代真实 reranker/DeepSeek 发布评测")
    if getattr(client, "provider", None) != "deepseek":
        raise ValueError("发布回答评测必须使用 DeepSeek provider")
    if not required_model or getattr(client, "model", None) != required_model:
        raise ValueError("发布回答评测的 DeepSeek model 与固定基线不一致")
    actual_revision = getattr(client, "model_revision", None)
    if not required_model_revision or actual_revision != required_model_revision:
        raise ValueError("发布回答评测缺少或不匹配精确 model revision")


def run_evaluation(
    questions=None,
    client=None,
    limit=5,
    *,
    release_mode=False,
    required_model=None,
    required_model_revision=None,
):
    selected = questions if questions is not None else load_questions()
    active_client = client or (
        llm_client.DeepSeekClient.from_env()
        if os.environ.get("DEEPSEEK_API_KEY")
        else StructureOnlyClient()
    )
    if release_mode:
        _validate_release_client(
            active_client,
            required_model=required_model,
            required_model_revision=required_model_revision,
        )
    results = []
    for question in selected:
        payload = rag_answer.answer_question(question["query"], limit=limit, client=active_client)
        scored = score_payload(question, payload)
        scored["model_revision"] = getattr(active_client, "model_revision", "")
        results.append(scored)
    return results


def summarize(results):
    total = len(results)
    passed = sum(1 for item in results if item["decision"] == "pass")
    answered = [item for item in results if item["expected_status"] == "answered"]
    no_evidence = [item for item in results if item["expected_status"] == "no_evidence"]
    citation_covered = sum(1 for item in answered if item["citation_count"] > 0)
    no_evidence_rejected = sum(1 for item in no_evidence if item["answer_status"] == "no_evidence" and not item["generated"])
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "citation_coverage": round(citation_covered / len(answered), 4) if answered else 1.0,
        "no_evidence_rejection_rate": round(no_evidence_rejected / len(no_evidence), 4) if no_evidence else 1.0,
        "citations_from_context_pack": all(item["citations_from_context_pack"] for item in results),
    }


def render_report(results, api_key_configured, evaluation_mode=None):
    summary = summarize(results)
    selected_mode = evaluation_mode or (
        "real_deepseek" if api_key_configured else "development_structure_only"
    )
    lines = [
        "# 阶段 4.3 RAG 答案评测报告",
        "",
        "## 摘要",
        "",
        f"- 生成时间：{datetime.now().replace(microsecond=0).isoformat()}",
        f"- DeepSeek API key 配置：{'是' if api_key_configured else '否'}",
        f"- 评测模式：`{selected_mode}`",
        "- 密钥记录：未写入报告、数据集或仓库。",
        f"- 问题数：{summary['total']}",
        f"- 通过数：{summary['passed']}",
        f"- 失败数：{summary['failed']}",
        f"- 引用覆盖率：{summary['citation_coverage']:.2%}",
        f"- 无证据拒答率：{summary['no_evidence_rejection_rate']:.2%}",
        f"- citations 全部来自 context_pack：{'是' if summary['citations_from_context_pack'] else '否'}",
        "",
        "## 边界确认",
        "",
        "- 当前设备不运行本地模型。",
        "- 评测只调用 RAG Answer 编排，不写回实体、关系、chunk 或发布包。",
        "- 无证据问题必须拒答。",
        "- `DEEPSEEK_API_KEY` 只从环境变量读取。",
        "",
        "## 逐题结果",
        "",
        "| ID | 查询 | 预期 | 实际 | 结论 | 引用数 | 失败检查 |",
        "| --- | --- | --- | --- | --- | ---: | --- |",
    ]
    if selected_mode == "development_structure_only":
        lines[12:12] = [
            "- 发布资格：否；本报告仅用于开发结构检查。",
            "- 结构检查不能替代真实 reranker/DeepSeek 发布评测。",
        ]
    for item in results:
        failed = ", ".join(item["failed_checks"]) if item["failed_checks"] else ""
        lines.append(
            f"| {item['question_id']} | {item['query']} | {item['expected_status']} | "
            f"{item['answer_status']} | {item['decision']} | {item['citation_count']} | {failed} |"
        )
    lines.extend(["", "## 需人工复核", ""])
    failures = [item for item in results if item["decision"] != "pass"]
    if failures:
        for item in failures:
            lines.append(f"- `{item['question_id']}`：{', '.join(item['failed_checks'])}")
    else:
        lines.append("- 无。")
    return "\n".join(lines).rstrip() + "\n"


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run RAG answer quality evaluation.")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    api_key_configured = bool(os.environ.get("DEEPSEEK_API_KEY"))
    results = run_evaluation(limit=args.limit)
    write_jsonl(RESULTS_PATH, results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_report(results, api_key_configured), encoding="utf-8")
    print(f"Wrote {paths.rel(RESULTS_PATH)}")
    print(f"Wrote {paths.rel(REPORT_PATH)}")
    return 1 if summarize(results)["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
