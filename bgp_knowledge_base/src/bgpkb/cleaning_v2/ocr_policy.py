"""基于页面证据的确定性自适应 OCR 决策。"""


def decide_ocr(page, config):
    policy = config.get("ocr", {})
    reasons = []
    native_chars = page.get("native_text_chars", 0)
    if native_chars == 0:
        reasons.append("no_native_text")
    elif native_chars < policy.get("minimum_native_text_chars", 32):
        reasons.append("low_native_text")
    if page.get("text_coverage", 0.0) < policy.get("minimum_text_coverage", 0.15):
        reasons.append("low_text_coverage")
    if page.get("image_area_ratio", 0.0) >= policy.get("image_area_ratio_trigger", 0.65):
        reasons.append("image_dominated")
    if page.get("replacement_characters", 0) > policy.get("maximum_native_replacement_characters", 0):
        reasons.append("replacement_characters")
    reasons = list(dict.fromkeys(reasons))
    run_ocr = bool(reasons)
    return {
        "run_ocr": run_ocr,
        "reasons": reasons,
        "engine": "rapidocr" if run_ocr else None,
        "languages": list(policy.get("languages", [])) if run_ocr else [],
    }


def select_text_evidence(
    *,
    native_text,
    ocr_text,
    ocr_confidence,
    trigger_reasons,
    engine,
    languages,
    minimum_confidence,
):
    if trigger_reasons and ocr_text and ocr_confidence >= minimum_confidence:
        selected_text = ocr_text
        selected_source = "ocr"
        review_status = "auto_approved"
    elif trigger_reasons:
        selected_text = native_text if native_text and ocr_confidence >= minimum_confidence else ""
        selected_source = "native" if selected_text else "pending_review"
        review_status = "pending_review"
    else:
        selected_text = native_text
        selected_source = "native"
        review_status = "auto_approved"
    return {
        "native_text": native_text,
        "ocr_text": ocr_text,
        "selected_text": selected_text,
        "selected_source": selected_source,
        "ocr_confidence": ocr_confidence,
        "trigger_reasons": list(trigger_reasons),
        "engine": engine,
        "languages": list(languages),
        "review_status": review_status,
    }
