#!/usr/bin/env python3
"""
auth-scan audit_jwt step.

Audits JWT lifecycle across auth-related files.

Input (argv): JSON array of files from scan_routes
Output (stdout): JSON with JWT audit results
"""
import json
import os
import re
import sys


def audit_jwt(files_json: list[dict]) -> dict:
    """Audit JWT usage in auth files."""
    import_re = re.compile(r'import\s+.*?jsonwebtoken')
    sign_re = re.compile(r'jwt\.sign\s*\(')
    verify_re = re.compile(r'jwt\.verify\s*\(')
    expires_re = re.compile(r'expiresIn\s*:\s*["\']?([^"\'\s,}]+)')
    secret_re = re.compile(r'process\.env\.JWT_SECRET|process\.env\.SECRET')
    hardcoded_secret_re = re.compile(r'JWT_SECRET\s*=\s*["\'][^"\']+["\']|secret\s*:\s*["\'][^"\']+["\']')
    bearer_re = re.compile(r'Authorization|Bearer|bearer')
    refresh_re = re.compile(r'refresh|refreshToken|refresh_token')

    results = {
        "files": {},
        "summary": {
            "files_with_jwt": 0,
            "sign_count": 0,
            "verify_count": 0,
            "has_expiry": False,
            "uses_env_secret": False,
            "has_hardcoded_secret": False,
            "has_bearer_extraction": False,
            "has_refresh_token": False,
            "expires_in_values": [],
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

        if not any(kw in content.lower() for kw in ['jwt', 'jsonwebtoken', 'token', 'bearer']):
            continue

        signs = len(sign_re.findall(content))
        verifies = len(verify_re.findall(content))
        expires = expires_re.findall(content)
        uses_env = bool(secret_re.search(content))
        hardcoded = bool(hardcoded_secret_re.search(content))
        bearer = bool(bearer_re.search(content))
        refresh = bool(refresh_re.search(content))
        imports = bool(import_re.search(content))
        lines = [ln.strip() for ln in content.splitlines() if any(kw in ln.lower() for kw in ['jwt', 'token', 'bearer', 'expires'])][:15]

        file_result = {
            "sign_count": signs,
            "verify_count": verifies,
            "expires_in": expires,
            "uses_env_secret": uses_env,
            "has_hardcoded_secret": hardcoded,
            "has_bearer_extraction": bearer,
            "has_refresh_token": refresh,
            "imports_jwt": imports,
            "lines": lines,
        }

        results["files"][fpath] = file_result

        # Update summary
        results["summary"]["sign_count"] += signs
        results["summary"]["verify_count"] += verifies
        if expires:
            results["summary"]["has_expiry"] = True
            results["summary"]["expires_in_values"].extend(expires)
        if uses_env:
            results["summary"]["uses_env_secret"] = True
        if hardcoded:
            results["summary"]["has_hardcoded_secret"] = True
        if bearer:
            results["summary"]["has_bearer_extraction"] = True
        if refresh:
            results["summary"]["has_refresh_token"] = True

    results["summary"]["files_with_jwt"] = len(results["files"])
    # Deduplicate expires_in
    results["summary"]["expires_in_values"] = list(set(results["summary"]["expires_in_values"]))
    return results


def main():
    files_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    results = audit_jwt(files_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
