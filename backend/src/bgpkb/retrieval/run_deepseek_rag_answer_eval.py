import argparse
import json
import os
import sys
from pathlib import Path

from bgpkb import paths


ROOT = paths.PROJECT_ROOT
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bgpkb.retrieval import run_rag_answer_eval  # noqa: E402
from bgpkb.infrastructure import llm_client  # noqa: E402


RESULTS_PATH = paths.DATASETS_DIR / "deepseek_rag_answer_eval_results.jsonl"
REPORT_PATH = paths.report_path("deepseek_rag_answer_eval_report")


def write_jsonl(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def write_blocking_skip(reason, results_path=RESULTS_PATH, report_path=REPORT_PATH):
    record = {
        "schema_version": "rag_evaluation_blocking_v1",
        "status": "skipped_blocking",
        "reason": str(reason),
        "evaluation": "deepseek_answer",
    }
    write_jsonl(Path(results_path), [record])
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(
        "\n".join([
            "# DeepSeek 真实回答评测阻断报告",
            "",
            "- 状态：`skipped_blocking`",
            f"- 原因：{reason}",
            "- 发布影响：阻断；不得以结构检查或 mock 结果替代。",
            "",
        ]),
        encoding="utf-8",
    )
    return record


def run_real_eval(
    questions=None,
    client=None,
    results_path=RESULTS_PATH,
    report_path=REPORT_PATH,
    limit=5,
    *,
    required_model=None,
    required_model_revision=None,
):
    active_client = client or llm_client.DeepSeekClient.from_env()
    if not getattr(active_client, "api_key", "fake-key-for-tests"):
        raise SystemExit("DEEPSEEK_API_KEY is required for real DeepSeek evaluation.")
    resolved_model = (
        required_model
        if required_model is not None
        else os.environ.get("DEEPSEEK_MODEL", getattr(active_client, "model", ""))
    )
    resolved_revision = (
        required_model_revision
        if required_model_revision is not None
        else os.environ.get("DEEPSEEK_MODEL_REVISION", "")
    )
    selected = questions if questions is not None else run_rag_answer_eval.load_questions()
    results = run_rag_answer_eval.run_evaluation(
        questions=selected,
        client=active_client,
        limit=limit,
        release_mode=True,
        required_model=resolved_model,
        required_model_revision=resolved_revision,
    )
    write_jsonl(Path(results_path), results)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    report = run_rag_answer_eval.render_report(results, api_key_configured=True)
    report = report.replace("# 阶段 4.3 RAG 答案评测报告", "# 阶段 4.4 DeepSeek 真实批量评测报告", 1)
    Path(report_path).write_text(report, encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description="Run real DeepSeek batch evaluation for RAG answers.")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    try:
        results = run_real_eval(limit=args.limit)
    except (SystemExit, ValueError) as exc:
        write_blocking_skip(exc, results_path=RESULTS_PATH, report_path=REPORT_PATH)
        print(f"Wrote {paths.rel(RESULTS_PATH)}")
        print(f"Wrote {paths.rel(REPORT_PATH)}")
        return 1
    print(f"Wrote {paths.rel(RESULTS_PATH)}")
    print(f"Wrote {paths.rel(REPORT_PATH)}")
    failures = sum(1 for item in results if item["decision"] != "pass")
    if failures:
        print(f"Real DeepSeek evaluation has {failures} failed items; inspect the report.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
