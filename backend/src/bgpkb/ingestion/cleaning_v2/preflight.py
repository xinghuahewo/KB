"""在解析前生成只读文档画像、OCR 建议和幂等输入指纹。"""

import hashlib
import json
from pathlib import Path

from bgpkb.ingestion.cleaning_v2.ocr_policy import decide_ocr


GENERATED_BY = "src/bgpkb/cleaning_v2/preflight.py"


def sha256_path(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def processing_fingerprint(source_sha256, image_digest, model_hashes, config_hash):
    payload = {
        "source_sha256": source_sha256,
        "image_digest": image_digest,
        "model_hashes": sorted(model_hashes),
        "config_hash": config_hash,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "cleaning_v2_" + hashlib.sha256(encoded).hexdigest()


def _default_pdf_inspector(path):
    data = Path(path).read_bytes()
    if not data.startswith(b"%PDF-"):
        raise ValueError("invalid_pdf_signature")
    return {
        "encrypted": b"/Encrypt" in data,
        "pages": [],
    }


def preflight_document(path, config, pdf_inspector=None):
    path = Path(path)
    suffix = path.suffix.lower().lstrip(".")
    format_name = "yaml" if suffix in {"yaml", "yml"} else suffix
    result = {
        "doc_id": path.stem,
        "source_path": str(path),
        "source_sha256": sha256_path(path),
        "format": format_name,
        "size_bytes": path.stat().st_size,
        "encrypted": False,
        "page_count": None,
        "pages": [],
        "recommended_route": "native",
        "issues": [],
        "generated_by": GENERATED_BY,
    }
    if format_name != "pdf":
        return result

    inspector = pdf_inspector or _default_pdf_inspector
    try:
        evidence = inspector(path)
    except Exception as exc:
        issue = str(exc) or exc.__class__.__name__
        result["issues"].append(issue)
        result["recommended_route"] = "quarantine"
        return result

    result["encrypted"] = bool(evidence.get("encrypted"))
    if result["encrypted"]:
        result["issues"].append("encrypted_pdf")
        result["recommended_route"] = "quarantine"
        return result

    pages = []
    for page in evidence.get("pages", []):
        decision = decide_ocr(page, config)
        pages.append(
            {
                **page,
                "ocr_recommended": decision["run_ocr"],
                "ocr_reasons": decision["reasons"],
                "ocr_engine": decision["engine"],
                "ocr_languages": decision["languages"],
            }
        )
    result["pages"] = pages
    result["page_count"] = len(pages)
    if any(page["ocr_recommended"] for page in pages):
        result["recommended_route"] = "adaptive_ocr"
    return result
