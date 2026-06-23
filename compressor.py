"""Deterministic prompt compression for local, reproducible benchmarks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from token_counter import count_tokens, token_delta


MODE_RATIOS = {
    "conservative": 0.72,
    "balanced": 0.52,
    "aggressive": 0.38,
}

MODE_TOKEN_TARGETS = {
    "conservative": 0.66,
    "balanced": 0.52,
    "aggressive": 0.40,
}

FILLER_PATTERNS = [
    r"\bplease note that\b",
    r"\bit is important to note that\b",
    r"\bin order to\b",
    r"\bas a matter of fact\b",
    r"\bkind of\b",
    r"\bsort of\b",
    r"\bbasically\b",
    r"\breally\b",
    r"\bvery\b",
    r"\bjust\b",
    r"\bactually\b",
    r"\bin general\b",
]

PROTECTED_PATTERNS = [
    r"\bmust\b",
    r"\bshould\b",
    r"\bneed(?:s|ed)?\b",
    r"\brequire(?:ment|ments|d|s)?\b",
    r"\bconstraint(?:s)?\b",
    r"\bdo not\b",
    r"\bdon't\b",
    r"\bnever\b",
    r"\balways\b",
    r"\bonly\b",
    r"\binclude\b",
    r"\bexclude\b",
    r"\boutput\b",
    r"\bformat\b",
    r"\bjson\b",
    r"\bapi\b",
    r"\bendpoint\b",
    r"\berror\b",
    r"\bsecurity\b",
    r"\bprivacy\b",
    r"\bdeadline\b",
    r"\bbudget\b",
    r"\bacceptance\b",
    r"\btest(?:s|ing)?\b",
]

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class CompressionResult:
    original: str
    compressed: str
    mode: str
    original_tokens: int
    compressed_tokens: int
    saved_tokens: int
    reduction_pct: float


def normalize_text(text: str) -> str:
    """Normalize spacing while preserving paragraph/list boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_filler(text: str) -> str:
    """Remove low-information phrases that inflate prompts."""
    cleaned = text
    for pattern in FILLER_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r" {2,}", " ", cleaned)
    return cleaned.strip()


def split_units(text: str) -> list[str]:
    """Split prompt text into sentences/list-like units."""
    units: list[str] = []
    for raw_line in normalize_text(text).splitlines():
        line = raw_line.strip(" -\t")
        if not line:
            continue
        if len(line) <= 90 or re.match(r"^(\d+\.|[-*])\s+", raw_line.strip()):
            units.append(line)
            continue
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", line)
        units.extend(part.strip() for part in parts if part.strip())
    return units


def dedupe_units(units: list[str]) -> list[str]:
    """Remove repeated units using normalized lowercase text."""
    seen: set[str] = set()
    unique: list[str] = []
    for unit in units:
        key = re.sub(r"\W+", " ", unit).lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(unit)
    return unique


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{3,}", text.lower())
    return {word for word in words if word not in STOPWORDS}


def _is_protected(unit: str) -> bool:
    return any(re.search(pattern, unit, flags=re.IGNORECASE) for pattern in PROTECTED_PATTERNS)


def _score_unit(unit: str, index: int, total: int, global_keywords: set[str]) -> float:
    unit_keywords = _keywords(unit)
    score = 0.0
    score += min(len(unit_keywords & global_keywords), 10) * 1.5
    score += 8.0 if _is_protected(unit) else 0.0
    score += 2.0 if index in {0, total - 1} else 0.0
    score += 1.0 if re.search(r"\b\d+(?:\.\d+)?%?\b", unit) else 0.0

    word_count = len(unit.split())
    if 8 <= word_count <= 32:
        score += 2.0
    elif word_count > 48:
        score -= 2.0
    return score


def _compress_long_unit(unit: str) -> str:
    replacements = [
        (r"\bI want you to\b", ""),
        (r"\bCan you\b", ""),
        (r"\bCould you\b", ""),
        (r"\bmake sure to\b", "ensure"),
        (r"\bwith regard to\b", "about"),
        (r"\bdue to the fact that\b", "because"),
        (r"\bat this point in time\b", "now"),
    ]
    shortened = unit
    for pattern, replacement in replacements:
        shortened = re.sub(pattern, replacement, shortened, flags=re.IGNORECASE)
    return remove_filler(shortened)


def compress_prompt(text: str, mode: str = "balanced") -> CompressionResult:
    """Compress a prompt with deterministic extractive ranking."""
    if mode not in MODE_RATIOS:
        raise ValueError(f"Unsupported compression mode: {mode}")

    original = normalize_text(text)
    if not original:
        return CompressionResult("", "", mode, 0, 0, 0, 0.0)

    units = dedupe_units(split_units(remove_filler(original)))
    if not units:
        compressed = remove_filler(original)
    elif len(units) <= 2:
        compressed = " ".join(_compress_long_unit(unit) for unit in units)
    else:
        global_keywords = _keywords(" ".join(units))
        scored = [
            (_score_unit(unit, index, len(units), global_keywords), index, _compress_long_unit(unit))
            for index, unit in enumerate(units)
        ]
        keep_count = max(1, round(len(scored) * MODE_RATIOS[mode]))
        protected = {index for _, index, unit in scored if _is_protected(unit)}
        ranked = sorted(scored, key=lambda item: (-item[0], item[1]))
        selected = set(list(protected)[: max(1, keep_count)])
        for _, index, _ in ranked:
            if len(selected) >= keep_count:
                break
            selected.add(index)

        kept_units = [unit for _, index, unit in scored if index in selected]
        compressed = " ".join(kept_units)
        compressed = _trim_to_target(original, compressed, mode)

    compressed = normalize_text(compressed)
    metrics = token_delta(original, compressed)
    return CompressionResult(
        original=original,
        compressed=compressed,
        mode=mode,
        original_tokens=int(metrics["original_tokens"]),
        compressed_tokens=int(metrics["compressed_tokens"]),
        saved_tokens=int(metrics["saved_tokens"]),
        reduction_pct=float(metrics["reduction_pct"]),
    )


def _trim_to_target(original: str, compressed: str, mode: str) -> str:
    """Trim lowest priority non-protected units until a mode token target is met."""
    target_tokens = max(1, int(count_tokens(original) * MODE_TOKEN_TARGETS[mode]))
    units = split_units(compressed)
    if count_tokens(compressed) <= target_tokens or len(units) <= 1:
        return compressed

    protected_indexes = {index for index, unit in enumerate(units) if _is_protected(unit)}
    removable = [index for index in range(len(units)) if index not in protected_indexes]
    while removable and count_tokens(" ".join(units)) > target_tokens:
        remove_index = removable.pop()
        units.pop(remove_index)
        removable = [index for index in range(len(units)) if index not in protected_indexes]

    return " ".join(units)
