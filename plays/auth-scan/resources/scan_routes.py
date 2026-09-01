#!/usr/bin/env python3
"""
auth-scan scan_routes step.

Scans a source directory for auth-related files (routes, middleware, controllers).

Input (argv): src_dir
Output (stdout): JSON array of auth-related files
"""
import json
import os
import re
import sys


def scan_routes(src_dir: str) -> list[dict]:
    """Find all auth-related source files."""
    auth_keywords = [
        'auth', 'login', 'signup', 'register', 'password', 'token',
        'jwt', 'session', 'logout', 'bcrypt', 'hash', 'verify',
        'middleware', 'protected', 'guard', 'permission', 'role',
    ]

    results = []
    for root, dirs, files in os.walk(src_dir):
        # Skip common non-project dirs
        dirs[:] = [d for d in dirs if d in {
            'node_modules', '.git', 'dist', 'build', '.next', 'target',
            'vendor', '__pycache__', '.venv', 'venv', 'coverage',
        }]

        for fname in files:
            if not fname.endswith(('.js', '.ts', '.jsx', '.tsx', '.py', '.go', '.rb')):
                continue

            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, src_dir)

            # Check if filename suggests auth
            name_lower = fname.lower()
            is_auth_file = any(kw in name_lower for kw in auth_keywords)

            # Check file content for auth patterns
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except OSError:
                continue

            has_auth_content = any(
                re.search(pattern, content, re.IGNORECASE)
                for pattern in [
                    r'bcrypt', r'jwt\.', r'jsonwebtoken', r'password',
                    r'hash', r'token', r'auth', r'session', r'middleware',
                    r'express', r'passport', r'authorize', r'authenticate',
                ]
            )

            if is_auth_file or has_auth_content:
                results.append({
                    "path": rel,
                    "name": fname,
                    "size_bytes": os.path.getsize(fpath),
                    "is_auth_file": is_auth_file,
                })

    return results


def main():
    src_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.isdir(src_dir):
        print(json.dumps({"error": f"Source directory not found: {src_dir}"}))
        sys.exit(2)

    routes = scan_routes(src_dir)
    print(json.dumps(routes))


if __name__ == "__main__":
    main()
