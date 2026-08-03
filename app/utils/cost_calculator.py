"""Real-time token usage and cost estimator."""

from __future__ import annotations

# Approximate cost per 1M tokens (input, output) in USD
# Updated August 2026 — best-effort pricing
_COST_TABLE: dict[str, tuple[float, float]] = {
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "openai/gpt-5": (1.25, 10.00),
    "openai/o3-mini": (1.10, 4.40),
    "openai/o4-mini": (1.10, 4.40),
    "anthropic/claude-opus-4-20250514": (15.00, 75.00),
    "anthropic/claude-sonnet-4-20250514": (3.00, 15.00),
    "anthropic/claude-haiku-3-5-20241022": (0.80, 4.00),
    "gemini/gemini-2.5-pro-exp-03-25": (1.25, 10.00),
    "gemini/gemini-2.0-flash-exp": (0.10, 0.40),
    "openrouter/qwen/qwen-2.5-72b-instruct": (0.90, 0.90),
    "mistral/mistral-large-latest": (2.00, 6.00),
    "mistral/codestral-latest": (1.00, 3.00),
    "groq/llama-3.3-70b-versatile": (0.59, 0.79),
    "deepseek/deepseek-chat": (0.27, 1.10),
    "deepseek/deepseek-coder": (0.14, 0.28),
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """
    Estimate the cost of a request in USD.

    Args:
        model: Full provider/model string (e.g. 'openai/gpt-4o').
        prompt_tokens: Number of input tokens.
        completion_tokens: Number of output tokens.

    Returns:
        Estimated cost in USD.
    """
    input_price, output_price = _COST_TABLE.get(
        model, (0.0, 0.0)
    )

    if input_price == 0.0 and output_price == 0.0:
        return 0.0

    input_cost = (prompt_tokens / 1_000_000) * input_price
    output_cost = (completion_tokens / 1_000_000) * output_price

    return round(input_cost + output_cost, 8)


def count_tokens_approx(text: str) -> int:
    """
    Approximate token count without loading tiktoken.
    Rule of thumb: ~4 chars per token for English text.
    """
    if not text:
        return 0
    return max(1, len(text) // 4)


# Load tiktoken for accurate counting if available
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")

    def count_tokens(text: str) -> int:
        if not text:
            return 0
        return len(_enc.encode(text))

except Exception:
    count_tokens = count_tokens_approx
