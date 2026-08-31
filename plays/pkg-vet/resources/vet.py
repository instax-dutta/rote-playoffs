#!/usr/bin/env python3
"""
pkg-vet: Vet npm/PyPI/crates packages BEFORE installing.

Fetches registry metadata, checks OSV advisories, computes typosquat distance,
and produces a deterministic verdict (SAFE / CAUTION / AVOID) per package.

Input (argv): package names as comma-separated in arg1, ecosystems as comma-separated in arg2
Output (stdout): JSON with verdicts and evidence
"""
import json
import sys
import urllib.request
import urllib.parse
import http.client
from typing import Any


def fetch_json(url: str, timeout: int = 30) -> dict | None:
    """Fetch JSON from a URL, return None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pkg-vet/0.1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_npm(pkg: str) -> dict | None:
    """Fetch npm registry metadata for a package."""
    url = f"https://registry.npmjs.org/{urllib.parse.quote(pkg)}"
    return fetch_json(url)


def fetch_pypi(pkg: str) -> dict | None:
    """Fetch PyPI JSON API metadata for a package."""
    url = f"https://pypi.org/pypi/{urllib.parse.quote(pkg)}/json"
    return fetch_json(url)


def fetch_crates(pkg: str) -> dict | None:
    """Fetch crates.io API metadata for a package."""
    url = f"https://crates.io/api/v1/crates/{urllib.parse.quote(pkg)}"
    data = fetch_json(url)
    if data and "crate" in data:
        return data["crate"]
    return data


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
            headers={"Content-Type": "application/json", "User-Agent": "pkg-vet/0.1.0"},
            method="POST",
        )
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        return data.get("vulns", [])
    except Exception:
        return []


def levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    return prev_row[-1]


def typosquat_check(pkg: str, ecosystem: str, popular_names: list[str]) -> dict:
    """Check if a package name is a typosquat of popular packages."""
    matches = []
    for popular in popular_names:
        if popular == pkg:
            continue
        dist = levenshtein(pkg, popular)
        if dist <= 2 and dist > 0:
            matches.append({"name": popular, "distance": dist})
    return {"is_typosquat": len(matches) > 0, "matches": matches}


def get_popular_names(ecosystem: str) -> list[str]:
    """Get popular package names for typosquat checking."""
    # Well-known popular packages per ecosystem
    popular = {
        "npm": [
            "react", "vue", "angular", "express", "lodash", "axios", "webpack",
            "babel", "typescript", "eslint", "jest", "mocha", "chalk", "commander",
            "dotenv", "fs-extra", "glob", "minimist", "mkdirp", "rimraf",
            "semver", "uuid", "yargs", "debug", "ms", "slash", "kind-of",
            "left-pad", "is-odd", "is-number", "is-string", "is-array",
        ],
        "pypi": [
            "requests", "numpy", "pandas", "flask", "django", "pytest", "click",
            "setuptools", "wheel", "pip", "virtualenv", "black", "isort",
            "mypy", "sphinx", "twine", "keyring", "cryptography", "jwt",
            "boto3", "botocore", "urllib3", "certifi", "chardet", "idna",
        ],
        "cargo": [
            "serde", "tokio", "rand", "regex", "clap", "log", "env_logger",
            "chrono", "uuid", "reqwest", "hyper", "actix", "rocket", "warp",
            "sqlx", "diesel", "axum", "tower", "tracing", "anyhow",
        ],
    }
    return popular.get(ecosystem, [])


def vet_package(pkg: str, ecosystem: str) -> dict:
    """Vet a single package and return evidence + verdict."""
    result = {
        "package": pkg,
        "ecosystem": ecosystem,
        "verdict": "SAFE",
        "signals": [],
        "sources_ok": 0,
        "sources_total": 0,
    }

    # 1. Fetch registry metadata
    registry_data = None
    if ecosystem == "npm":
        registry_data = fetch_npm(pkg)
    elif ecosystem == "pypi":
        registry_data = fetch_pypi(pkg)
    elif ecosystem == "cargo":
        registry_data = fetch_crates(pkg)

    result["sources_total"] += 1
    if registry_data:
        result["sources_ok"] += 1

    # 2. Check OSV advisories
    osv_vulns = check_osv(ecosystem, pkg)
    result["sources_total"] += 1
    if osv_vulns is not None:
        result["sources_ok"] += 1

    high_vulns = []
    for v in osv_vulns:
        # OSV severity can be a list of objects or strings
        severity_list = v.get("database_specific", {}).get("severity", [])
        if isinstance(severity_list, list):
            for s in severity_list:
                if isinstance(s, dict):
                    sev = s.get("score", "")
                else:
                    sev = str(s)
                if sev in ("HIGH", "CRITICAL", "7.0", "8.0", "9.0", "10.0"):
                    high_vulns.append(v)
                    break
        elif isinstance(severity_list, str):
            if severity_list in ("HIGH", "CRITICAL"):
                high_vulns.append(v)
    if high_vulns:
        result["signals"].append({
            "type": "vulnerability",
            "severity": "high",
            "detail": f"{len(high_vulns)} HIGH/CRITICAL advisories found",
        })
        result["verdict"] = "CAUTION"

    # 3. Typosquat check
    popular = get_popular_names(ecosystem)
    typosquat = typosquat_check(pkg, ecosystem, popular)
    if typosquat["is_typosquat"]:
        matches_str = ", ".join(f"{m['name']} (dist={m['distance']})" for m in typosquat["matches"])
        result["signals"].append({
            "type": "typosquat",
            "severity": "high",
            "detail": f"Possible typosquat of: {matches_str}",
        })
        result["verdict"] = "AVOID"

    # 4. Package age and version count
    if registry_data:
        if ecosystem == "npm":
            created = registry_data.get("time", {}).get("created", "")
            versions = len(registry_data.get("versions", {}))
        elif ecosystem == "pypi":
            releases = registry_data.get("releases", {})
            versions = len(releases)
            # Get creation time from info
            created = registry_data.get("info", {}).get("release_url", "")
        elif ecosystem == "cargo":
            created = registry_data.get("created_at", "")
            versions = registry_data.get("versions_count", 0) or len(registry_data.get("versions", []))
        else:
            created = ""
            versions = 0

        if versions > 0 and versions < 3:
            result["signals"].append({
                "type": "few_versions",
                "severity": "low",
                "detail": f"Only {versions} version(s) published",
            })
            if result["verdict"] == "SAFE":
                result["verdict"] = "CAUTION"

    # 5. Download trend (npm only)
    if ecosystem == "npm" and registry_data:
        # npm doesn't expose downloads in registry JSON; skip for now
        pass

    return result


def main():
    # Parse arguments
    packages_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    ecosystems_arg = sys.argv[2] if len(sys.argv) > 2 else "auto"

    packages = [p.strip() for p in packages_arg.split(",") if p.strip()]

    if not packages:
        print(json.dumps({"error": "No packages specified"}))
        sys.exit(1)

    # Parse ecosystems - handle "auto" specially
    if ecosystems_arg.strip().lower() == "auto":
        ecosystems: list[str] = []  # Will auto-detect per package
    else:
        ecosystems = [e.strip().lower() for e in ecosystems_arg.split(",") if e.strip()]

    # Vet each package
    results = []
    for pkg in packages:
        # Auto-detect ecosystem if needed
        pkg_ecosystems = ecosystems
        if not ecosystems:
            # Try npm first, then pypi, then cargo
            for eco in ["npm", "pypi", "cargo"]:
                data = None
                if eco == "npm":
                    data = fetch_npm(pkg)
                elif eco == "pypi":
                    data = fetch_pypi(pkg)
                elif eco == "cargo":
                    data = fetch_crates(pkg)
                if data:
                    pkg_ecosystems = [eco]
                    break

        for eco in pkg_ecosystems:
            result = vet_package(pkg, eco)
            results.append(result)

    # Compute overall verdict
    verdicts = [r["verdict"] for r in results]
    overall = "SAFE"
    if "AVOID" in verdicts:
        overall = "AVOID"
    elif "CAUTION" in verdicts:
        overall = "CAUTION"

    total_ok = sum(r["sources_ok"] for r in results)
    total_sources = sum(r["sources_total"] for r in results)

    output = {
        "verdict": overall,
        "packages": results,
        "sources_ok": total_ok,
        "sources_total": total_sources,
        "receipt": f"pkg-vet — {len(packages)} packages checked · {verdicts.count('SAFE')} SAFE · {verdicts.count('CAUTION')} CAUTION · {verdicts.count('AVOID')} AVOID · {total_ok}/{total_sources} sources ok",
    }

    print(json.dumps(output))


if __name__ == "__main__":
    main()
