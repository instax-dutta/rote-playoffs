#!/usr/bin/env python3
"""
git-hygiene analyze_hygiene step.

Joins branch, merged, and worktree data to find stale branches and hygiene issues.

Input (argv): branches_json, merged_json, worktrees_json from upstream steps
Output (stdout): JSON with full hygiene analysis
"""
import json
import sys


def main():
    branches_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    merged_json = sys.argv[2] if len(sys.argv) > 2 else "[]"
    worktrees_json = sys.argv[3] if len(sys.argv) > 3 else "{}"

    try:
        branches = json.loads(branches_json)
        merged = json.loads(merged_json)
        wt_data = json.loads(worktrees_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid input JSON: {e}"}))
        sys.exit(2)

    worktrees = wt_data.get("worktrees", [])
    unpushed = wt_data.get("unpushed", [])

    # Find stale branches (not main/master, no upstream)
    stale = []
    for b in branches:
        name = b.get("name", "")
        if name in ("main", "master"):
            continue
        if not b.get("upstream"):
            stale.append({
                "name": name,
                "last_commit": b.get("last_commit", ""),
                "reason": "no upstream",
            })

    result = {
        "branches_total": len(branches),
        "stale_branches": stale,
        "merged_unpruned": merged,
        "worktrees": worktrees,
        "unpushed": unpushed,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
