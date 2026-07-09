#!/usr/bin/env python3
"""运行私有 Docling v2 可恢复清洗批次。"""

import argparse
import json
import os
from pathlib import Path

import yaml

from bgpkb import paths
from bgpkb.cleaning_v2.batch import BatchRunner
from bgpkb.cleaning_v2.runtime_pipeline import build_stage_handlers
from bgpkb.pipeline import parse_documents


DEFAULT_CONFIG = paths.CONFIG_DIR / "docling_cleaning_v2.yaml"


def discover_sources(input_dir, supported_formats):
    suffixes = {"." + item.lower().lstrip(".") for item in supported_formats}
    return sorted(
        (path for path in Path(input_dir).rglob("*") if path.is_file() and path.suffix.lower() in suffixes),
        key=lambda path: path.as_posix(),
    )


def legacy_fallback(source, doc_id):
    """仅在显式允许时调用现有确定性解析器，并保留原格式证据。"""
    source = Path(source)
    suffix = source.suffix.lower()
    if suffix == ".txt":
        return parse_documents.parse_txt(source, doc_id)
    if suffix == ".html":
        return parse_documents.parse_html(source, doc_id)
    if suffix in {".yaml", ".yml"}:
        return parse_documents.parse_yaml(source, doc_id)
    if suffix == ".pdf":
        document, text, error = parse_documents.parse_pdf(source, doc_id)
        if document is None:
            raise ValueError(error)
        return document, text
    if suffix == ".md":
        text = source.read_text(encoding="utf-8")
        title = next(
            (line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")),
            doc_id,
        )
        return {
            "doc_id": doc_id,
            "source_path": str(source.relative_to(paths.PROJECT_ROOT)),
            "source_format": "markdown",
            "title": title,
            "sections": [{"section_id": "full", "heading": title, "content": text}],
        }, text
    raise ValueError(f"现有解析器不支持后缀: {suffix}")


def _project_path(value):
    path = Path(value)
    return path if path.is_absolute() else paths.PROJECT_ROOT / path


def _runtime_identity(config, evidence_path=None):
    if evidence_path:
        return json.loads(Path(evidence_path).read_text(encoding="utf-8"))
    runtime = dict(config.get("runtime", {}))
    runtime.update(
        {
            "image_digest": os.environ.get("BGP_DOCILING_IMAGE_DIGEST", "unrecorded"),
            "gpu": os.environ.get("BGP_DOCILING_GPU", "unrecorded"),
            "driver": os.environ.get("BGP_DOCILING_DRIVER", "unrecorded"),
        }
    )
    return runtime


def build_parser():
    parser = argparse.ArgumentParser(description="运行离线 Docling v2 文档级可恢复清洗批次")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--input-dir", type=Path, default=paths.RAW_DIR)
    parser.add_argument("--source", type=Path, action="append", default=[])
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--run-root", type=Path)
    parser.add_argument("--runtime-identity", type=Path, help="运行环境证据 JSON")
    parser.add_argument("--run-id")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--allow-fallback", action="store_true", help="仅在已注入 fallback 解析器时生效")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    sources = sorted(set(args.source)) if args.source else discover_sources(
        args.input_dir, config["formats"]["supported"]
    )
    if not sources:
        raise SystemExit("未发现可处理文档")
    output_root = args.output_root or _project_path(config["paths"]["cleaned_blocks"])
    run_root = args.run_root or _project_path(config["paths"]["runs"])
    runtime = _runtime_identity(config, args.runtime_identity)
    handlers = build_stage_handlers(
        config=config, runtime_identity=runtime, fallback_parser=legacy_fallback,
        allow_fallback=args.allow_fallback
    )
    result = BatchRunner(
        output_root=output_root,
        run_root=run_root,
        config=config,
        runtime_identity=runtime,
        handlers=handlers,
    ).run(sources, run_id=args.run_id, resume=args.resume)
    print(
        json.dumps(
            {"run_id": result["run_id"], "summary": result["summary"], "run_dir": str(run_root / result["run_id"])},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
