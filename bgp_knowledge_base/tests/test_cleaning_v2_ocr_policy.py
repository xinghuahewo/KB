import importlib
import importlib.util

import yaml

from bgpkb import paths


MODULE = "bgpkb.cleaning_v2.ocr_policy"
CONFIG = yaml.safe_load((paths.CONFIG_DIR / "docling_cleaning_v2.yaml").read_text(encoding="utf-8"))


def load_module():
    assert importlib.util.find_spec(MODULE) is not None, "自适应 OCR 策略尚未实现"
    return importlib.import_module(MODULE)


def page(**overrides):
    result = {
        "page_number": 1,
        "native_text_chars": 1000,
        "text_coverage": 0.9,
        "image_area_ratio": 0.1,
        "replacement_characters": 0,
    }
    result.update(overrides)
    return result


def test_high_quality_native_page_does_not_run_ocr():
    module = load_module()

    decision = module.decide_ocr(page(), CONFIG)

    assert decision == {"run_ocr": False, "reasons": [], "engine": None, "languages": []}


def test_no_text_image_dominated_and_low_quality_pages_trigger_ocr():
    module = load_module()

    no_text = module.decide_ocr(page(native_text_chars=0, text_coverage=0.0), CONFIG)
    image = module.decide_ocr(page(image_area_ratio=0.9), CONFIG)
    corrupt = module.decide_ocr(page(replacement_characters=2), CONFIG)

    assert "no_native_text" in no_text["reasons"]
    assert "image_dominated" in image["reasons"]
    assert "replacement_characters" in corrupt["reasons"]
    assert all(result["run_ocr"] for result in (no_text, image, corrupt))
    assert no_text["engine"] == "rapidocr"
    assert no_text["languages"] == ["ch", "en"]


def test_text_evidence_preserves_native_and_ocr_with_auditable_selection():
    module = load_module()

    evidence = module.select_text_evidence(
        native_text="BGP 路由",
        ocr_text="BGP 路由安全",
        ocr_confidence=0.96,
        trigger_reasons=["image_dominated"],
        engine="rapidocr",
        languages=["ch", "en"],
        minimum_confidence=0.85,
    )

    assert evidence["native_text"] == "BGP 路由"
    assert evidence["ocr_text"] == "BGP 路由安全"
    assert evidence["selected_text"] == "BGP 路由安全"
    assert evidence["selected_source"] == "ocr"
    assert evidence["review_status"] == "auto_approved"
    assert evidence["trigger_reasons"] == ["image_dominated"]


def test_low_confidence_ocr_is_preserved_but_requires_review():
    module = load_module()

    evidence = module.select_text_evidence(
        native_text="",
        ocr_text="B6P?",
        ocr_confidence=0.42,
        trigger_reasons=["no_native_text"],
        engine="rapidocr",
        languages=["ch", "en"],
        minimum_confidence=0.85,
    )

    assert evidence["ocr_text"] == "B6P?"
    assert evidence["selected_text"] == ""
    assert evidence["selected_source"] == "pending_review"
    assert evidence["review_status"] == "pending_review"
