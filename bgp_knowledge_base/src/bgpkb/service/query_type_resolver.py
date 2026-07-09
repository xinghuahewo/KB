"""阶段 B 查询类型解析：显式优先、DeepSeek 分类、规则回退。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bgpkb.service.llm_client import DeepSeekClient


ALLOWED_QUERY_TYPES = ("fact", "procedure", "policy", "global", "auto")
RESOLVED_QUERY_TYPES = ("fact", "procedure", "policy", "global")
DEFAULT_PROMPT_VERSION = "query_type_classification_v1"


@dataclass
class QueryTypeResolver:
    client: Any | None = None
    prompt_version: str = DEFAULT_PROMPT_VERSION

    def resolve(self, query: str, requested_query_type: str = "auto") -> dict[str, Any]:
        if requested_query_type not in ALLOWED_QUERY_TYPES:
            raise ValueError("query_type 必须是 fact/procedure/policy/global/auto")
        if requested_query_type != "auto":
            return {
                "requested_query_type": requested_query_type,
                "resolved_query_type": requested_query_type,
                "provider": "explicit",
                "model": "",
                "prompt_version": self.prompt_version,
                "reason": "调用方显式指定 query_type",
                "degraded": False,
                "degraded_reason": None,
            }

        active_client = self.client or DeepSeekClient.from_env()
        response = active_client.classify_query_type(query, self.prompt_version)
        if response.get("ok"):
            resolved = response.get("query_type")
            if resolved in RESOLVED_QUERY_TYPES:
                return {
                    "requested_query_type": "auto",
                    "resolved_query_type": resolved,
                    "provider": response.get("provider", "deepseek"),
                    "model": response.get("model", ""),
                    "prompt_version": self.prompt_version,
                    "reason": response.get("reason", "DeepSeek 结构化分类"),
                    "degraded": False,
                    "degraded_reason": None,
                }
            fallback = _rule_based_type(query)
            return _fallback_payload(
                query=query,
                resolved=fallback,
                prompt_version=self.prompt_version,
                degraded_reason="deepseek_invalid_query_type",
            )
        fallback = _rule_based_type(query)
        return _fallback_payload(
            query=query,
            resolved=fallback,
            prompt_version=self.prompt_version,
            degraded_reason=response.get("error_code") or response.get("error") or "deepseek_unavailable",
        )


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def _rule_based_type(query: str) -> str:
    if _contains_any(query, ("步骤", "流程", "如何", "怎么", "procedure", "step", "workflow", "state machine", "状态机")):
        return "procedure"
    if _contains_any(query, ("总结", "综述", "概览", "全局", "跨章节", "共同", "比较", "global", "overview", "summarize")):
        return "global"
    if _contains_any(query, ("must", "shall", "must not", "rfc", "规范", "条款", "约束", "合规", "policy", "合同")):
        return "policy"
    return "fact"


def _fallback_payload(query: str, resolved: str, prompt_version: str, degraded_reason: str) -> dict[str, Any]:
    return {
        "requested_query_type": "auto",
        "resolved_query_type": resolved,
        "provider": "rule_based",
        "model": "",
        "prompt_version": prompt_version,
        "reason": f"DeepSeek 分类不可用或非法，按可审计规则从查询文本回退；query={query}",
        "degraded": True,
        "degraded_reason": degraded_reason,
    }


def resolve_query_type(
    query: str,
    requested_query_type: str = "auto",
    client: Any | None = None,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
) -> dict[str, Any]:
    return QueryTypeResolver(client=client, prompt_version=prompt_version).resolve(query, requested_query_type)
