#!/usr/bin/env python3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "pipeline_report.md"

STEPS = [
    ("解析原始文档", "parse_documents.py"),
    ("构建知识片段", "build_chunks.py"),
    ("抽取案例观察值", "extract_case_observations.py"),
    ("构建来源处理状态", "build_source_processing_status.py"),
    ("构建来源缺口队列", "build_source_gap_queue.py"),
    ("构建实体复核队列", "build_entity_review_queue.py"),
    ("构建实体来源证据索引", "build_entity_source_evidence.py"),
    ("构建实体人工复核包", "build_entity_review_packets.py"),
    ("构建权威来源补充需求", "build_authoritative_source_requirements.py"),
    ("构建下一步行动队列", "build_next_action_queue.py"),
    ("构建 LLM 跳过记录", "build_llm_processing_skip_report.py"),
    ("构建案例观察值复核指南", "build_case_observation_guides.py"),
    ("构建人工复核工作簿", "build_human_review_workbook.py"),
    ("构建人工复核决策输入模板", "build_human_review_decision_template.py"),
    ("校验人工复核决策输入", "build_human_review_input_validation.py"),
    ("审计人工复核决策", "build_human_review_decision_audit.py"),
    ("预览人工复核决策应用", "apply_human_review_decisions.py"),
    ("构建人工复核进度", "build_human_review_progress.py"),
    ("构建人工复核证据摘录", "build_human_review_evidence_extracts.py"),
    ("构建人工复核会话队列", "build_human_review_session_queue.py"),
    ("构建人工复核会话状态", "build_human_review_session_status.py"),
    ("构建人工复核逐字段清单", "build_human_review_field_checklist.py"),
    ("构建人工复核来源矩阵", "build_human_review_source_matrix.py"),
    ("构建人工复核任务板", "build_human_review_task_board.py"),
    ("构建人工复核交接清单", "build_human_review_handoff.py"),
    ("构建人工复核会话决策模板", "build_human_review_session_decision_templates.py"),
    ("构建人工复核会话指南", "build_human_review_session_guides.py"),
    ("构建人工复核指南", "build_human_review_guides.py"),
    ("构建术语表", "build_glossary.py"),
    ("构建发布知识库", "build_published_knowledge_base.py"),
    ("构建语义标识前置层", "build_semantic_identity.py"),
    ("构建 LLM 候选增强框架", "build_llm_candidate_enrichment.py"),
    ("构建 RAG 检索索引框架", "build_rag_indexes.py"),
    ("构建 SQLite 知识库", "build_sqlite_knowledge_base.py"),
    ("构建查询样例报告", "build_query_examples.py"),
    ("校验发布完整性", "build_published_integrity_report.py"),
    ("构建知识库就绪度报告", "build_readiness_report.py"),
    ("构建数据字典", "build_data_dictionary.py"),
    ("构建覆盖报告", "build_coverage_report.py"),
    ("构建数据管理能力报告", "build_data_management_report.py"),
    ("构建生命周期治理报告", "build_lifecycle_report.py"),
    ("构建语义质量治理报告", "build_semantic_quality_report.py"),
    ("构建 RAG 就绪框架报告", "build_rag_readiness_report.py"),
    ("运行 RAG 答案质量评测", "run_rag_answer_eval.py"),
    ("构建 RAG 答案失败样本分析", "build_rag_answer_failure_analysis.py"),
    ("构建制品清单", "build_artifact_manifest.py"),
    ("运行质量检查", "quality_check.py"),
]


def run_step(label, script_name):
    script = ROOT / "scripts" / script_name
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    elapsed = time.monotonic() - start
    return {
        "label": label,
        "script": f"scripts/{script_name}",
        "returncode": result.returncode,
        "elapsed": elapsed,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def fenced(text):
    if not text:
        return "无"
    return f"```text\n{text}\n```"


def write_report(results):
    ok = all(item["returncode"] == 0 for item in results)
    lines = [
        "# 确定性流水线报告",
        "",
        "## 摘要",
        "",
        f"- 运行时间：{datetime.now().isoformat(timespec='seconds')}",
        f"- 工作目录：`{ROOT}`",
        f"- 步骤数：{len(results)}",
        f"- 总体状态：{'通过' if ok else '失败'}",
        "",
        "## 步骤结果",
        "",
        "| 步骤 | 脚本 | 状态 | 耗时秒 |",
        "| --- | --- | --- | ---: |",
    ]
    for item in results:
        status = "通过" if item["returncode"] == 0 else f"失败({item['returncode']})"
        lines.append(f"| {item['label']} | `{item['script']}` | {status} | {item['elapsed']:.2f} |")

    lines.extend(["", "## 输出详情", ""])
    for item in results:
        lines.extend([
            f"### {item['label']}",
            "",
            f"- 脚本：`{item['script']}`",
            f"- 返回码：{item['returncode']}",
            "",
            "标准输出：",
            "",
            fenced(item["stdout"]),
            "",
            "标准错误：",
            "",
            fenced(item["stderr"]),
            "",
        ])
    REPORT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main():
    results = []
    for label, script_name in STEPS:
        result = run_step(label, script_name)
        results.append(result)
        if result["returncode"] != 0:
            break
    write_report(results)
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    if any(item["returncode"] != 0 for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
