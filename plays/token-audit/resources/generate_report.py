#!/usr/bin/env python3
"""
token-audit generate_report step.

Generates a final budget report from analysis.

Input (argv): JSON analysis from analyze_budget
Output (stdout): JSON with final report
"""
import json
import sys


def main():
    analysis_json = sys.argv[1] if len(sys.argv) > 1 else "{}"
    try:
        analysis = json.loads(analysis_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid analysis JSON: {e}"}))
        sys.exit(2)

    if "error" in analysis:
        print(json.dumps(analysis))
        return

    # Build report
    report = {
        "summary": f"{analysis.get('total_files', 0)} files · {analysis.get('total_tokens', 0)} tokens",
        "total_files": analysis.get("total_files", 0),
        "total_tokens": analysis.get("total_tokens", 0),
        "bloat_count": len(analysis.get("bloat_files", [])),
        "daily_cost_estimate": analysis.get("daily_cost_estimate", {}),
        "largest_files": analysis.get("largest_files", []),
        "warnings": analysis.get("warnings", []),
        "receipt": (
            f"token-audit — {analysis.get('total_files', 0)} files · "
            f"{analysis.get('total_tokens', 0)} tokens · "
            f"{len(analysis.get('bloat_files', []))} bloated"
        ),
    }

    print(json.dumps(report))


if __name__ == "__main__":
    main()
