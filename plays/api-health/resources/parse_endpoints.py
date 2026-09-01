#!/usr/bin/env python3
"""
api-health parse_endpoints step.

Parses API endpoints from OpenAPI spec or directory of route files.

Input (argv): src (path to spec file or routes directory)
Output (stdout): JSON array of endpoints
"""
import json
import os
import re
import sys


def parse_endpoints_from_spec(fpath: str) -> list[dict]:
    """Parse endpoints from OpenAPI/Swagger JSON or YAML."""
    endpoints = []
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Try JSON first
        try:
            spec = json.loads(content)
        except json.JSONDecodeError:
            # Simple YAML path extraction (basic)
            paths = re.findall(r'^\s+(/[^:{}]+):', content, re.MULTILINE)
            methods = re.findall(r'^\s+(get|post|put|delete|patch)\s*:', content, re.MULTILINE)
            for i, path in enumerate(paths):
                method = methods[i] if i < len(methods) else "get"
                endpoints.append({"method": method.upper(), "path": path.strip()})
            return endpoints

        # Parse OpenAPI JSON
        paths = spec.get("paths", {})
        for path, methods in paths.items():
            for method in methods:
                if method in ("get", "post", "put", "delete", "patch", "options", "head"):
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "summary": methods[method].get("summary", ""),
                    })
    except OSError:
        pass
    return endpoints


def parse_endpoints_from_dir(src_dir: str) -> list[dict]:
    """Parse endpoints from route files (Express, FastAPI, etc.)."""
    endpoints = []
    route_patterns = [
        # Express: app.get('/path', ...) or router.post('/path', ...)
        re.compile(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'),
        # FastAPI: @app.get('/path')
        re.compile(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'),
        # Flask: @app.route('/path', methods=['GET'])
        re.compile(r'@app\.route\s*\(\s*["\']([^"\']+)["\']'),
    ]

    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', '.git', '__pycache__', 'venv', '.venv',
            'dist', 'build', '.next', 'target',
        }]

        for fname in files:
            if not fname.endswith(('.js', '.ts', '.py', '.go', '.rb')):
                continue

            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except OSError:
                continue

            for pattern in route_patterns:
                for m in pattern.finditer(content):
                    if len(m.groups()) == 2:
                        method = m.group(1).upper()
                        path = m.group(2)
                    else:
                        method = "GET"
                        path = m.group(1)
                    endpoints.append({
                        "method": method,
                        "path": path,
                        "source": os.path.relpath(fpath, src_dir),
                    })

    return endpoints


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else "."

    if not os.path.exists(src):
        print(json.dumps({"error": f"Path not found: {src}"}))
        sys.exit(2)

    if os.path.isfile(src):
        endpoints = parse_endpoints_from_spec(src)
    else:
        endpoints = parse_endpoints_from_dir(src)

    print(json.dumps(endpoints))


if __name__ == "__main__":
    main()
