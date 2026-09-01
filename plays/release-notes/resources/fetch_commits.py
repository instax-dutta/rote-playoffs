#!/usr/bin/env python3
"""
release-notes fetch_commits step.

Reads git log between two refs and outputs commit data.

Input (argv): from_ref, to_ref, repo_path
Output (stdout): JSON array of commits
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


def resolve_ref(ref: str, repo_path: str) -> str:
    """Resolve a git ref to a full SHA."""
    output = run_git(["rev-parse", ref], cwd=repo_path)
    return output if output else ref


def main():
    from_ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD~10"
    to_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    repo_path = sys.argv[3] if len(sys.argv) > 3 else "."

    # Validate repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({"error": f"Not a git repository: {repo_path}"}))
        sys.exit(2)

    # Resolve refs to SHAs
    from_sha = resolve_ref(from_ref, repo_path)
    to_sha = resolve_ref(to_ref, repo_path)

    # Get commits
    fmt = "%H|%an|%s|%ad"
    output = run_git(
        ["log", f"{from_sha}..{to_sha}", f"--format={fmt}", "--date=short"],
        cwd=repo_path,
    )

    if not output:
        print(json.dumps({"error": f"No commits found between {from_ref} and {to_ref}"}))
        sys.exit(2)

    commits = []
    for line in output.split("\n"):
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0][:8],
                "author": parts[1],
                "subject": parts[2],
                "date": parts[3],
            })

    print(json.dumps(commits))


if __name__ == "__main__":
    main()
