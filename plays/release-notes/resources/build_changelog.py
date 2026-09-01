#!/usr/bin/env python3
"""
release-notes build_changelog step.

Builds a categorized changelog from classified commits.

Input (argv): JSON array of classified commits from classify_commits
Output (stdout): JSON with markdown changelog and metadata
"""
import json
import sys


def main():
    commits_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    try:
        commits = json.loads(commits_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid commits JSON: {e}"}))
        sys.exit(2)

    # Group by type
    categories: dict[str, list[dict]] = {}
    type_order = ["feat", "fix", "perf", "refactor", "docs", "test", "chore", "build", "ci", "revert", "other"]

    for commit in commits:
        t = commit.get("type", "other")
        if t not in categories:
            categories[t] = []
        categories[t].append(commit)

    # Build markdown
    lines: list[str] = []

    # Summary counts
    counts = {t: len(categories.get(t, [])) for t in type_order if t in categories}
    summary_parts = [f"{count} {t}" for t, count in counts.items()]
    lines.append(f"**{len(commits)} commits** — {', '.join(summary_parts)}")
    lines.append("")

    # Breaking changes first
    breaking = [c for c in commits if c.get("type") == "breaking"]
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

    result = {
        "markdown": "\n".join(lines),
        "total": len(commits),
        "categories": list(categories.keys()),
        "counts": counts,
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
