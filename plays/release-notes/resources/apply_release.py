#!/usr/bin/env python3
"""
release-notes apply_release step.

Creates a git tag/release when apply=true. Dry-run by default.

Input (argv): apply ("true"/"false"), from_ref, to_ref, repo_path
Output (stdout): JSON with release result
"""
import json
import sys
import os


def main():
    apply = sys.argv[1] if len(sys.argv) > 1 else "false"
    from_ref = sys.argv[2] if len(sys.argv) > 2 else "HEAD~10"
    to_ref = sys.argv[3] if len(sys.argv) > 3 else "HEAD"
    repo_path = sys.argv[4] if len(sys.argv) > 4 else "."

    if apply.lower() != "true":
        print(json.dumps({
            "applied": False,
            "note": "apply=false (dry run) — no release created. Set apply=true to create.",
        }))
        return

    # Validate repo exists
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        print(json.dumps({
            "applied": False,
            "error": f"Not a git repository: {repo_path}",
        }))
        return

    # In a real implementation, this would create a git tag or GitHub release
    # For safety, we just note that apply was requested
    print(json.dumps({
        "applied": False,
        "note": "apply=true was set but no write was performed (safe mode — implement release creation here)",
    }))


if __name__ == "__main__":
    main()
