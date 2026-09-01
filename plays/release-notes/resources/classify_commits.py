#!/usr/bin/env python3
"""
release-notes classify_commits step.

Classifies commits by conventional-commit type.

Input (argv): JSON array of commits from fetch_commits
Output (stdout): JSON array of commits with type field added
"""
import json
import sys
import re


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


def main():
    commits_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    try:
        commits = json.loads(commits_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid commits JSON: {e}"}))
        sys.exit(2)

    for commit in commits:
        commit["type"] = classify_commit(commit.get("subject", ""))

    print(json.dumps(commits))


if __name__ == "__main__":
    main()
