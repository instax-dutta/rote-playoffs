#!/usr/bin/env python3
"""
auth-scan judge_security step.

Combines all audit findings into a deterministic verdict.

Input (argv): bcrypt_json, jwt_json, middleware_json
Output (stdout): JSON with final verdict
"""
import json
import sys


def parse_size_ttl(expires_values: list) -> int:
    """Parse expiresIn values to find max TTL in seconds."""
    max_ttl = 0
    for val in expires_values:
        m = re.match(r'^(\d+)([smhd])$', str(val))
        if m:
            mult = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}.get(m[2], 0)
            max_ttl = max(max_ttl, int(m[1]) * mult)
    return max_ttl


import re


def judge(bcrypt_json: dict, jwt_json: dict, middleware_json: dict) -> dict:
    """Combine all findings into a verdict."""
    checks = []
    recommendations = []

    bcrypt_summary = bcrypt_json.get("summary", {})
    jwt_summary = jwt_json.get("summary", {})
    mw_summary = middleware_json.get("summary", {})

    # --- Password Hashing Checks ---
    checks.append({
        "id": "PH-1",
        "area": "Password Hashing",
        "check": "bcrypt.hash() present with salt rounds >= 10",
        "status": "PASS" if bcrypt_summary.get("has_hash") and bcrypt_summary.get("max_rounds", 0) >= 10
                  else "WARN" if bcrypt_summary.get("has_hash") else "FAIL",
        "detail": f"max rounds={bcrypt_summary.get('max_rounds', 0)}" if bcrypt_summary.get("has_hash")
                  else "no bcrypt.hash() call found",
    })

    checks.append({
        "id": "PH-2",
        "area": "Password Hashing",
        "check": "bcrypt.compare() used for verification",
        "status": "PASS" if bcrypt_summary.get("has_compare") else "FAIL",
        "detail": "compare() used" if bcrypt_summary.get("has_compare") else "no bcrypt.compare() found",
    })

    checks.append({
        "id": "PH-3",
        "area": "Password Hashing",
        "check": "No plaintext password comparison",
        "status": "FAIL" if bcrypt_summary.get("has_plaintext_compare") else "PASS",
        "detail": "plaintext comparison detected" if bcrypt_summary.get("has_plaintext_compare")
                  else "no plaintext comparison found",
    })

    if not bcrypt_summary.get("has_hash") or not bcrypt_summary.get("has_compare"):
        recommendations.append("Adopt bcryptjs with hash(password, 12) and bcrypt.compare() for password verification")

    # --- JWT Token Generation Checks ---
    checks.append({
        "id": "JWT-1",
        "area": "Token Generation",
        "check": "jwt.sign() present with expiresIn set",
        "status": "PASS" if jwt_summary.get("sign_count", 0) > 0 and jwt_summary.get("has_expiry")
                  else "WARN" if jwt_summary.get("sign_count", 0) > 0 else "FAIL",
        "detail=f"sign() calls={jwt_summary.get('sign_count', 0)}, expiresIn={jwt_summary.get('expires_in_values', []) or 'not found'}"
        if jwt_summary.get("sign_count", 0) > 0 else "no jwt.sign() call found",
    })
    # Fix the detail field - can't use = in f-string like that
    sign_count = jwt_summary.get("sign_count", 0)
    expires_values = jwt_summary.get("expires_in_values", [])
    if sign_count > 0:
        checks[-1]["detail"] = f"sign() calls={sign_count}, expiresIn={expires_values or 'not found'}"

    checks.append({
        "id": "JWT-2",
        "area": "Token Generation",
        "check": "JWT secret sourced from process.env (not hardcoded)",
        "status": "PASS" if jwt_summary.get("uses_env_secret") and not jwt_summary.get("has_hardcoded_secret")
                  else "FAIL",
        "detail": "JWT_SECRET read from environment" if jwt_summary.get("uses_env_secret")
                  else "JWT_SECRET not read from process.env",
    })

    if jwt_summary.get("has_hardcoded_secret"):
        recommendations.append("CRITICAL: Remove hardcoded JWT secret. Use process.env.JWT_SECRET instead")

    # Parse TTL
    max_ttl = parse_size_ttl(expires_values)
    if max_ttl > 28800:
        recommendations.append(f"Token expiry of {max_ttl // 3600}h is long-lived; consider shorter TTL or refresh tokens")

    # --- JWT Verification Checks ---
    checks.append({
        "id": "JWT-3",
        "area": "Token Verification",
        "check": "jwt.verify() present in middleware",
        "status": "PASS" if jwt_summary.get("verify_count", 0) > 0 else "FAIL",
        "detail": f"jwt.verify() calls={jwt_summary.get('verify_count', 0)}",
    })

    checks.append({
        "id": "JWT-4",
        "area": "Token Verification",
        "check": "Bearer token extraction from Authorization header",
        "status": "PASS" if jwt_summary.get("has_bearer_extraction") else "WARN",
        "detail": "Bearer extraction found" if jwt_summary.get("has_bearer_extraction")
                  else "no Bearer extraction detected",
    })

    if jwt_summary.get("verify_count", 0) == 0:
        recommendations.append("Add auth middleware that calls jwt.verify(token, process.env.JWT_SECRET) before protected routes")

    # --- Middleware Coverage Checks ---
    checks.append({
        "id": "MW-1",
        "area": "Middleware Coverage",
        "check": "Auth middleware files present",
        "status": "PASS" if mw_summary.get("middleware_files", 0) > 0 else "FAIL",
        "detail": f"{mw_summary.get('middleware_files', 0)} middleware file(s) found",
    })

    checks.append({
        "id": "MW-2",
        "area": "Middleware Coverage",
        "check": "Protected routes use auth middleware",
        "status": "PASS" if mw_summary.get("coverage_pct", 0) >= 80
                  else "WARN" if mw_summary.get("coverage_pct", 0) >= 50 else "FAIL",
        "detail": f"{mw_summary.get('protected', 0)}/{mw_summary.get('total_routes', 0)} routes protected ({mw_summary.get('coverage_pct', 0)}%)",
    })

    if mw_summary.get("coverage_pct", 0) < 80:
        recommendations.append(f"Only {mw_summary.get('coverage_pct', 0)}% of routes are protected; add auth middleware to unprotected routes")

    # --- Refresh Token Check ---
    checks.append({
        "id": "RT-1",
        "area": "Token Refresh",
        "check": "Refresh token mechanism present",
        "status": "PASS" if jwt_summary.get("has_refresh_token") else "WARN",
        "detail": "Refresh token found" if jwt_summary.get("has_refresh_token")
                  else "no refresh token mechanism detected",
    })

    if not jwt_summary.get("has_refresh_token"):
        recommendations.append("Consider adding refresh tokens for better security posture")

    # Compute verdict
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARN")

    if fail_count == 0 and warn_count == 0:
        verdict = "PASS"
    elif fail_count == 0:
        verdict = "PASS_WITH_WARNINGS"
    else:
        verdict = "FAIL"

    return {
        "verdict": verdict,
        "checks": checks,
        "recommendations": recommendations,
        "summary": {
            "total": len(checks),
            "pass": pass_count,
            "fail": fail_count,
            "warn": warn_count,
        },
        "receipt": f"auth-scan — {verdict} — {pass_count}/{len(checks)} pass, {fail_count} fail, {warn_count} warn",
    }


def main():
    bcrypt_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    jwt_json = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    middleware_json = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}

    results = judge(bcrypt_json, jwt_json, middleware_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
