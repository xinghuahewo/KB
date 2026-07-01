"""把预检、Docling 适配、清洗与校验组装为批处理阶段。"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from functools import lru_cache
import tempfile

from .batch import BatchFailure
from .contracts import atomic_write_json, validate_blocks
from .docling_adapter import DoclingParseError, parse_with_explicit_fallback
from .preflight import preflight_document
from .transformations import CleaningRule, apply_rules, build_review_queue, publishable_blocks


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _default_docling_converter():
    """每个批次进程只加载一次模型，避免逐文档重复占用 GPU。"""
    try:
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption

        pipeline_options = PdfPipelineOptions()
        pipeline_options.artifacts_path = Path(
            os.environ.get("DOCLING_ARTIFACTS_PATH", "/opt/docling/models")
        )
        pipeline_options.do_ocr = True
        pipeline_options.ocr_options = RapidOcrOptions(backend="torch")
        pipeline_options.generate_picture_images = True
        pipeline_options.images_scale = 1.0
        return DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
        )
    except Exception as exc:
        raise DoclingParseError(str(exc) or exc.__class__.__name__) from exc


def _default_docling_parser(source: Path):
    """仅在容器实际解析时加载 Docling，避免本地工具链被重依赖绑定。"""
    try:
        converter = _default_docling_converter()
        result = converter.convert(source)
        return result.document.export_to_dict()
    except Exception as exc:
        raise DoclingParseError(str(exc) or exc.__class__.__name__) from exc


def _gpu_peak_memory_mb():
    try:
        import torch

        if torch.cuda.is_available():
            return float(torch.cuda.max_memory_allocated()) / (1024 * 1024)
    except (ImportError, RuntimeError):
        pass
    return 0.0


def materialize_picture_assets(payload, assets_dir, doc_id):
    """把 Docling 内嵌 data URI 落成稳定图片文件，并回填适配字段。"""
    del doc_id
    assets_dir = Path(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)
    extension_by_mime = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    for index, picture in enumerate(payload.get("pictures", []), start=1):
        image = picture.get("image") or {}
        if image.get("path") and image.get("sha256"):
            continue
        uri = str(image.get("uri", ""))
        if not uri.startswith("data:") or "," not in uri:
            continue
        header, encoded = uri.split(",", 1)
        mime = str(image.get("mimetype") or header.removeprefix("data:").split(";", 1)[0])
        try:
            content = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error):
            continue
        extension = extension_by_mime.get(mime, ".bin")
        filename = f"picture-{index:04d}{extension}"
        target = assets_dir / filename
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=assets_dir, prefix=f".{filename}.", suffix=".tmp", delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        except Exception:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise
        picture["image"] = {
            "path": f"assets/{filename}",
            "sha256": hashlib.sha256(content).hexdigest(),
        }


def _lossless_rules(config):
    configured = config.get("rules", {}).get("lossless", ["unicode_whitespace"])
    return [CleaningRule(str(rule_id), "1", "lossless") for rule_id in configured]


def build_stage_handlers(
    *, config: dict, runtime_identity: dict, docling_parser=None,
    fallback_parser=None, allow_fallback: bool = False,
):
    """创建可注入解析器、可离线测试的五阶段处理器。"""
    parse_docling = docling_parser or _default_docling_parser

    def preflighted(context):
        record = preflight_document(context.source_path, config.get("ocr", {}))
        record["doc_id"] = context.doc_id
        atomic_write_json(context.temporary_dir / "preflight.json", record)
        if record["recommended_route"] == "quarantine":
            raise BatchFailure("invalid_content", ",".join(record["issues"]) or "预检失败")
        return {"page_count": record.get("page_count") or 0, "ocr_page_count": 0}

    def parsed(context):
        preflight = _load_json(context.temporary_dir / "preflight.json")
        source_meta = {
            "doc_id": context.doc_id,
            "source_path": str(context.source_path),
            "source_sha256": preflight["source_sha256"],
        }
        if fallback_parser is None:
            def unavailable_fallback(_source, _doc_id):
                raise RuntimeError("未配置 fallback 解析器")
            selected_fallback = unavailable_fallback
        else:
            selected_fallback = fallback_parser
        document = parse_with_explicit_fallback(
            context.source_path, source_meta, runtime_identity, config,
            parse_docling, selected_fallback, allow_fallback=allow_fallback,
            payload_preprocessor=lambda payload: materialize_picture_assets(
                payload, context.temporary_dir / "assets", context.doc_id
            ),
        )
        atomic_write_json(context.temporary_dir / "parsed_document.json", document)
        if document["document_status"] == "quarantined":
            raise BatchFailure("invalid_content", document.get("fallback_reason") or "Docling 解析失败")
        page_count = len({row.get("page_number") for row in document["blocks"] if row.get("page_number") is not None})
        ocr_pages = len({row.get("page_number") for row in document["blocks"] if row.get("quality", {}).get("ocr_used")})
        return {
            "page_count": page_count,
            "ocr_page_count": ocr_pages,
            "gpu_peak_memory_mb": _gpu_peak_memory_mb(),
            "fallback_used": document.get("parser_mode") == "fallback",
            "output_counts": {"parsed_blocks": len(document["blocks"]), "assets": len(document["assets"])},
        }

    def normalized(context):
        parsed_document = _load_json(context.temporary_dir / "parsed_document.json")
        governed = apply_rules(parsed_document["blocks"], _lossless_rules(config), config)
        cleaned_document = dict(parsed_document)
        cleaned_document["blocks"] = governed["cleaned_blocks"]
        cleaned_document["transformations"] = governed["transformations"]
        cleaned_document["review_items"] = governed["review_items"]
        cleaned_document["document_status"] = "normalized"
        atomic_write_json(context.temporary_dir / "cleaned_document.json", cleaned_document)
        atomic_write_json(context.temporary_dir / "transformations.json", governed["transformations"])
        return {
            "output_counts": {
                "cleaned_blocks": len(cleaned_document["blocks"]),
                "transformations": len(governed["transformations"]),
            }
        }

    def validated(context):
        document = _load_json(context.temporary_dir / "cleaned_document.json")
        errors = validate_blocks(document["blocks"])
        review_queue = build_review_queue(document["blocks"])
        publishable = publishable_blocks(document["blocks"])
        validation = {
            "valid": not errors and bool(publishable),
            "errors": errors,
            "review_queue": review_queue,
            "publishable_block_count": len(publishable),
        }
        atomic_write_json(context.temporary_dir / "validation.json", validation)
        atomic_write_json(context.temporary_dir / "review_queue.json", review_queue)
        if errors:
            raise BatchFailure("schema_error", ";".join(errors))
        if not publishable:
            raise BatchFailure("governance_error", "没有可发布的 approved Block")
        return {"output_counts": {"review_items": len(review_queue)}}

    def approved(context):
        document = _load_json(context.temporary_dir / "cleaned_document.json")
        document["document_status"] = "approved"
        atomic_write_json(context.temporary_dir / "cleaned_document.json", document)
        return {"output_counts": {"approved_blocks": len(document["blocks"])}}

    return {
        "preflighted": preflighted,
        "parsed": parsed,
        "normalized": normalized,
        "validated": validated,
        "approved": approved,
    }
