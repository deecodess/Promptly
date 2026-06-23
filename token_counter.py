"""Token counting utilities with a tiktoken-backed implementation and fallback."""

from __future__ import annotations

import re
from functools import lru_cache


DEFAULT_ENCODING = "cl100k_base"


@lru_cache(maxsize=8)
def _get_tiktoken_encoding(encoding_name: str):
    try:
        import tiktoken
    except ImportError:
        return None

    try:
        return tiktoken.get_encoding(encoding_name)
    except Exception:
        try:
            return tiktoken.get_encoding(DEFAULT_ENCODING)
        except Exception:
            return None


def count_tokens(text: str, encoding_name: str = DEFAULT_ENCODING) -> int:
    """Return a token count for text.

    Uses tiktoken when installed. The fallback is deterministic and close enough
    for tests/benchmarking on machines where dependencies have not been installed.
    """
    if not text:
        return 0

    encoding = _get_tiktoken_encoding(encoding_name)
    if encoding is not None:
        return len(encoding.encode(text))

    pieces = re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE)
    long_word_penalty = sum(max(0, len(piece) - 8) // 6 for piece in pieces)
    return len(pieces) + long_word_penalty


def token_delta(original: str, compressed: str, encoding_name: str = DEFAULT_ENCODING) -> dict[str, float | int]:
    """Compute token savings metrics for two prompts."""
    original_tokens = count_tokens(original, encoding_name)
    compressed_tokens = count_tokens(compressed, encoding_name)
    saved_tokens = max(0, original_tokens - compressed_tokens)
    reduction_pct = (saved_tokens / original_tokens * 100) if original_tokens else 0.0

    return {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "saved_tokens": saved_tokens,
        "reduction_pct": round(reduction_pct, 2),
    }
