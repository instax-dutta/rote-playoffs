#!/usr/bin/env python3
"""
auth-scan audit_bcrypt step.

Audits bcrypt usage across auth-related files.

Input (argv): JSON array of files from scan_routes
Output (stdout): JSON with bcrypt audit results
"""
import json
import os
import re
import sys


def audit_bcrypt(files_json: list[dict]) -> dict:
    """Audit bcrypt usage in auth files."""
    hash_re = re.compile(r'bcrypt\.hash\s*\(\s*([^,]+)\s*,\s*(\d+)')
    compare_re = re.compile(r'bcrypt\.compare\s*\(')
    gen_salt_re = re.compile(r'bcrypt\.genSalt\s*\(\s*(\d+)')
    import_re = re.compile(r'import\s+.*?bcrypt')
    plaintext_re = re.compile(r'password\s*===?\s*[^;]+|===?\s*password')
    store_re = re.compile(r'(save|create|insert|update)\s*\(\s*\{[^}]*password')

    results = {
        "files": {},
        "summary": {
            "files_with_bcrypt": 0,
            "max_rounds": 0,
            "has_hash": False,
            "has_compare": False,
            "has_plaintext_compare": False,
            "imports_bcrypt": False,
        },
    }

    for f in files_json:
        fpath = f.get("path", "")
        if not fpath:
            continue

        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
        except OSError:
            continue

        if not any(kw in content.lower() for kw in ['bcrypt', 'bcryptjs', 'hash', 'password']):
            continue

        rounds = []
        for m in hash_re.finditer(content):
            rounds.append(int(m.group(2)))
        for m in gen_salt_re.finditer(content):
            rounds.append(int(m.group(1)))

        compares = len(compare_re.findall(content))
        plaintext = len(plaintext_re.findall(content))
        imports = bool(import_re.search(content))
        lines = [ln.strip() for ln in content.splitlines() if any(kw in ln.lower() for kw in ['bcrypt', 'hash', 'password'])][:15]

        file_result = {
            "has_hash": bool(rounds),
            "rounds": rounds,
            "has_compare": compares > 0,
            "compare_count": compares,
            "has_plaintext_compare": plaintext > 0,
            "plaintext_compare_count": plaintext,
            "imports_bcrypt": imports,
            "lines": lines,
        }

        results["files"][fpath] = file_result

        # Update summary
        if rounds:
            results["summary"]["has_hash"] = True
            results["summary"]["max_rounds"] = max(results["summary"]["max_rounds"], max(rounds))
        if compares > 0:
            results["summary"]["has_compare"] = True
        if plaintext > 0:
            results["summary"]["has_plaintext_compare"] = True
        if imports:
            results["summary"]["imports_bcrypt"] = True

    results["summary"]["files_with_bcrypt"] = len(results["files"])
    return results


def main():
    files_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    results = audit_bcrypt(files_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
