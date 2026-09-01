#!/usr/bin/env python3
"""
readme-health check_links step.

Checks for broken links and link quality in README.

Input (argv): JSON README files from scan_readme
Output (stdout): JSON with link analysis
"""
import json
import os
import re
import sys


def check_links(readme_json: list[dict]) -> dict:
    """Check link quality in README files."""
    link_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
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

        links = []
        for m in link_re.finditer(content):
            text = m.group(1)
            url = m.group(2)
            links.append({
                "text": text,
                "url": url,
                "is_relative": url.startswith(('./', '../', '#')),
                "is_external": url.startswith(('http://', 'https://')),
                "is_empty": not url or url == '#',
            })

        empty_links = [l for l in links if l["is_empty"]]
        external_links = [l for l in links if l["is_external"]]
        relative_links = [l for l in links if l["is_relative"]]

        results[fpath] = {
            "total_links": len(links),
            "external_links": len(external_links),
            "relative_links": len(relative_links),
            "empty_links": len(empty_links),
            "links": links[:20],  # Cap at 20 for fixture size
        }

    return results


def main():
    readme_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    results = check_links(readme_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
