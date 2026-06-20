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

    def generate_answer(self, query, context_items):
        if not self.api_key:
            return {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "missing_api_key",
                "error": "DEEPSEEK_API_KEY is not configured.",
            }

        request = urllib.request.Request(
            self.base_url,
            data=json.dumps(self.build_payload(query, context_items), ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "http_error",
                "error": f"DeepSeek API returned HTTP {exc.code}.",
            }
        except Exception as exc:
            return {
                "ok": False,
                "provider": "deepseek",
                "model": self.model,
                "error_code": "request_failed",
                "error": str(exc),
            }

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
