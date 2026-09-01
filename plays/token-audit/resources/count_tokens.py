#!/usr/bin/env python3
"""
token-audit count_tokens step.

Estimates token counts for each prompt file.

Input (argv): JSON array of prompt files from scan_prompts
Output (stdout): JSON array of files with token estimates
"""
import json
import os
import sys


def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token for English text."""
    return len(text) // 4


def count_tokens_in_file(fpath: str) -> dict:
    """Count estimated tokens in a file."""
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        token_count = estimate_tokens(content)
        line_count = content.count('\n') + 1
        return {
            "path": fpath,
            "token_count": token_count,
            "line_count": line_count,
            "char_count": len(content),
            "ok": True,
        }
    except Exception as e:
        return {
            "path": fpath,
            "token_count": 0,
            "line_count": 0,
            "char_count": 0,
            "ok": False,
            "error": str(e),
        }


def main():
    prompts_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    try:
        prompts = json.loads(prompts_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid prompts JSON: {e}"}))
        sys.exit(2)

    results = []
    for p in prompts:
        fpath = p.get("path", "")
        if fpath and os.path.isfile(fpath):
            result = count_tokens_in_file(fpath)
            results.append(result)
        else:
            results.append({
                "path": fpath,
                "token_count": 0,
                "line_count": 0,
                "char_count": 0,
                "ok": False,
                "error": "File not found",
            })

    print(json.dumps(results))


if __name__ == "__main__":
    main()
