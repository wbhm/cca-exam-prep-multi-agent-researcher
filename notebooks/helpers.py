"""Shared notebook helpers: usage reporting and result comparison.

Matches the sibling project's helpers.py pattern.
"""

from __future__ import annotations


# Pricing per 1M tokens (Claude Sonnet 4.6)
_PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-opus-4-6": {"input": 5.00, "output": 25.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}


def print_usage(response: object, model: str = "claude-sonnet-4-6") -> None:
    """Print formatted token-usage summary with estimated USD cost."""
    usage = getattr(response, "usage", None)
    if usage is None:
        print("No usage data available.")
        return

    input_tokens = getattr(usage, "input_tokens", 0)
    output_tokens = getattr(usage, "output_tokens", 0)
    cache_read = getattr(usage, "cache_read_input_tokens", 0)
    cache_create = getattr(usage, "cache_creation_input_tokens", 0)

    prices = _PRICING.get(model, _PRICING["claude-sonnet-4-6"])

    # Cache reads cost 10% of input price, cache writes cost 125%
    cost = (
        (input_tokens / 1_000_000) * prices["input"]
        + (output_tokens / 1_000_000) * prices["output"]
        + (cache_read / 1_000_000) * prices["input"] * 0.10
        + (cache_create / 1_000_000) * prices["input"] * 1.25
    )

    print(f"  Input tokens:  {input_tokens:>8,}")
    print(f"  Output tokens: {output_tokens:>8,}")
    if cache_read:
        print(f"  Cache read:    {cache_read:>8,}")
    if cache_create:
        print(f"  Cache create:  {cache_create:>8,}")
    print(f"  Est. cost:     ${cost:>8.4f}")


def compare_results(anti_result: dict, correct_result: dict) -> None:
    """Print side-by-side comparison table of anti-pattern vs correct results.

    Boolean rows are labelled ``FIXED`` when the correct value is True and
    ``REGRESSED`` when it is False, so every boolean metric must be phrased as
    a property the correct pattern should have (``free_of_leaks``, not
    ``contains_leaks``). Values must be measured from a run, never literals;
    ``tests/test_notebooks.py`` enforces both rules.
    """
    all_keys = sorted(set(list(anti_result.keys()) + list(correct_result.keys())))

    print(f"{'Metric':<30} {'Anti-Pattern':>15} {'Correct':>15} {'Delta':>15}")
    print("-" * 77)

    for key in all_keys:
        anti_val = anti_result.get(key, "N/A")
        correct_val = correct_result.get(key, "N/A")

        # Format delta
        if isinstance(anti_val, bool) and isinstance(correct_val, bool):
            if anti_val != correct_val:
                delta = "FIXED" if correct_val else "REGRESSED"
            else:
                delta = "same"
        elif isinstance(anti_val, int | float) and isinstance(correct_val, int | float):
            diff = correct_val - anti_val
            if anti_val != 0:
                pct = (diff / anti_val) * 100
                delta = f"{pct:+.1f}%"
            else:
                delta = f"{diff:+}"
        else:
            delta = "" if str(anti_val) == str(correct_val) else "changed"

        print(f"{key:<30} {str(anti_val):>15} {str(correct_val):>15} {delta:>15}")
