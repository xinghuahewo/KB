import hashlib
import importlib
import importlib.util

import pytest
import yaml

from bgpkb import paths


MODULE = "bgpkb.cleaning_v2.preflight"
CONFIG = yaml.safe_load((paths.CONFIG_DIR / "docling_cleaning_v2.yaml").read_text(encoding="utf-8"))


def load_module():
    assert importlib.util.find_spec(MODULE) is not None, "清洗 v2 文档预检尚未实现"
    return importlib.import_module(MODULE)


@pytest.mark.parametrize(
    ("filename", "content", "expected_format"),
    [
        ("sample.txt", b"BGP route validation\n", "txt"),
        ("sample.html", b"<html><body>BGP</body></html>", "html"),
        ("sample.yaml", b"title: BGP\nversion: 1\n", "yaml"),
    ],
)
def test_preflight_non_pdf_formats_are_hashed_without_mutation(tmp_path, filename, content, expected_format):
    module = load_module()
    source = tmp_path / filename
    source.write_bytes(content)

    result = module.preflight_document(source, CONFIG)

    assert source.read_bytes() == content
    assert result["format"] == expected_format
    assert result["source_sha256"] == hashlib.sha256(content).hexdigest()
    assert result["page_count"] is None
    assert result["recommended_route"] == "native"


def test_pdf_preflight_routes_only_risky_pages_to_adaptive_ocr(tmp_path):
    module = load_module()
    source = tmp_path / "mixed.pdf"
    source.write_bytes(b"%PDF-1.7\nfixture")

    def inspect_pdf(_path):
        return {
            "encrypted": False,
            "pages": [
                {"page_number": 1, "native_text_chars": 1200, "text_coverage": 0.9, "image_area_ratio": 0.1, "replacement_characters": 0},
                {"page_number": 2, "native_text_chars": 0, "text_coverage": 0.0, "image_area_ratio": 0.98, "replacement_characters": 0},
            ],
        }

    result = module.preflight_document(source, CONFIG, pdf_inspector=inspect_pdf)

    assert result["page_count"] == 2
    assert result["pages"][0]["ocr_recommended"] is False
    assert result["pages"][1]["ocr_recommended"] is True
    assert "no_native_text" in result["pages"][1]["ocr_reasons"]
    assert result["recommended_route"] == "adaptive_ocr"


def test_encrypted_and_corrupt_pdfs_are_quarantined(tmp_path):
    module = load_module()
    encrypted = tmp_path / "encrypted.pdf"
    corrupt = tmp_path / "corrupt.pdf"
    encrypted.write_bytes(b"%PDF-1.7 encrypted")
    corrupt.write_bytes(b"not-a-pdf")

    encrypted_result = module.preflight_document(
        encrypted,
        CONFIG,
        pdf_inspector=lambda _path: {"encrypted": True, "pages": []},
    )
    corrupt_result = module.preflight_document(corrupt, CONFIG)

    assert encrypted_result["recommended_route"] == "quarantine"
    assert "encrypted_pdf" in encrypted_result["issues"]
    assert corrupt_result["recommended_route"] == "quarantine"
    assert "invalid_pdf_signature" in corrupt_result["issues"]


def test_processing_fingerprint_is_stable_and_invalidated_by_config():
    module = load_module()
    arguments = ("a" * 64, "sha256:" + "b" * 64, ["c" * 64, "d" * 64], "e" * 64)

    first = module.processing_fingerprint(*arguments)

    assert first == module.processing_fingerprint(*arguments)
    assert first != module.processing_fingerprint(*arguments[:-1], "f" * 64)
    assert first.startswith("cleaning_v2_")
