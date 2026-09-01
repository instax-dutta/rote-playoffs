#!/usr/bin/env python3
"""
env-diff judge_drift step.

Combines all findings into a deterministic verdict.

Input (argv): drift_json, secrets_json
Output (stdout): JSON with final verdict
"""
import json
import sys


def judge(drift_json: dict, secrets_json: dict) -> dict:
    """Combine drift and secrets findings into a verdict."""
    checks = []
    recommendations = []

    drift_count = drift_json.get("drift_count", 0)
    missing = drift_json.get("missing_in_env", [])
    extra = drift_json.get("extra_in_env", [])
    secrets_count = secrets_json.get("count", 0)

    # Drift checks
    checks.append({
        "id": "DRIFT-1",
        "area": "Key Coverage",
        "check": "All template keys present in .env files",
        "status": "PASS" if not missing else "WARN",
        "detail": f"{len(missing)} key(s) missing" if missing else "all template keys present",
    })

    checks.append({
        "id": "DRIFT-2",
        "area": "Key Coverage",
        "check": "No extra keys in .env files",
        "status": "PASS" if not extra else "WARN",
        "detail": f"{len(extra)} extra key(s)" if extra else "no extra keys",
    })

    if missing:
        recommendations.append(f"Add missing keys to .env: {', '.join(missing[:5])}")
    if extra:
        recommendations.append(f"Remove extra keys from .env or add to template: {', '.join(extra[:5])}")

    # Secret checks
    checks.append({
        "id": "SEC-1",
        "area": "Secret Safety",
        "check": "No potential secret leaks in .env files",
        "status": "FAIL" if secrets_count > 0 else "PASS",
        "detail": f"{secrets_count} potential leak(s)" if secrets_count else "no leaks detected",
    })

    if secrets_count > 0:
        recommendations.append("CRITICAL: Remove committed secrets from .env files and rotate them")

    # Verdict
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARN")

    if fail_count == 0 and warn_count == 0:
        verdict = "CLEAN"
    elif fail_count == 0:
        verdict = "DRIFT"
    else:
        verdict = "LEAK"

    return {
        "verdict": verdict,
        "checks": checks,
        "recommendations": recommendations,
        "summary": {
            "drift_count": drift_count,
            "secrets_found": secrets_count,
            "total_checks": len(checks),
            "pass": pass_count,
            "fail": fail_count,
            "warn": warn_count,
        },
        "receipt": f"env-diff — {verdict} — {drift_count} drift, {secrets_count} leaks",
    }


def main():
    drift_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    secrets_json = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    results = judge(drift_json, secrets_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
