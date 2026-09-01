#!/usr/bin/env python3
"""
auth-scan audit_middleware step.

Audits auth middleware coverage across route handlers.

Input (argv): JSON array of files from scan_routes
Output (stdout): JSON with middleware coverage results
"""
import json
import os
import re
import sys


def audit_middleware(files_json: list[dict]) -> dict:
    """Audit auth middleware coverage."""
    middleware_re = re.compile(r'(auth|authenticate|authorize|requireAuth|isAuthenticated|jwt\.verify|passport\.authenticate)')
    route_re = re.compile(r'(app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']')
    protected_routes = []
    unprotected_routes = []
    middleware_files = []

    for f in files_json:
        fpath = f.get("path", "")
        if not fpath:
            continue

        try:
            with open(fpath, 'r', encoding='utf-8', errors='ignore') as fh:
                content = fh.read()
        except OSError:
            continue

        # Check if this is a middleware file
        if 'middleware' in fpath.lower() or 'auth' in fpath.lower():
            if middleware_re.search(content):
                middleware_files.append(fpath)

        # Find routes
        for m in route_re.finditer(content):
            method = m.group(2)
            route = m.group(3)
            line_num = content[:m.start()].count('\n') + 1

            # Check if this route has auth middleware
            # Look for auth middleware on the same line or in the handler args
            line_end = content.find('\n', m.start())
            if line_end == -1:
                line_end = len(content)
            route_context = content[m.start():line_end + 200]  # Next 200 chars

            has_auth = bool(middleware_re.search(route_context))

            route_info = {
                "method": method,
                "path": route,
                "file": fpath,
                "line": line_num,
                "protected": has_auth,
            }

            if has_auth:
                protected_routes.append(route_info)
            else:
                unprotected_routes.append(route_info)

    return {
        "middleware_files": middleware_files,
        "protected_routes": protected_routes,
        "unprotected_routes": unprotected_routes,
        "summary": {
            "total_routes": len(protected_routes) + len(unprotected_routes),
            "protected": len(protected_routes),
            "unprotected": len(unprotected_routes),
            "middleware_files": len(middleware_files),
            "coverage_pct": round(
                len(protected_routes) / max(len(protected_routes) + len(unprotected_routes), 1) * 100
            ),
        },
    }


def main():
    files_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    results = audit_middleware(files_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
