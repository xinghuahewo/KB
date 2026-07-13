#!/usr/bin/env python3
"""计算清洗 v2 高风险人工验收指标并生成中文报告。"""

import argparse
import json
from pathlib import Path

from bgpkb import paths
from bgpkb.ingestion.cleaning_v2.evaluation import (
    evaluate_acceptance,
    evaluate_gold_document,
    load_annotations,
    write_acceptance_outputs,
)


DEFAULT_ANNOTATIONS = paths.REVIEW_INPUTS_DIR / "cleaning_v2_gold_annotations.json"
DEFAULT_PARSED_ROOT = paths.CORPUS_DIR / "parsed_v2"
DEFAULT_DATASET = paths.DATASETS_DIR / "cleaning_v2_human_acceptance.json"
DEFAULT_REPORT = paths.GENERATED_DIR / "reports" / "corpus" / "cleaning_v2_human_acceptance_report.md"


def build_report(
    *,
    annotation_path=DEFAULT_ANNOTATIONS,
    parsed_root=DEFAULT_PARSED_ROOT,
    dataset_path=DEFAULT_DATASET,
    report_path=DEFAULT_REPORT,
    expected_document_count=12,
):
    annotations = load_annotations(annotation_path)
    documents = []
    for annotation in annotations:
        parsed_path = Path(parsed_root) / f"{annotation['doc_id']}.json"
        document = json.loads(parsed_path.read_text(encoding="utf-8"))
        documents.append(evaluate_gold_document(annotation, document))
    result = evaluate_acceptance(documents, expected_document_count=expected_document_count)
    result["schema_version"] = "cleaning_v2_human_acceptance_v1"
    result["documents"] = documents
    write_acceptance_outputs(result, dataset_path=dataset_path, report_path=report_path)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="生成清洗 v2 高风险人工验收指标与中文报告")
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--parsed-root", type=Path, default=DEFAULT_PARSED_ROOT)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--expected-document-count", type=int, default=12)
    args = parser.parse_args(argv)
    result = build_report(
        annotation_path=args.annotations,
        parsed_root=args.parsed_root,
        dataset_path=args.dataset,
        report_path=args.report,
        expected_document_count=args.expected_document_count,
    )
    print(json.dumps(result["metrics"], ensure_ascii=False, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
