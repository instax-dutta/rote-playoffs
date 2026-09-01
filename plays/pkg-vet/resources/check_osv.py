#!/usr/bin/env python3
"""
pkg-vet check_osv step.

Checks OSV.dev for known vulnerabilities for each package.

Input (argv): JSON array of [{package, ecosystem}, ...] from parse_input
Output (stdout): JSON array of [{package, ecosystem, vulns: [...], ok, warning?}]
"""
import json
import sys
import urllib.request


def check_osv(ecosystem: str, pkg: str) -> list[dict]:
    """Check OSV.dev for known vulnerabilities."""
    url = "https://api.osv.dev/v1/query"
    payload = json.dumps({
        "version": "0.0.1",
        "package": {
            "name": pkg,
            "ecosystem": ecosystem,
        },
    }).encode()
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "pkg-vet/1.0.0"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        return data.get("vulns", [])
    except Exception:
        return None  # Signal: check failed


def classify_severity(vuln: dict) -> str:
    """Classify a vulnerability's highest severity."""
    severity_list = vuln.get("database_specific", {}).get("severity", [])
    if isinstance(severity_list, list):
        for s in severity_list:
            if isinstance(s, dict):
                score = s.get("score", "")
            else:
                score = str(s)
            if score in ("CRITICAL", "9.0", "10.0"):
                return "CRITICAL"
            if score in ("HIGH", "7.0", "8.0"):
                return "HIGH"
    elif isinstance(severity_list, str):
        if severity_list == "CRITICAL":
            return "CRITICAL"
        if severity_list == "HIGH":
            return "HIGH"

    # Check CVSS in severity field
    severity_data = vuln.get("severity", [])
    if isinstance(severity_data, list):
        for s in severity_data:
            score = s.get("score", "") if isinstance(s, dict) else str(s)
            if isinstance(score, str):
                try:
                    val = float(score)
                    if val >= 9.0:
                        return "CRITICAL"
                    if val >= 7.0:
                        return "HIGH"
                except (ValueError, TypeError):
                    pass

    return "MODERATE"


def main():
    input_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    try:
        items = json.loads(input_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid input JSON: {e}"}))
        sys.exit(2)

    if not isinstance(items, list):
        items = [items]

    results = []
    for item in items:
        pkg = item.get("package", "")
        eco = item.get("ecosystem", "")
        if not pkg or not eco:
            results.append({"package": pkg, "ecosystem": eco, "vulns": [], "ok": True, "warning": "Skipped - no ecosystem"})
            continue

        vulns = check_osv(eco, pkg)
        if vulns is None:
            # Two-lane failure: OSV unavailable, not a hard error
            results.append({"package": pkg, "ecosystem": eco, "vulns": [], "ok": True, "available": False, "warning": "OSV check unavailable"})
        else:
            # Classify each vuln
            classified = []
            for v in vulns:
                severity = classify_severity(v)
                classified.append({
                    "id": v.get("id", ""),
                    "severity": severity,
                    "summary": v.get("summary", ""),
                })
            results.append({"package": pkg, "ecosystem": eco, "vulns": classified, "ok": True})

    print(json.dumps(results))


if __name__ == "__main__":
    main()
