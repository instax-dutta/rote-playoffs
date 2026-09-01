#!/usr/bin/env python3
"""
env-diff compare_drift step.

Compares keys between .env files and templates to find drift.

Input (argv): JSON parsed keys from parse_keys
Output (stdout): JSON with drift analysis
"""
import json
import sys


def compare_drift(keys_json: dict) -> dict:
    """Find keys present in examples but missing from .env files and vice versa."""
    env_keys = set()
    example_keys = set()
    env_files = []
    example_files = []

    for fpath, info in keys_json.items():
        keys = set(info.get("keys", []))
        if info.get("category") == "env_files":
            env_keys.update(keys)
            env_files.append(fpath)
        else:
            example_keys.update(keys)
            example_files.append(fpath)

    missing_in_env = sorted(example_keys - env_keys)  # in template but not in .env
    extra_in_env = sorted(env_keys - example_keys)  # in .env but not in template
    common = sorted(env_keys & example_keys)

    return {
        "env_files": env_files,
        "example_files": example_files,
        "env_key_count": len(env_keys),
        "example_key_count": len(example_keys),
        "common_count": len(common),
        "missing_in_env": missing_in_env,
        "extra_in_env": extra_in_env,
        "drift_count": len(missing_in_env) + len(extra_in_env),
    }


def main():
    keys_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    results = compare_drift(keys_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
