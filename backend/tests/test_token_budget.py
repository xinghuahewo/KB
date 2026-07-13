import pytest

from bgpkb.domain.token_budget import TokenCounter, parent_budget


def test_parent_budget_uses_dynamic_formulas():
    assert parent_budget("normal", 3000).per_parent == 900
    assert parent_budget("normal", 6000).per_parent == 1200
    assert parent_budget("fact", 6000).per_parent == 1200
    assert parent_budget("procedure", 6000).per_parent == 1200

    assert parent_budget("policy", 4000).per_parent == 2000
    assert parent_budget("policy", 8000).per_parent == 3000
    assert parent_budget("policy", 8000).max_full_parent_sections == 1

    assert parent_budget("global", 4000).per_parent == 1400
    assert parent_budget("global", 8000).per_parent == 2000
    assert parent_budget("global", 6000).max_total_full_tokens == 3600
    assert parent_budget("global", 6000).max_full_parent_sections == 2


def test_parent_budget_rejects_invalid_budget_or_type():
    for value in (0, -1, 8001, True, "6000"):
        with pytest.raises(ValueError):
            parent_budget("normal", value)
    with pytest.raises(ValueError):
        parent_budget("unknown", 6000)


class FakeTokenizer:
    def encode(self, text):
        return text.split()


def test_token_counter_prefers_real_tokenizer_and_marks_estimation():
    real = TokenCounter(tokenizer=FakeTokenizer()).count("one two three")
    estimated = TokenCounter(tokenizer=None).count("abcdef")

    assert real.tokens == 3
    assert real.estimated is False
    assert real.method == "tokenizer"
    assert estimated.tokens >= 2
    assert estimated.estimated is True
    assert estimated.method == "char_estimate"
