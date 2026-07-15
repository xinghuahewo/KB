"""用于 ADR 决策的小型、确定性近重复策略比较器。"""

from __future__ import annotations

import hashlib
import re
import unicodedata


STRATEGIES = ("exact_hash", "token_shingles", "minhash", "simhash")


def _normalize(text: str, *, mask_numbers: bool = False) -> str:
    value = unicodedata.normalize("NFKC", text).casefold()
    tokens = re.findall(r"[\w]+", value, flags=re.UNICODE)
    if mask_numbers:
        tokens = ["<number>" if token.isdigit() else token for token in tokens]
    return " ".join(tokens)


def _shingles(text: str, size: int = 3) -> set[str]:
    tokens = _normalize(text, mask_numbers=True).split()
    if len(tokens) < size:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[index:index + size]) for index in range(len(tokens) - size + 1)}


def _jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def _minhash_signature(values: set[str], permutations: int = 64) -> tuple[int, ...]:
    if not values:
        return tuple(0 for _ in range(permutations))
    return tuple(
        min(int.from_bytes(hashlib.sha256(f"{seed}\0{value}".encode()).digest()[:8], "big") for value in values)
        for seed in range(permutations)
    )


def _minhash_similarity(left: set[str], right: set[str]) -> float:
    left_signature = _minhash_signature(left)
    right_signature = _minhash_signature(right)
    return sum(a == b for a, b in zip(left_signature, right_signature, strict=True)) / len(left_signature)


def _simhash(text: str, bits: int = 64) -> int:
    tokens = _normalize(text, mask_numbers=True).split()
    weights = [0] * bits
    for token in tokens:
        value = int.from_bytes(hashlib.sha256(token.encode()).digest()[: bits // 8], "big")
        for index in range(bits):
            weights[index] += 1 if value & (1 << index) else -1
    fingerprint = 0
    for index, weight in enumerate(weights):
        if weight >= 0:
            fingerprint |= 1 << index
    return fingerprint


def _simhash_similarity(left: str, right: str, bits: int = 64) -> float:
    distance = (_simhash(left, bits) ^ _simhash(right, bits)).bit_count()
    return 1 - distance / bits


def _decision(pair: dict, strategy: str) -> tuple[bool, float]:
    left = str(pair["left"])
    right = str(pair["right"])
    same_source = pair.get("same_source") is True
    if strategy == "exact_hash":
        score = float(_normalize(left) == _normalize(right))
        return same_source and score == 1.0, score
    left_shingles = _shingles(left)
    right_shingles = _shingles(right)
    if strategy == "token_shingles":
        score = _jaccard(left_shingles, right_shingles)
        return same_source and score >= 0.8, score
    if strategy == "minhash":
        score = _minhash_similarity(left_shingles, right_shingles)
        return same_source and score >= 0.8, score
    if strategy == "simhash":
        score = _simhash_similarity(left, right)
        return same_source and score >= 0.85, score
    raise ValueError(f"未知去重策略：{strategy}")


def evaluate_strategies(pairs: list[dict]) -> dict:
    report = {"pair_count": len(pairs), "strategies": {}}
    expected_duplicates = sum(pair.get("should_collapse") is True for pair in pairs)
    expected_independent = len(pairs) - expected_duplicates
    for strategy in STRATEGIES:
        decisions = {}
        false_collapses = 0
        missed_duplicates = 0
        for pair in pairs:
            predicted, score = _decision(pair, strategy)
            expected = pair.get("should_collapse") is True
            false_collapses += predicted and not expected
            missed_duplicates += not predicted and expected
            decisions[pair["id"]] = {"collapse": predicted, "score": round(score, 6)}
        report["strategies"][strategy] = {
            "pair_count": len(pairs),
            "false_collapse_count": false_collapses,
            "false_collapse_rate": false_collapses / expected_independent if expected_independent else 0.0,
            "missed_duplicate_count": missed_duplicates,
            "missed_duplicate_rate": missed_duplicates / expected_duplicates if expected_duplicates else 0.0,
            "decisions": decisions,
        }
    return report


def initial_policy(report: dict, *, near_duplicate_approved: bool) -> dict:
    if not report.get("strategies"):
        raise ValueError("策略报告不能为空")
    return {
        "hard_gate": "exact_hash",
        "near_duplicate_mode": "approved" if near_duplicate_approved else "diagnostic_only",
        "cross_source_collapse": False,
    }
