#!/usr/bin/env python3
"""
git-hygiene scan_worktrees step.

Gets worktrees and unpushed work.

Input (argv): repo_path
Output (stdout): JSON with worktrees and unpushed arrays
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


def get_worktrees(repo_path: str) -> list[dict]:
    """Get git worktree list."""
    output = run_git(["worktree", "list", "--porcelain"], cwd=repo_path)
    if not output:
        return []

    trees = []
    current = {}
    for line in output.split("\n"):
        if line.startswith("worktree "):
            if current:
                trees.append(current)
            current = {"path": line[9:]}
        elif line.startswith("branch "):
            current["branch"] = line[7:]
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True
    if current:
        trees.append(current)
    return trees


def get_unpushed(repo_path: str) -> list[dict]:
    """Find unpushed commits."""
    output = run_git(["status", "--branch", "--porcelain"], cwd=repo_path)
    if not output:
        return []

    unpushed = []
    for line in output.split("\n"):
        if line.startswith("##"):
            if "[ahead " in line:
                ahead = line.split("[ahead ")[1].split("]")[0]
                branch = line[3:].split("...")[0].strip()
                unpushed.append({"branch": branch, "ahead": ahead})
    return unpushed


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({"error": f"Not a git repository: {repo_path}"}))
        sys.exit(2)

    worktrees = get_worktrees(repo_path)
    unpushed = get_unpushed(repo_path)

    print(json.dumps({"worktrees": worktrees, "unpushed": unpushed}))


if __name__ == "__main__":
    main()
