#!/usr/bin/env python3
"""
readme-health check_sections step.

Checks README for standard sections.

Input (argv): JSON README files from scan_readme
Output (stdout): JSON with section coverage
"""
import json
import os
import re
import sys


STANDARD_SECTIONS = {
    "installation": [r'##?\s*install', r'##?\s*setup', r'##?\s*getting started'],
    "usage": [r'##?\s*usage', r'##?\s*example', r'##?\s*quick start'],
    "api": [r'##?\s*api', r'##?\s*reference', r'##?\s*docs'],
    "contributing": [r'##?\s*contribut', r'##?\s*develop'],
    "license": [r'##?\s*license', r'##?\s*licence'],
    "badges": [r'\[!\[', r'badge', r'shields\.io'],
    "description": [r'##?\s*about', r'##?\s*description', r'##?\s*introduction'],
}


def check_sections(readme_json: list[dict]) -> dict:
    """Check which standard sections are present."""
    results = {}

    for f in readme_json:
        fpath = f.get("path", "")
        if not fpath or not os.path.isfile(fpath):
            continue

        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
        except OSError:
            continue

        sections_found = {}
        for section_name, patterns in STANDARD_SECTIONS.items():
            found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
            sections_found[section_name] = found

        results[fpath] = {
            "sections": sections_found,
            "found_count": sum(1 for v in sections_found.values() if v),
            "total_sections": len(STANDARD_SECTIONS),
        }

    return results


def main():
    readme_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    results = check_sections(readme_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
