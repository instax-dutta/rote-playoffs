#!/usr/bin/env python3
"""
git-hygiene apply_prune step.

Prunes merged branches when apply=true. Dry-run by default.

Input (argv): apply ("true"/"false"), repo_path, merged_json
Output (stdout): JSON with prune result
"""
import json
import subprocess
import sys
import os


def run_git(args: list[str], cwd: str) -> str | None:
    """Run a git command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def main():
    apply = sys.argv[1] if len(sys.argv) > 1 else "false"
    repo_path = sys.argv[2] if len(sys.argv) > 2 else "."
    merged_json = sys.argv[3] if len(sys.argv) > 3 else "[]"

    if apply.lower() != "true":
        print(json.dumps({
            "applied": False,
            "pruned": [],
            "note": "apply=false (dry run) — no branches pruned. Set apply=true to prune.",
        }))
        return

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({
            "applied": False,
            "pruned": [],
            "error": f"Not a git repository: {repo_path}",
        }))
        return

    try:
        merged = json.loads(merged_json)
    except json.JSONDecodeError:
        merged = []

    pruned = []
    for branch_name in merged:
        result = run_git(["branch", "-d", branch_name], cwd=repo_path)
        pruned.append(branch_name)

    print(json.dumps({
        "applied": True,
        "pruned": pruned,
        "note": f"Pruned {len(pruned)} branches",
    }))


if __name__ == "__main__":
    main()
