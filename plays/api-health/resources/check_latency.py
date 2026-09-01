#!/usr/bin/env python3
"""
api-health check_latency step.

Measures response time for endpoints.

Input (argv): JSON endpoints from parse_endpoints, base_url
Output (stdout): JSON with latency measurements
"""
import json
import sys
import time
import urllib.request
import urllib.error


def check_latency(endpoints_json: list[dict], base_url: str) -> list[dict]:
    """Measure response time for each endpoint."""
    results = []

    for ep in endpoints_json:
        method = ep.get("method", "GET")
        path = ep.get("path", "")
        url = base_url.rstrip('/') + '/' + path.lstrip('/')

        try:
            start = time.time()
            req = urllib.request.Request(url, method=method, headers={"User-Agent": "api-health/1.0.0"})
            resp = urllib.request.urlopen(req, timeout=10)
            resp.read()  # Read body to get full timing
            elapsed = (time.time() - start) * 1000  # ms

            results.append({
                "method": method,
                "path": path,
                "url": url,
                "latency_ms": round(elapsed, 1),
                "ok": elapsed < 2000,  # < 2s is ok
            })
        except Exception as e:
            results.append({
                "method": method,
                "path": path,
                "url": url,
                "latency_ms": -1,
                "ok": False,
                "error": str(e),
            })

    return results


def main():
    endpoints_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    base_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000"

    results = check_latency(endpoints_json, base_url)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
