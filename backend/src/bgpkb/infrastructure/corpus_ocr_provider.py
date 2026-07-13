"""可替换的语料 OCR 质量评估 Provider。"""

import json

from bgpkb.infrastructure.llm_client import DeepSeekClient


class DisabledCorpusOcrProvider:
    name = "disabled"
    model = "none"

    def assess(self, item, prompt_version):
        return {
            "ok": False,
            "provider": self.name,
            "model": self.model,
            "error_code": "provider_disabled",
            "error": "Provider is disabled.",
        }


class MockCorpusOcrProvider:
    name = "mock"
    model = "deterministic-ocr-quality-mock-v1"

    def assess(self, item, prompt_version):
        sample = item.get("sample", "")
        replacement_count = sample.count("�")
        control_count = sum(1 for char in sample if ord(char) < 32 and char not in "\n\r\t")
        if replacement_count or control_count:
            risk = "high"
            reason = "抽样中存在替换字符或控制字符。"
            recommendation = "人工核对原文解析与 OCR 结果。"
        elif len(sample.strip()) < 40:
            risk = "medium"
            reason = "抽样文本较短，无法充分判断 OCR 连续性。"
            recommendation = "人工确认正文是否完整。"
        else:
            risk = "low"
            reason = "抽样字符连续，未发现稳定 mock 规则可识别的 OCR 风险。"
            recommendation = "无需额外处理；可按常规比例抽样复核。"
        return {
            "ok": True,
            "provider": self.name,
            "model": self.model,
            "content": json.dumps({
                "risk_level": risk,
                "reason": reason,
                "recommendation": recommendation,
            }, ensure_ascii=False, sort_keys=True),
        }


class DeepSeekCorpusOcrProvider:
    name = "deepseek"

    def __init__(self, api_key=None, client=None):
        self.client = client or (
            DeepSeekClient.from_env() if api_key is None else DeepSeekClient(api_key=api_key)
        )
        self.model = self.client.model

    def assess(self, item, prompt_version):
        return self.client.generate_corpus_ocr_assessment(item, prompt_version)

