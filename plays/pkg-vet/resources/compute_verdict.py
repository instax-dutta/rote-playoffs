#!/usr/bin/env python3
"""
pkg-vet compute_verdict step.

Joins registry, OSV, and typosquat data to compute a deterministic verdict
per package and an overall verdict.

Input (argv): registry_json, osv_json, typosquat_json (from upstream steps)
Output (stdout): JSON with verdicts, signals, and receipt
"""
import json
import sys
from datetime import datetime, timezone
from typing import Any


def parse_date(date_str: str) -> datetime | None:
    """Parse an ISO date string."""
    if not date_str:
        return None
    try:
        # Handle various ISO formats
        date_str = date_str.replace("Z", "+00:00")
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


def compute_package_verdict(pkg_data: dict, osv_data: dict, typosquat_data: dict) -> dict:
    """Compute verdict for a single package from all signals."""
    pkg_name = pkg_data.get("package", "?")
    eco = pkg_data.get("ecosystem", "?")
    verdict = "SAFE"
    signals = []

    registry = pkg_data.get("registry")

    # 1. Vulnerability signal
    vulns = osv_data.get("vulns", [])
    high_vulns = [v for v in vulns if v.get("severity") in ("HIGH", "CRITICAL")]
    if high_vulns:
        signals.append({
            "type": "vulnerability",
            "severity": "high",
            "detail": f"{len(high_vulns)} HIGH/CRITICAL advisories",
        })
        verdict = "CAUTION"
    elif vulns:
        signals.append({
            "type": "vulnerability",
            "severity": "moderate",
            "detail": f"{len(vulns)} moderate/low advisories",
        })

    # 2. OSV availability
    if osv_data.get("available") is False:
        signals.append({
            "type": "source_degraded",
            "severity": "info",
            "detail": "OSV check unavailable",
        })

    # 3. Typosquat signal
    if typosquat_data.get("is_typosquat"):
        matches_str = ", ".join(f"{m['name']} (dist={m['distance']})" for m in typosquat_data.get("matches", []))
        signals.append({
            "type": "typosquat",
            "severity": "high",
            "detail": f"Possible typosquat of: {matches_str}",
        })
        verdict = "AVOID"

    # 4. Registry availability
    if not registry:
        signals.append({
            "type": "not_found",
            "severity": "high",
            "detail": pkg_data.get("warning", "Package not found in registry"),
        })
        if verdict != "AVOID":
            verdict = "CAUTION"
        return {
            "package": pkg_name,
            "ecosystem": eco,
            "verdict": verdict,
            "signals": signals,
            "sources_ok": 1 if osv_data.get("ok") else 0,
            "sources_total": 2,
        }

    # 5. Package age signal
    created_str = registry.get("created", "")
    created = parse_date(created_str)
    if created:
        age_days = (datetime.now(timezone.utc) - created).days
        if age_days < 90:
            signals.append({
                "type": "young_package",
                "severity": "low",
                "detail": f"Only {age_days} days old",
            })
            if verdict == "SAFE":
                verdict = "CAUTION"

    # 6. Version count signal
    version_count = registry.get("version_count", 0)
    if version_count > 0 and version_count < 3:
        signals.append({
            "type": "few_versions",
            "severity": "low",
            "detail": f"Only {version_count} version(s) published",
        })
        if verdict == "SAFE":
            verdict = "CAUTION"

    # 7. Maintainer signal
    maintainer_count = registry.get("maintainer_count", 0)
    if maintainer_count == 0:
        signals.append({
            "type": "maintainer_unknown",
            "severity": "info",
            "detail": "Maintainer count unknown",
        })

    # 8. License signal
    license_val = registry.get("license", "")
    if not license_val:
        signals.append({
            "type": "license_missing",
            "severity": "low",
            "detail": "No license specified",
        })

    sources_ok = 2  # registry + osv
    sources_total = 2
    if osv_data.get("available") is False:
        sources_ok = 1

    return {
        "package": pkg_name,
        "ecosystem": eco,
        "verdict": verdict,
        "signals": signals,
        "sources_ok": sources_ok,
        "sources_total": sources_total,
    }


def main():
    registry_json = sys.argv[1] if len(sys.argv) > 1 else "[]"
    osv_json = sys.argv[2] if len(sys.argv) > 2 else "[]"
    typosquat_json = sys.argv[3] if len(sys.argv) > 3 else "[]"

    try:
        registry_data = json.loads(registry_json)
        osv_data = json.loads(osv_json)
        typosquat_data = json.loads(typosquat_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid input JSON: {e}"}))
        sys.exit(2)

    # Index by package name for joining
    registry_by_pkg = {item.get("package"): item for item in registry_data}
    osv_by_pkg = {item.get("package"): item for item in osv_data}
    typosquat_by_pkg = {item.get("package"): item for item in typosquat_data}

    # Compute verdict per package
    results = []
    for pkg_name in registry_by_pkg:
        pkg_data = registry_by_pkg[pkg_name]
        osv_d = osv_by_pkg.get(pkg_name, {})
        typosquat_d = typosquat_by_pkg.get(pkg_name, {})
        result = compute_package_verdict(pkg_data, osv_d, typosquat_d)
        results.append(result)

    # Overall verdict = worst of all
    verdicts = [r["verdict"] for r in results]
    overall = "SAFE"
    if "AVOID" in verdicts:
        overall = "AVOID"
    elif "CAUTION" in verdicts:
        overall = "CAUTION"

    total_ok = sum(r["sources_ok"] for r in results)
    total_sources = sum(r["sources_total"] for r in results)

    safe_count = verdicts.count("SAFE")
    caution_count = verdicts.count("CAUTION")
    avoid_count = verdicts.count("AVOID")

    output = {
        "verdict": overall,
        "packages": results,
        "sources_ok": total_ok,
        "sources_total": total_sources,
        "receipt": f"pkg-vet — {len(results)} packages · {safe_count} SAFE · {caution_count} CAUTION · {avoid_count} AVOID · {total_ok}/{total_sources} sources ok",
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
