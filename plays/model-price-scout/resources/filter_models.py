#!/usr/bin/env python3
"""
model-price-scout filter_models step.

Filters classified models by tier, provider, and budget.

Input (argv): file path from classify_models, tier_filter, providers_filter, budget
Output (stdout): JSON with temp file path of filtered models
"""
import json
import sys
import os
import tempfile


def is_recognizable(model_name: str, provider: str) -> bool:
    """Filter to models a developer would actually recognize and consider."""
    name_lower = model_name.lower()

    recognizable_prefixes = [
        "gpt-4", "gpt-5", "o1", "o3", "o4",
        "claude-",
        "gemini-",
        "mistral", "mixtral", "ministral", "magistral", "devstral",
        "llama-3", "llama-4", "llama3", "llama4",
        "deepseek",
        "grok-",
        "command-",
        "qwen",
        "cursor", "minimax", "perplexity", "sonar",
    ]
    for prefix in recognizable_prefixes:
        if name_lower.startswith(prefix) or f"/{prefix}" in name_lower:
            return True

    clean_providers = {"openai", "anthropic", "google", "gemini", "mistral", "xai", "deepseek", "cohere"}
    if provider in clean_providers:
        return True

    return False


def main():
    info_json = sys.argv[1] if len(sys.argv) > 1 else "{}"
    tier_filter = sys.argv[2] if len(sys.argv) > 2 else "auto"
    providers_filter = sys.argv[3] if len(sys.argv) > 3 else "all"
    budget = float(sys.argv[4]) if len(sys.argv) > 4 else 0

    try:
        info = json.loads(info_json)
        file_path = info.get("file", "")
    except json.JSONDecodeError:
        file_path = info_json

    if not file_path or not os.path.exists(file_path):
        print(json.dumps({"error": f"Classified file not found: {file_path}"}))
        sys.exit(2)

    with open(file_path) as f:
        models = json.load(f)

    # Parse provider filter
    provider_whitelist = None
    if providers_filter != "all":
        provider_whitelist = set(p.strip().lower() for p in providers_filter.split(",") if p.strip())

    filtered = []
    for m in models:
        if tier_filter != "auto" and m.get("tier") != tier_filter:
            continue
        if provider_whitelist and m.get("provider") not in provider_whitelist:
            continue
        if budget > 0 and m.get("input_cost_per_token", 0) > 0:
            if m["input_cost_per_token"] * 1_000_000 > budget:
                continue
        if not is_recognizable(m.get("model", ""), m.get("provider", "")):
            continue
        filtered.append(m)

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, prefix='mpc_filtered_')
    json.dump(filtered, tmp)
    tmp.close()

    print(json.dumps({"file": tmp.name, "count": len(filtered)}))


if __name__ == "__main__":
    main()
