"""
Token calculation and cost estimation utilities for LLM optimization.
"""
from typing import Dict, Any
import tiktoken

# Pricing per million tokens (Input) as of late 2024 / current industry standards
MODEL_PRICING_PER_MILLION = {
    "GPT-4o (o200k)": 2.50,
    "Claude 3.5 Sonnet": 3.00,
    "Gemini 1.5 Pro": 1.25,
    "Gemini 1.5 Flash": 0.075,
    "GPT-4o-mini": 0.15,
    "DeepSeek V3": 0.14,
}

# Cache tokenizers to avoid re-initialization
_ENCODINGS = {}

def get_encoding(name: str = "o200k_base"):
    if name not in _ENCODINGS:
        try:
            _ENCODINGS[name] = tiktoken.get_encoding(name)
        except Exception:
            _ENCODINGS[name] = tiktoken.get_encoding("cl100k_base")
    return _ENCODINGS[name]

def count_tokens(text: str, encoding_name: str = "o200k_base") -> int:
    """
    Returns accurate token count using tiktoken.
    Falls back to character heuristics (1 token ≈ 4 chars) if tiktoken fails.
    """
    if not text:
        return 0
    try:
        enc = get_encoding(encoding_name)
        return len(enc.encode(text, disallowed_special=()))
    except Exception:
        # Fallback estimation for text
        return max(1, len(text) // 4)

def calculate_savings(raw_tokens: int, optimized_tokens: int) -> Dict[str, Any]:
    """
    Computes savings percentage, tokens saved, and financial impact.
    """
    tokens_saved = max(0, raw_tokens - optimized_tokens)
    reduction_pct = (tokens_saved / raw_tokens * 100) if raw_tokens > 0 else 0.0

    cost_savings = {}
    for model, price_per_m in MODEL_PRICING_PER_MILLION.items():
        saved_per_call = (tokens_saved / 1_000_000) * price_per_m
        cost_savings[model] = {
            "per_single_call": saved_per_call,
            "per_10k_calls": saved_per_call * 10_000,
            "per_100k_calls": saved_per_call * 100_000,
            "per_1m_calls": saved_per_call * 1_000_000,
        }

    return {
        "raw_tokens": raw_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "reduction_percentage": round(reduction_pct, 2),
        "cost_savings": cost_savings,
    }
