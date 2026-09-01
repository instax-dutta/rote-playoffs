#!/usr/bin/env python3
"""
readme-health scan_readme step.

Scans a project for README files.

Input (argv): src_dir
Output (stdout): JSON with README files found
"""
import json
import os
import sys


def scan_readme(src_dir: str) -> list[dict]:
    """Find all README files."""
    readme_names = {'readme.md', 'readme.txt', 'readme', 'readme.rst'}
    results = []

    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', '.git', '__pycache__', 'venv', '.venv',
            'dist', 'build', '.next', 'target', 'vendor', 'coverage',
        }]

        for fname in files:
            if fname.lower() in readme_names:
                fpath = os.path.join(root, fname)
                rel = os.path.relpath(fpath, src_dir)
                results.append({
                    "path": rel,
                    "name": fname,
                    "size_bytes": os.path.getsize(fpath),
                })

    return results


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.isdir(src_dir):
        print(json.dumps({"error": f"Directory not found: {src_dir}"}))
        sys.exit(2)

    results = scan_readme(src_dir)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
