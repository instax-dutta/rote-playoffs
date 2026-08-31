#!/usr/bin/env python3
"""
release-notes: Compose a categorized changelog from a git range.

Reads git log between two refs, classifies commits by conventional-commit type,
enriches with PR info where available, and outputs markdown-ready changelog.

Input (argv): from_ref, to_ref, apply ("true"/"false"), repo_path
Output (stdout): JSON with changelog markdown and metadata
"""
import json
import subprocess
import sys
import re
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


def classify_commit(subject: str) -> str:
    """Classify a commit subject by conventional-commit type."""
    subject_lower = subject.lower().strip()

    # Breaking changes
    if "!" in subject.split(":")[0] or "breaking" in subject_lower:
        return "breaking"

    # Match conventional commit prefixes
    patterns = [
        (r"^feat[\(:]", "feat"),
        (r"^fix[\(:]", "fix"),
        (r"^perf[\(:]", "perf"),
        (r"^refactor[\(:]", "refactor"),
        (r"^docs[\(:]", "docs"),
        (r"^style[\(:]", "style"),
        (r"^test[\(:]", "test"),
        (r"^chore[\(:]", "chore"),
        (r"^build[\(:]", "build"),
        (r"^ci[\(:]", "ci"),
        (r"^revert[\(:]", "revert"),
    ]

    for pattern, commit_type in patterns:
        if re.match(pattern, subject_lower):
            return commit_type

    return "other"


def get_commits(from_ref: str, to_ref: str, repo_path: str) -> list[dict]:
    """Get commits between two refs."""
    # Format: hash|author|subject|date
    fmt = "%H|%an|%s|%ad"
    output = run_git(
        ["log", f"{from_ref}..{to_ref}", f"--format={fmt}", "--date=short"],
        cwd=repo_path,
    )

    if not output:
        return []

    commits = []
    for line in output.split("\n"):
        parts = line.split("|", 3)
        if len(parts) >= 4:
            commits.append({
                "hash": parts[0][:8],
                "author": parts[1],
                "subject": parts[2],
                "date": parts[3],
                "type": classify_commit(parts[2]),
            })

    return commits


def build_changelog(commits: list[dict], from_ref: str, to_ref: str) -> dict:
    """Build a categorized changelog from commits."""
    # Group by type
    categories: dict[str, list[dict]] = {}
    type_order = ["feat", "fix", "perf", "refactor", "docs", "test", "chore", "build", "ci", "revert", "other"]

    for commit in commits:
        t = commit["type"]
        if t not in categories:
            categories[t] = []
        categories[t].append(commit)

    # Build markdown
    lines: list[str] = []
    lines.append(f"## Changelog: {from_ref} → {to_ref}")
    lines.append("")

    # Summary counts
    counts = {t: len(categories.get(t, [])) for t in type_order if t in categories}
    summary_parts = [f"{count} {t}" for t, count in counts.items()]
    lines.append(f"**{len(commits)} commits** — {', '.join(summary_parts)}")
    lines.append("")

    # Breaking changes first
    breaking = [c for c in commits if c["type"] == "breaking"]
    if breaking:
        lines.append("### Breaking Changes")
        lines.append("")
        for c in breaking:
            lines.append(f"- {c['subject']} ({c['hash']}) — @{c['author']}")
        lines.append("")

    # Categorized commits
    type_headings = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "perf": "Performance",
        "refactor": "Refactoring",
        "docs": "Documentation",
        "test": "Tests",
        "chore": "Chores",
        "build": "Build",
        "ci": "CI",
        "revert": "Reverts",
        "other": "Other",
    }

    for t in type_order:
        if t in categories and categories[t]:
            heading = type_headings.get(t, t.title())
            lines.append(f"### {heading}")
            lines.append("")
            for c in categories[t]:
                lines.append(f"- {c['subject']} ({c['hash']}) — @{c['author']}")
            lines.append("")

    return {
        "markdown": "\n".join(lines),
        "counts": counts,
        "total": len(commits),
        "categories": list(categories.keys()),
    }


def resolve_ref(ref: str, repo_path: str) -> str:
    """Resolve a git ref to a full SHA."""
    output = run_git(["rev-parse", ref], cwd=repo_path)
    return output if output else ref


def main():
    from_ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD~10"
    to_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    apply_release = sys.argv[3] if len(sys.argv) > 3 else "false"
    repo_path = sys.argv[4] if len(sys.argv) > 4 else "."

    # Validate repo
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({"error": f"Not a git repository: {repo_path}"}))
        sys.exit(1)

    # Resolve refs to SHAs
    from_sha = resolve_ref(from_ref, repo_path)
    to_sha = resolve_ref(to_ref, repo_path)

    # Get commits
    commits = get_commits(from_sha, to_sha, repo_path)
    if not commits:
        print(json.dumps({"error": f"No commits found between {from_ref} and {to_ref}"}))
        sys.exit(1)

    # Build changelog
    changelog = build_changelog(commits, from_ref, to_ref)

    # Handle apply (gated write)
    release_result = None
    if apply_release.lower() == "true":
        # Create a git tag and/or GitHub release would go here
        # For safety, we just note that apply was requested
        release_result = {
            "applied": False,
            "note": "apply=true was set but no write was performed (safe mode)",
        }

    output = {
        "from": from_ref,
        "to": to_ref,
        "changelog": changelog,
        "apply": apply_release,
        "release_result": release_result,
        "receipt": f"release-notes — {from_ref}→{to_ref} · {changelog['total']} commits · {len(changelog['categories'])} categories · apply={apply_release}",
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
