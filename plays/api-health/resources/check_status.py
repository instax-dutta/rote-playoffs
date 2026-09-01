#!/usr/bin/env python3
"""
api-health check_status step.

Checks HTTP status codes for endpoints.

Input (argv): JSON endpoints from parse_endpoints, base_url
Output (stdout): JSON with status check results
"""
import json
import sys
import urllib.request
import urllib.error


def check_status(endpoints_json: list[dict], base_url: str) -> list[dict]:
    """Check HTTP status for each endpoint."""
    results = []

    for ep in endpoints_json:
        method = ep.get("method", "GET")
        path = ep.get("path", "")
        url = base_url.rstrip('/') + '/' + path.lstrip('/')

        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "api-health/1.0.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.getcode()
            results.append({
                "method": method,
                "path": path,
                "url": url,
                "status": status,
                "ok": 200 <= status < 400,
                "error": None,
            })
        except urllib.error.HTTPError as e:
            results.append({
                "method": method,
                "path": path,
                "url": url,
                "status": e.code,
                "ok": 200 <= e.code < 400,
                "error": str(e),
            })
        except Exception as e:
            results.append({
                "method": method,
                "path": path,
                "url": url,
                "status": 0,
                "ok": False,
                "error": str(e),
            })

    return results


def main():
    endpoints_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000"

    results = check_status(endpoints_json, base_url)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
