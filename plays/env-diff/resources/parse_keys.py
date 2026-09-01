#!/usr/bin/env python3
"""
env-diff parse_keys step.

Parses keys from .env files and templates.

Input (argv): JSON env files from scan_env_files
Output (stdout): JSON with parsed keys per file
"""
import json
import os
import re
import sys


def parse_env_keys(fpath: str) -> list[str]:
    """Extract key names from a .env file."""
    keys = []
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                # Match KEY=value or KEY= or export KEY=value
                m = re.match(r'^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=', line)
                if m:
                    keys.append(m.group(1))
    except OSError:
        pass
    return keys


def main():
    files_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}

    results = {}
    for category in ["env_files", "example_files"]:
        for f in files_json.get(category, []):
            fpath = f.get("path", "")
            if fpath and os.path.isfile(fpath):
                keys = parse_env_keys(fpath)
                results[fpath] = {
                    "keys": keys,
                    "count": len(keys),
                    "category": category,
                }

    print(json.dumps(results))


if __name__ == "__main__":
    main()
