#!/usr/bin/env python3
"""
api-health judge_api_health step.

Combines all findings into a deterministic verdict.

Input (argv): status_json, latency_json
Output (stdout): JSON with final verdict
"""
import json
import sys


def judge(status_json: list[dict], latency_json: list[dict]) -> dict:
    """Combine status and latency findings into a verdict."""
    checks = []
    recommendations = []

    # Status checks
    total = len(status_json)
    ok_count = sum(1 for s in status_json if s.get("ok"))
    fail_count = total - ok_count

    checks.append({
        "id": "STATUS-1",
        "area": "Endpoint Status",
        "check": "All endpoints return 2xx/3xx status",
        "status": "PASS" if fail_count == 0 else "WARN" if ok_count > total / 2 else "FAIL",
        "detail": f"{ok_count}/{total} endpoints healthy",
    })

    if fail_count > 0:
        failed = [s for s in status_json if not s.get("ok")]
        recommendations.append(f"Fix {fail_count} failing endpoint(s): {', '.join(f['path'] for f in failed[:3])}")

    # Latency checks
    latencies = [l for l in latency_json if l.get("latency_ms", -1) > 0]
    if latencies:
        avg_latency = sum(l["latency_ms"] for l in latencies) / len(latencies)
        max_latency = max(l["latency_ms"] for l in latencies)
        slow_count = sum(1 for l in latencies if l["latency_ms"] > 1000)

        checks.append({
            "id": "LAT-1",
            "area": "Response Time",
            "check": "Average response time < 500ms",
            "status": "PASS" if avg_latency < 500 else "WARN" if avg_latency < 1000 else "FAIL",
            "detail": f"avg={avg_latency:.0f}ms, max={max_latency:.0f}ms",
        })

        if slow_count > 0:
            recommendations.append(f"{slow_count} endpoint(s) are slow (>1000ms); consider caching or optimization")
    else:
        checks.append({
            "id": "LAT-1",
            "area": "Response Time",
            "check": "Response time measurable",
            "status": "WARN",
            "detail": "no latency data available (endpoints may be down)",
        })

    # Verdict
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARN")

    if fail_count == 0 and warn_count == 0:
        verdict = "HEALTHY"
    elif fail_count == 0:
        verdict = "DEGRADED"
    else:
        verdict = "UNHEALTHY"

    return {
        "verdict": verdict,
        "checks": checks,
        "recommendations": recommendations,
        "summary": {
            "total_endpoints": total,
            "healthy": ok_count,
            "unhealthy": fail_count,
            "avg_latency_ms": round(sum(l["latency_ms"] for l in latencies) / max(len(latencies), 1), 1) if latencies else 0,
            "total_checks": len(checks),
            "pass": pass_count,
            "fail": fail_count,
            "warn": warn_count,
        },
        "receipt": f"api-health — {verdict} — {ok_count}/{total} healthy, {pass_count}/{len(checks)} checks pass",
    }


def main():
    status_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else []
    latency_json = json.loads(sys.argv[2]) if len(sys.argv) > 2 else []
    results = judge(status_json, latency_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
