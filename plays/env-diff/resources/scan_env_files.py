#!/usr/bin/env python3
"""
env-diff scan_env_files step.

Scans a directory for .env files and .env.example templates.

Input (argv): src_dir
Output (stdout): JSON with env files found
"""
import json
import os
import sys


def scan_env_files(src_dir: str) -> dict:
    """Find all .env files and templates."""
    env_files = []
    example_files = []
    template_files = []

    for root, dirs, files in os.walk(src_dir):
        # Skip common non-project dirs
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', '.git', '__pycache__', 'venv', '.venv',
            'dist', 'build', '.next', 'target', 'vendor', 'coverage',
        }]

        for fname in files:
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, src_dir)

            if fname.startswith('.env') and not fname.endswith('.example') and not fname.endswith('.template'):
                env_files.append({"path": rel, "name": fname, "size_bytes": os.path.getsize(fpath)})
            elif fname in ('.env.example', '.env.template', '.env.sample', '.env.dist'):
                example_files.append({"path": rel, "name": fname, "size_bytes": os.path.getsize(fpath)})

    return {
        "env_files": env_files,
        "example_files": example_files,
        "total": len(env_files) + len(example_files),
    }


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.isdir(src_dir):
        print(json.dumps({"error": f"Directory not found: {src_dir}"}))
        sys.exit(2)

    results = scan_env_files(src_dir)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
