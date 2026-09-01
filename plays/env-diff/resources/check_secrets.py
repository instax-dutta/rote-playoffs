#!/usr/bin/env python3
"""
env-diff check_secrets step.

Checks for potential secret leaks in .env files (committed secrets).

Input (argv): JSON env files from scan_env_files
Output (stdout): JSON with secret leak findings
"""
import json
import os
import re
import sys


# Patterns that suggest real secrets (not placeholders)
SECRET_PATTERNS = [
    (re.compile(r'(?:password|secret|token|key|api_key)\s*=\s*["\']?([^\s"\']{8,})', re.IGNORECASE), "potential_secret"),
    (re.compile(r'(?:AWS|AMAZON)_?(?:ACCESS_?KEY|SECRET_?KEY)\s*=\s*["\']?([A-Z0-9/+=]{20,})', re.IGNORECASE), "aws_key"),
    (re.compile(r'GITHUB_?TOKEN\s*=\s*["\']?([^\s"\']{20,})', re.IGNORECASE), "github_token"),
    (re.compile(r'PRIVATE_?KEY\s*=\s*["\']?-----BEGIN', re.IGNORECASE), "private_key"),
]

# Placeholder values to ignore
PLACEHOLDERS = {
    'your_password', 'your_secret', 'your_key', 'xxx', 'abc123', 'changeme',
    'password', 'secret', 'test', 'example', 'placeholder', 'dummy',
    'your_token_here', 'your_api_key_here', 'insert_here', 'replace_me',
}


def check_secrets(files_json: dict) -> dict:
    """Check for potential secret leaks."""
    findings = []

    for f in files_json.get("env_files", []):
        fpath = f.get("path", "")
        if not fpath or not os.path.isfile(fpath):
            continue

        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
        except OSError:
            continue

        for pattern, secret_type in SECRET_PATTERNS:
            for m in pattern.finditer(content):
                value = m.group(1)
                if value.lower() not in PLACEHOLDERS and len(value) > 6:
                    line_num = content[:m.start()].count('\n') + 1
                    findings.append({
                        "file": fpath,
                        "line": line_num,
                        "type": secret_type,
                        "key": m.group(0).split('=')[0].strip(),
                    })

    return {
        "findings": findings,
        "count": len(findings),
        "risk_level": "high" if findings else "low",
    }


def main():
    files_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    results = check_secrets(files_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
