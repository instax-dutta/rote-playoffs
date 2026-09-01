#!/usr/bin/env python3
"""
git-hygiene scan_branches step.

Gets all local branches with their status.

Input (argv): repo_path
Output (stdout): JSON array of branches
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
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({"error": f"Not a git repository: {repo_path}"}))
        sys.exit(2)

    output = run_git(
        ["for-each-ref", "--format=%(refname:short)|%(committerdate:relative)|%(upstream:short)", "refs/heads/"],
        cwd=repo_path,
    )

    if not output:
        print(json.dumps([]))
        return

    branches = []
    for line in output.split("\n"):
        parts = line.split("|", 2)
        if len(parts) >= 2:
            branches.append({
                "name": parts[0],
                "last_commit": parts[1],
                "upstream": parts[2] if len(parts) > 2 else "",
            })

    print(json.dumps(branches))


if __name__ == "__main__":
    main()
