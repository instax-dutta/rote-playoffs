#!/usr/bin/env python3
"""
token-audit analyze_budget step.

Analyzes token counts for bloat and projects API costs.

Input (argv): JSON array of token counts from count_tokens, runs_per_day
Output (stdout): JSON with budget analysis
"""
import json
import sys


# Approximate costs per 1M tokens (USD) for common models
MODEL_COSTS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
}

BLOAT_THRESHOLD = 4000  # tokens


def main():
    tokens_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    runs_per_day = int(sys.argv[2]) if len(sys.argv) > 2 else 1000

    try:
        files = json.loads(tokens_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid tokens JSON: {e}"}))
        sys.exit(2)

    analysis = {
        "total_files": len(files),
        "total_tokens": 0,
        "bloat_files": [],
        "largest_files": [],
        "daily_cost_estimate": {},
        "warnings": [],
    }

    # Compute totals and find bloat
    for f in files:
        tok = f.get("token_count", 0)
        analysis["total_tokens"] += tok
        if tok > BLOAT_THRESHOLD:
            analysis["bloat_files"].append({
                "path": f.get("path", ""),
                "tokens": tok,
                "severity": "high" if tok > 8000 else "medium",
            })

    # Largest files
    sorted_files = sorted(files, key=lambda x: x.get("token_count", 0), reverse=True)
    analysis["largest_files"] = [
        {"path": f.get("path", ""), "tokens": f.get("token_count", 0)}
        for f in sorted_files[:5]
    ]

    # Cost estimates
    for model, costs in MODEL_COSTS.items():
        # Assume 70% input, 30% output
        input_tokens = analysis["total_tokens"] * 0.7
        output_tokens = analysis["total_tokens"] * 0.3
        daily_cost = (input_tokens * costs["input"] + output_tokens * costs["output"]) / 1_000_000 * runs_per_day
        analysis["daily_cost_estimate"][model] = round(daily_cost, 2)

    # Warnings
    if analysis["bloat_files"]:
        analysis["warnings"].append(
            f"{len(analysis['bloat_files'])} files exceed {BLOAT_THRESHOLD} token bloat threshold"
        )
    if analysis["total_tokens"] > 50000:
        analysis["warnings"].append(
            f"Total prompt tokens ({analysis['total_tokens']}) exceed 50k - consider consolidation"
        )

    print(json.dumps(analysis))


if __name__ == "__main__":
    main()
