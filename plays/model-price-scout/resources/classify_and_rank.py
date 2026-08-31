#!/usr/bin/env python3
"""
model-price-scout classify_and_rank step.

Reads the LiteLLM catalog JSON from stdin, classifies models by capability
tier, filters to recognizable/important models, applies user filters, and
emits a ranked decision table as JSON to stdout.

Input (stdin): raw LiteLLM catalog JSON
Args: tier providers max_results budget_per_mtok
"""
import json
import sys
from typing import Any


def _safe_num(val: Any, default: float = 0) -> float:
    """Coerce a value to float, returning default for strings/dicts/None."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default


def _safe_int(val: Any, default: int = 0) -> int:
    """Coerce a value to int, returning default for strings/dicts/None."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default
    return default


def extract_costs(model_data: dict) -> tuple[float, float, int]:
    """Extract input cost, output cost, and context window from a model entry."""
    input_cost = _safe_num(model_data.get("input_cost_per_token"))
    output_cost = _safe_num(model_data.get("output_cost_per_token"))
    context_window = _safe_int(model_data.get("max_input_tokens"))
    if context_window == 0:
        context_window = _safe_int(model_data.get("max_tokens"))
    # Some entries use cost_per_token (same for in/out)
    if input_cost == 0 and "cost_per_token" in model_data:
        c = _safe_num(model_data["cost_per_token"])
        input_cost = c
        output_cost = c
    return input_cost, output_cost, context_window


def extract_provider(model_name: str, model_data: dict) -> str:
    """Extract provider from litellm_provider field, fallback to name parsing."""
    litellm_provider = model_data.get("litellm_provider", "")
    if litellm_provider:
        return litellm_provider
    if "/" in model_name:
        return model_name.split("/")[0]
    return "other"


def classify_tier(model_name: str, max_input_cost: float, context_window: int) -> str:
    """Heuristic tier classification based on pricing and context window."""
    name_lower = model_name.lower()
    if "embed" in name_lower or "embedding" in name_lower:
        return "embedding"
    # Flagship: expensive (>$5/Mtok input) OR very large context (>=200k)
    if max_input_cost > 5.0 or context_window >= 200000:
        return "flagship"
    # Fast: very cheap (<$0.5/Mtok input) AND small-medium context (<64k)
    if max_input_cost < 0.5 and context_window < 64000:
        return "fast"
    return "mid"


def is_recognizable(model_name: str, provider: str) -> bool:
    """Filter to models a developer would actually recognize and consider."""
    name_lower = model_name.lower()
    
    # Well-known model families
    recognizable_prefixes = [
        # OpenAI
        "gpt-4", "gpt-5", "o1", "o3", "o4",
        # Anthropic
        "claude-",
        # Google
        "gemini-",
        # Mistral
        "mistral", "mixtral", "ministral", "magistral", "devstral",
        # Meta (via various providers)
        "llama-3", "llama-4", "llama3", "llama4",
        # DeepSeek
        "deepseek",
        # xAI
        "grok-",
        # Cohere
        "command-",
        # Qwen
        "qwen",
        # Other notable
        "cursor", "minimax", "perplexity", "sonar",
    ]
    for prefix in recognizable_prefixes:
        if name_lower.startswith(prefix) or f"/{prefix}" in name_lower:
            return True
    
    # Well-known providers with clean model names
    clean_providers = {"openai", "anthropic", "google", "gemini", "mistral", "xai", "deepseek", "cohere"}
    if provider in clean_providers:
        return True
    
    return False


def fetch_catalog() -> dict:
    """Fetch the LiteLLM public model catalog."""
    import urllib.request
    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    req = urllib.request.Request(url, headers={"User-Agent": "model-price-scout/0.1.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())


def main():
    # Fetch catalog directly (self-sufficient step — no stdin piping)
    try:
        catalog = fetch_catalog()
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch catalog: {e}"}))
        sys.exit(1)

    # Args
    tier_filter = sys.argv[1] if len(sys.argv) > 1 else "auto"
    providers_filter = sys.argv[2] if len(sys.argv) > 2 else "all"
    max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 0

    # Parse provider filter
    provider_whitelist = None
    if providers_filter != "all":
        provider_whitelist = set(p.strip().lower() for p in providers_filter.split(",") if p.strip())

    # Process each model
    rows = []
    for model_name, model_data in catalog.items():
        if not isinstance(model_data, dict):
            continue

        # Skip non-chat models
        mode = model_data.get("mode", "chat")
        if mode and mode != "chat":
            continue

        input_cost, output_cost, context_window = extract_costs(model_data)

        # Skip models with no pricing data
        if input_cost == 0 and output_cost == 0:
            continue

        provider = extract_provider(model_name, model_data)
        tier = classify_tier(model_name, input_cost, context_window)

        # Apply tier filter
        if tier_filter != "auto" and tier != tier_filter:
            continue

        # Apply provider filter
        if provider_whitelist and provider not in provider_whitelist:
            continue

        # Apply budget filter
        if budget > 0 and input_cost > 0 and input_cost * 1_000_000 > budget:
            continue

        # Only include recognizable models
        if not is_recognizable(model_name, provider):
            continue

        # Compute per-Mtok costs for display
        in_per_mtok = round(input_cost * 1_000_000, 2)
        out_per_mtok = round(output_cost * 1_000_000, 2)

        # Note: flag context window tradeoffs
        note = ""
        if tier == "flagship" and context_window > 0 and context_window < 128000:
            note = "small ctx for flagship"
        elif tier == "fast" and context_window >= 128000:
            note = "large ctx for $"
        elif context_window == 0:
            note = "ctx unknown"

        sort_key = input_cost if input_cost > 0 else (output_cost * 0.1)

        rows.append({
            "model": model_name,
            "provider": provider,
            "tier": tier,
            "input_cost_per_token": in_per_mtok,
            "output_cost_per_token": out_per_mtok,
            "context_window": context_window,
            "note": note,
            "sort_key": sort_key,
        })

    # Sort: cheapest first, but break ties toward well-known providers
    MAJOR_PROVIDERS = {"openai", "anthropic", "google", "gemini", "mistral", "xai", "deepseek", "cohere", "meta-llama"}
    rows.sort(key=lambda r: (r["sort_key"], 0 if r["provider"] in MAJOR_PROVIDERS else 1, r["model"]))

    # Limit results
    total_matched = len(rows)
    rows = rows[:max_results]

    # Remove internal sort fields
    for r in rows:
        del r["sort_key"]

    result = {
        "table": rows,
        "meta": {
            "count": len(rows),
            "total_matched": total_matched,
            "tier_filter": tier_filter,
            "providers_filter": providers_filter,
            "budget_per_mtok": budget,
            "source": "LiteLLM public catalog",
            "source_url": "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json",
        }
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
