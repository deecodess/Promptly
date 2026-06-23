"""Cost estimation helpers for prompt input tokens."""

from __future__ import annotations

import json
from pathlib import Path


PRICING_FILE = Path(__file__).with_name("model_pricing.json")


def load_pricing(path: Path | str = PRICING_FILE) -> dict[str, dict[str, float | str]]:
    """Load model pricing from JSON config."""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def available_models(path: Path | str = PRICING_FILE) -> list[str]:
    """Return configured model names in display order."""
    return list(load_pricing(path).keys())


def estimate_input_cost(tokens: int, model_name: str, path: Path | str = PRICING_FILE) -> float:
    """Estimate input-token cost in USD for a configured model."""
    pricing = load_pricing(path)
    if model_name not in pricing:
        raise KeyError(f"Unknown model: {model_name}")

    rate = float(pricing[model_name]["input_per_million"])
    return tokens / 1_000_000 * rate


def estimate_savings(original_tokens: int, compressed_tokens: int, model_name: str) -> dict[str, float]:
    """Return before/after cost and savings for input tokens."""
    before = estimate_input_cost(original_tokens, model_name)
    after = estimate_input_cost(compressed_tokens, model_name)
    saved = max(0.0, before - after)
    savings_pct = (saved / before * 100) if before else 0.0

    return {
        "cost_before": before,
        "cost_after": after,
        "cost_saved": saved,
        "cost_savings_pct": round(savings_pct, 2),
    }


def format_usd(value: float) -> str:
    """Format small API costs without rounding them down to zero."""
    if value == 0:
        return "$0.00"
    if value < 0.01:
        return f"${value:.6f}"
    return f"${value:.4f}"
