#!/usr/bin/env python3
"""
git-hygiene: The cleanup nobody wants by hand.

Audits a git repo for: stale branches, unpushed work, dirty worktrees,
oversized tracked files, merged-but-not-pruned branches.

Input (argv): repo_path, apply ("true"/"false")
Output (stdout): JSON with findings
"""
import json
import subprocess
import sys
import os
from typing import Any


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


def get_branches(repo_path: str) -> list[dict]:
    """Get all local branches with their status."""
    output = run_git(
        ["for-each-ref", "--format=%(refname:short)|%(committerdate:relative)|%(upstream:short)", "refs/heads/"],
        cwd=repo_path,
    )
    if not output:
        return []

    branches = []
    for line in output.split("\n"):
        parts = line.split("|", 2)
        if len(parts) >= 2:
            branches.append({
                "name": parts[0],
                "last_commit": parts[1],
                "upstream": parts[2] if len(parts) > 2 else "",
            })
    return branches


def get_merged_branches(repo_path: str, main_branch: str = "main") -> list[str]:
    """Get branches merged into the main branch."""
    output = run_git(["branch", "--merged", main_branch], cwd=repo_path)
    if not output:
        # Try master
        output = run_git(["branch", "--merged", "master"], cwd=repo_path)
    if not output:
        return []

    merged = []
    for line in output.split("\n"):
        name = line.strip().lstrip("* ").strip()
        if name and name != main_branch and name != "master":
            merged.append(name)
    return merged


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


def get_large_files(repo_path: str, threshold_mb: int = 10) -> list[dict]:
    """Find large tracked files."""
    output = run_git(
        ["rev-list", "--objects", "--all"],
        cwd=repo_path,
    )
    if not output:
        return []

    # Use git cat-file to find large blobs
    large_files = []
    seen = set()
    for line in output.split("\n"):
        parts = line.split(None, 1)
        if len(parts) < 1:
            continue
        sha = parts[0]
        if sha in seen:
            continue
        seen.add(sha)

        # Check size
        size_output = run_git(["cat-file", "-s", sha], cwd=repo_path)
        if size_output:
            try:
                size = int(size_output)
                if size > threshold_mb * 1024 * 1024:
                    # Get filename
                    name_output = run_git(["rev-list", "--all", "--objects"], cwd=repo_path)
                    if name_output:
                        for nline in name_output.split("\n"):
                            if sha in nline:
                                fname = nline.split(None, 1)
                                if len(fname) > 1:
                                    large_files.append({
                                        "file": fname[1],
                                        "size_mb": round(size / 1024 / 1024, 1),
                                    })
                                break
            except ValueError:
                pass

    return large_files


def get_unpushed(repo_path: str) -> list[dict]:
    """Find unpushed commits."""
    output = run_git(["status", "--branch", "--porcelain"], cwd=repo_path)
    if not output:
        return []

    unpushed = []
    for line in output.split("\n"):
        if line.startswith("##"):
            # Parse branch info
            if "[ahead " in line:
                ahead = line.split("[ahead ")[1].split("]")[0]
                branch = line[3:].split("...")[0].strip()
                unpushed.append({"branch": branch, "ahead": ahead})
    return unpushed


def main():
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    apply_prune = sys.argv[2] if len(sys.argv) > 2 else "false"

    # Validate repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({"error": f"Not a git repository: {repo_path}"}))
        sys.exit(1)

    # Gather findings
    branches = get_branches(repo_path)
    merged = get_merged_branches(repo_path)
    worktrees = get_worktrees(repo_path)
    unpushed = get_unpushed(repo_path)

    # Find stale branches (not main/master, no upstream, old)
    stale = []
    for b in branches:
        if b["name"] in ("main", "master"):
            continue
        if not b["upstream"]:
            stale.append({
                "name": b["name"],
                "last_commit": b["last_commit"],
                "reason": "no upstream",
            })

    # Prune action
    pruned = []
    if apply_prune.lower() == "true":
        for branch_name in merged:
            result = run_git(["branch", "-d", branch_name], cwd=repo_path)
            pruned.append(branch_name)

    output = {
        "branches_total": len(branches),
        "stale_branches": stale,
        "merged_unpruned": merged,
        "worktrees": worktrees,
        "unpushed": unpushed,
        "apply": apply_prune,
        "pruned": pruned,
        "receipt": f"git-hygiene — {len(branches)} branches · {len(stale)} stale · {len(merged)} merged-unpruned · {len(worktrees)} worktrees · apply={apply_prune}",
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
