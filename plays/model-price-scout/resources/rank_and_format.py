#!/usr/bin/env python3
"""
model-price-scout rank_and_format step.

Sorts filtered models by cost, limits results, and formats the decision table.

Input (argv): file path from filter_models, max_results
Output (stdout): JSON with ranked table and metadata
"""
import json
import sys
import os


def main():
    info_json = sys.argv[1] if len(sys.argv) > 1 else "{}"
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    try:
        info = json.loads(info_json)
        file_path = info.get("file", "")
    except json.JSONDecodeError:
        file_path = info_json

    if not file_path or not os.path.exists(file_path):
        print(json.dumps({"error": f"Filtered file not found: {file_path}"}))
        sys.exit(2)

    with open(file_path) as f:
        models = json.load(f)

    # Sort: cheapest first, break ties toward major providers
    MAJOR_PROVIDERS = {"openai", "anthropic", "google", "gemini", "mistral", "xai", "deepseek", "cohere", "meta-llama"}

    for m in models:
        m["sort_key"] = m.get("input_cost_per_token", 0) if m.get("input_cost_per_token", 0) > 0 else (m.get("output_cost_per_token", 0) * 0.1)

    models.sort(key=lambda r: (r["sort_key"], 0 if r.get("provider") in MAJOR_PROVIDERS else 1, r.get("model", "")))

    total_matched = len(models)
    models = models[:max_results]

    # Format for display
    rows = []
    for m in models:
        input_cost = m.get("input_cost_per_token", 0)
        output_cost = m.get("output_cost_per_token", 0)
        context_window = m.get("context_window", 0)

        in_per_mtok = round(input_cost * 1_000_000, 2)
        out_per_mtok = round(output_cost * 1_000_000, 2)

        note = ""
        tier = m.get("tier", "")
        if tier == "flagship" and context_window > 0 and context_window < 128000:
            note = "small ctx for flagship"
        elif tier == "fast" and context_window >= 128000:
            note = "large ctx for $"
        elif context_window == 0:
            note = "ctx unknown"

        rows.append({
            "model": m.get("model", ""),
            "provider": m.get("provider", ""),
            "tier": tier,
            "input_cost_per_token": in_per_mtok,
            "output_cost_per_token": out_per_mtok,
            "context_window": context_window,
            "note": note,
        })

    result = {
        "table": rows,
        "meta": {
            "count": len(rows),
            "total_matched": total_matched,
            "source": "LiteLLM public catalog",
            "source_url": "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json",
        }
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
