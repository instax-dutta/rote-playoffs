#!/usr/bin/env python3
"""
readme-health check_code_blocks step.

Checks for code examples and formatting quality.

Input (argv): JSON README files from scan_readme
Output (stdout): JSON with code block analysis
"""
import json
import os
import re
import sys


def check_code_blocks(readme_json: list[dict]) -> dict:
    """Check code block quality in README files."""
    code_block_re = re.compile(r'```(\w+)?')
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

        blocks = code_block_re.findall(content)
        lang_specified = [b for b in blocks if b]
        lang_unspecified = [b for b in blocks if not b]

        # Check for images
        images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', content)

        # Check for headers
        headers = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)

        results[fpath] = {
            "code_blocks": len(blocks),
            "with_language": len(lang_specified),
            "without_language": len(lang_unspecified),
            "images": len(images),
            "headers": len(headers),
            "has_toc": bool(re.search(r'table.of.contents|## Contents', content, re.IGNORECASE)),
        }

    return results


def main():
    readme_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    results = check_code_blocks(readme_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
