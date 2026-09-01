#!/usr/bin/env python3
"""
git-hygiene scan_merged step.

Gets branches merged into the main branch.

Input (argv): repo_path
Output (stdout): JSON array of merged branch names
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

    # Try main first, then master
    output = run_git(["branch", "--merged", "main"], cwd=repo_path)
    if not output:
        output = run_git(["branch", "--merged", "master"], cwd=repo_path)
    if not output:
        print(json.dumps([]))
        return

    merged = []
    for line in output.split("\n"):
        name = line.strip().lstrip("* ").strip()
        if name and name != "main" and name != "master":
            merged.append(name)

    print(json.dumps(merged))


if __name__ == "__main__":
    main()
