"""阶段 B context pack token 预算与计数工具。"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Any


HARD_MAX_TOKENS = 8000


@dataclass(frozen=True)
class TokenCount:
    tokens: int
    estimated: bool
    method: str


@dataclass(frozen=True)
class ParentBudget:
    query_type: str
    context_budget: int
    per_parent: int
    max_full_parent_sections: int = 0
    max_total_full_tokens: int | None = None


class TokenCounter:
    def __init__(self, tokenizer: Any | None = None):
        self.tokenizer = tokenizer

    def count(self, text: str) -> TokenCount:
        if self.tokenizer is not None:
            try:
                return TokenCount(tokens=len(self.tokenizer.encode(text)), estimated=False, method="tokenizer")
            except Exception:
                pass
        return TokenCount(tokens=_conservative_char_estimate(text), estimated=True, method="char_estimate")


def _conservative_char_estimate(text: str) -> int:
    if not text:
        return 0
    cjk_count = len(re.findall(r"[\u3400-\u9fff]", text))
    non_cjk_count = max(0, len(text) - cjk_count)
    return max(1, cjk_count + math.ceil(non_cjk_count / 3))


def _validate_context_budget(context_budget: int) -> int:
    if isinstance(context_budget, bool) or not isinstance(context_budget, int):
        raise ValueError("context_budget 必须是正整数")
    if context_budget <= 0 or context_budget > HARD_MAX_TOKENS:
        raise ValueError("context_budget 必须在 1 到 8000 tokens 之间")
    return context_budget


def parent_budget(query_type: str, context_budget: int) -> ParentBudget:
    budget = _validate_context_budget(context_budget)
    if query_type in {"normal", "fact", "procedure"}:
        return ParentBudget(
            query_type=query_type,
            context_budget=budget,
            per_parent=min(1200, int(budget * 0.30)),
        )
    if query_type == "policy":
        return ParentBudget(
            query_type=query_type,
            context_budget=budget,
            per_parent=min(3000, int(budget * 0.50)),
            max_full_parent_sections=1,
        )
    if query_type == "global":
        return ParentBudget(
            query_type=query_type,
            context_budget=budget,
            per_parent=min(2000, int(budget * 0.35)),
            max_full_parent_sections=2,
            max_total_full_tokens=int(budget * 0.60),
        )
    raise ValueError("query_type 必须是 normal/fact/procedure/policy/global")
