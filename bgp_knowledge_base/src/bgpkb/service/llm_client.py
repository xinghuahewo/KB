import json
import os
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


class DeepSeekClient:
    def __init__(self, api_key="", base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL, timeout=30):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    @classmethod
    def from_env(cls):
        return cls(
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=os.environ.get("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL),
            model=os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
            timeout=int(os.environ.get("DEEPSEEK_TIMEOUT_SECONDS", "30")),
        )

    def build_payload(self, query, context_items):
        evidence_lines = []
        for item in context_items:
            evidence_lines.append(
                "\n".join([
                    f"chunk_id: {item.get('chunk_id', '')}",
                    f"title: {item.get('title', '')}",
                    f"source_ref: {item.get('source_ref', '')}",
                    f"content: {item.get('content_preview', '')}",
                ])
            )
        return {
            "model": self.model,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是 BGP 知识库问答助手。必须基于引用证据回答；"
                        "不得编造来源；不确定时说明证据不足；回答末尾列出引用 chunk_id 和 source_ref。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"问题：{query}\n\n可用证据：\n" + "\n\n---\n\n".join(evidence_lines),
                },
            ],
        }

    def build_standard_mapping_payload(self, items, prompt_version):
        """构建与问答提示隔离的标准映射结构化请求。"""
        required_fields = [
            "candidate_type", "local_value", "suggested_mapping",
            "source_refs", "confidence", "reason",
        ]
        return {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是标准语义映射候选生成器。只输出一个 JSON 对象，唯一顶层字段为 candidates。"
                        "每个候选必须只使用输入中的本地项和来源证据，并包含指定字段；"
                        "不得输出 candidate_id、input_fingerprint、provider、model、prompt_version、"
                        "status 或 generated_at；这些治理字段由系统生成，并把状态固定为 pending_review。"
                        "不得批准候选或修改主数据。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "prompt_version": prompt_version,
                            "required_fields": required_fields,
                            "provider": "deepseek",
                            "model": self.model,
                            "items": items,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                },
            ],
        }

    def build_corpus_ocr_payload(self, item, prompt_version):
        """构建与问答、标准映射隔离的语料 OCR 质量评估请求。"""
        return {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是技术语料 OCR 质量评估器。只输出一个 JSON 对象，且只能包含 "
                        "risk_level、reason、recommendation。risk_level 只能是 low、medium 或 high。"
                        "判断字符断裂、乱码、阅读顺序和疑似 OCR 噪声；不得改写文本或给出治理状态。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({
                        "doc_id": item.get("doc_id", ""),
                        "input_fingerprint": item.get("input_fingerprint", ""),
                        "prompt_version": prompt_version,
                        "sample": item.get("sample", ""),
                    }, ensure_ascii=False, sort_keys=True),
                },
            ],
        }

    def _post_payload(self, payload):
        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return None, {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "http_error",
                "error": f"DeepSeek API returned HTTP {exc.code}.",
            }
        except Exception as exc:
            return None, {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "request_failed",
                "error": str(exc),
            }
        return response_payload, None

    def generate_standard_mapping_candidates(self, items, prompt_version):
        """请求结构化待审核映射候选。"""
        if not self.api_key:
            return {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "missing_api_key",
                "error": "DEEPSEEK_API_KEY is not configured.",
            }
        payload, error = self._post_payload(self.build_standard_mapping_payload(items, prompt_version))
        if error:
            return error
        choices = payload.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        return {
            "ok": bool(content),
            "provider": "deepseek",
            "model": self.model,
            "content": content,
            "raw_usage": payload.get("usage", {}),
        }

    def generate_corpus_ocr_assessment(self, item, prompt_version):
        """请求单篇语料的结构化 OCR 风险建议。"""
        if not self.api_key:
            return {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "missing_api_key",
                "error": "OCR quality provider is not configured.",
            }
        payload, error = self._post_payload(self.build_corpus_ocr_payload(item, prompt_version))
        if error:
            return error
        choices = payload.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        return {
            "ok": bool(content),
            "provider": "deepseek",
            "model": self.model,
            "content": content,
        }

    def generate_answer(self, query, context_items):
        if not self.api_key:
            return {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "missing_api_key",
                "error": "DEEPSEEK_API_KEY is not configured.",
            }

        payload, error = self._post_payload(self.build_payload(query, context_items))
        if error:
            return error

        choices = payload.get("choices", [])
        content = ""
        if choices:
            content = choices[0].get("message", {}).get("content", "")
        return {
            "ok": bool(content),
            "provider": "deepseek",
            "model": self.model,
            "content": content,
            "raw_usage": payload.get("usage", {}),
        }
