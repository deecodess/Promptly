"""Benchmark and quality metrics for Promptly compression."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from time import perf_counter

from compressor import CompressionResult, compress_prompt
from cost_estimator import estimate_savings
from token_counter import count_tokens


IMPORTANT_PATTERNS = [
    r"\bmust\b",
    r"\bshould\b",
    r"\bdo not\b",
    r"\bnever\b",
    r"\balways\b",
    r"\binclude\b",
    r"\bexclude\b",
    r"\bjson\b",
    r"\bapi\b",
    r"\bdeadline\b",
    r"\bbudget\b",
    r"\bsecurity\b",
    r"\bacceptance\b",
    r"\btest(?:s|ing)?\b",
]


@dataclass(frozen=True)
class EvaluationResult:
    prompt_id: str
    category: str
    mode: str
    original_tokens: int
    compressed_tokens: int
    saved_tokens: int
    reduction_pct: float
    cost_before: float
    cost_after: float
    cost_saved: float
    preservation_score: float
    latency_ms: float


def load_prompts(path: Path | str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def preservation_score(original: str, compressed: str) -> float:
    """Estimate whether important constraints survived compression."""
    original_terms = _important_terms(original)
    if not original_terms:
        return 100.0

    compressed_lower = compressed.lower()
    kept = sum(1 for term in original_terms if term in compressed_lower)
    return round(kept / len(original_terms) * 100, 2)


def evaluate_prompt(
    prompt: dict[str, str],
    mode: str = "balanced",
    model_name: str = "gpt-5.4-mini",
) -> EvaluationResult:
    start = perf_counter()
    result: CompressionResult = compress_prompt(prompt["prompt"], mode)
    latency_ms = (perf_counter() - start) * 1000
    costs = estimate_savings(result.original_tokens, result.compressed_tokens, model_name)

    return EvaluationResult(
        prompt_id=prompt["id"],
        category=prompt["category"],
        mode=mode,
        original_tokens=result.original_tokens,
        compressed_tokens=result.compressed_tokens,
        saved_tokens=result.saved_tokens,
        reduction_pct=result.reduction_pct,
        cost_before=costs["cost_before"],
        cost_after=costs["cost_after"],
        cost_saved=costs["cost_saved"],
        preservation_score=preservation_score(prompt["prompt"], result.compressed),
        latency_ms=round(latency_ms, 2),
    )


def benchmark(
    prompts: list[dict[str, str]],
    mode: str = "balanced",
    model_name: str = "gpt-5.4-mini",
) -> dict[str, object]:
    count_tokens("tokenizer warmup")
    results = [evaluate_prompt(prompt, mode, model_name) for prompt in prompts]
    return summarize(results)


def summarize(results: list[EvaluationResult]) -> dict[str, object]:
    if not results:
        return {"summary": {}, "results": []}

    return {
        "summary": {
            "prompt_count": len(results),
            "avg_reduction_pct": round(mean(item.reduction_pct for item in results), 2),
            "avg_preservation_score": round(mean(item.preservation_score for item in results), 2),
            "avg_latency_ms": round(mean(item.latency_ms for item in results), 2),
            "total_tokens_saved": sum(item.saved_tokens for item in results),
            "total_estimated_cost_saved": round(sum(item.cost_saved for item in results), 8),
        },
        "results": [asdict(item) for item in results],
    }


def _important_terms(text: str) -> set[str]:
    lowered = text.lower()
    terms = {match.group(0).lower() for pattern in IMPORTANT_PATTERNS for match in re.finditer(pattern, lowered)}
    quoted = re.findall(r"`([^`]{2,40})`|\"([^\"]{2,40})\"", text)
    for first, second in quoted:
        value = (first or second).strip().lower()
        if value:
            terms.add(value)
    return terms
