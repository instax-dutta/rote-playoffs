#!/usr/bin/env python3
"""
pkg-vet fetch_registry step.

Fetches registry metadata for each package in the input list.
Auto-detects ecosystem if not specified.

Input (argv): JSON array of [{package, ecosystem}, ...] from parse_input
Output (stdout): JSON array of [{package, ecosystem, registry: {...}|null, ok, warning?}]
"""
import json
import sys
import urllib.request
import urllib.parse
from typing import Any


def fetch_json(url: str, timeout: int = 30) -> dict | None:
    """Fetch JSON from a URL, return None on failure."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "pkg-vet/1.0.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_npm(pkg: str) -> dict | None:
    url = f"https://registry.npmjs.org/{urllib.parse.quote(pkg)}"
    return fetch_json(url)


def fetch_pypi(pkg: str) -> dict | None:
    url = f"https://pypi.org/pypi/{urllib.parse.quote(pkg)}/json"
    return fetch_json(url)


def fetch_crates(pkg: str) -> dict | None:
    url = f"https://crates.io/api/v1/crates/{urllib.parse.quote(pkg)}"
    data = fetch_json(url)
    if data and "crate" in data:
        return data["crate"]
    return data


def detect_ecosystem(pkg: str) -> str | None:
    """Try to auto-detect the ecosystem for a package."""
    for eco, fetcher in [("npm", fetch_npm), ("pypi", fetch_pypi), ("cargo", fetch_crates)]:
        data = fetcher(pkg)
        if data:
            return eco
    return None


def fetch_for_package(pkg: str, eco: str | None) -> dict:
    """Fetch registry data for a single package."""
    # If ecosystem specified, try that first
    if eco:
        fetchers = {
            "npm": fetch_npm,
            "pypi": fetch_pypi,
            "cargo": fetch_crates,
        }
        fetcher = fetchers.get(eco)
        if fetcher:
            data = fetcher(pkg)
            if data:
                return {"package": pkg, "ecosystem": eco, "registry": extract_registry_data(data, eco), "ok": True}
            return {"package": pkg, "ecosystem": eco, "registry": None, "ok": False, "warning": f"Package '{pkg}' not found in {eco}"}

    # Auto-detect
    detected = detect_ecosystem(pkg)
    if detected:
        fetchers = {"npm": fetch_npm, "pypi": fetch_pypi, "cargo": fetch_crates}
        data = fetchers[detected](pkg)
        if data:
            return {"package": pkg, "ecosystem": detected, "registry": extract_registry_data(data, detected), "ok": True}

    return {"package": pkg, "ecosystem": eco or "unknown", "registry": None, "ok": False, "warning": f"Package '{pkg}' not found in any ecosystem"}


def extract_registry_data(data: dict, eco: str) -> dict:
    """Extract relevant fields from registry metadata."""
    result = {}
    if eco == "npm":
        result["description"] = data.get("description", "")
        result["license"] = data.get("license", "")
        if isinstance(result["license"], dict):
            result["license"] = result["license"].get("type", "")
        result["homepage"] = data.get("homepage", "")
        result["repository"] = data.get("repository", "")
        if isinstance(result["repository"], dict):
            result["repository"] = result["repository"].get("url", "")
        time_data = data.get("time", {})
        result["created"] = time_data.get("created", "")
        result["modified"] = time_data.get("modified", "")
        versions = data.get("versions", {})
        result["version_count"] = len(versions)
        result["latest_version"] = data.get("dist-tags", {}).get("latest", "")
        maintainers = data.get("maintainers", [])
        result["maintainer_count"] = len(maintainers)
    elif eco == "pypi":
        info = data.get("info", {})
        result["description"] = info.get("summary", "")
        result["license"] = info.get("license", "")
        result["homepage"] = info.get("home_page", "")
        result["repository"] = info.get("project_url", "")
        result["latest_version"] = info.get("version", "")
        releases = data.get("releases", {})
        result["version_count"] = len(releases)
        result["maintainer_count"] = len(info.get("maintainer", "").split(",")) if info.get("maintainer") else 0
    elif eco == "cargo":
        result["description"] = data.get("description", "")
        result["license"] = data.get("license", "")
        result["homepage"] = data.get("homepage", "")
        result["repository"] = data.get("repository", "")
        result["created"] = data.get("created_at", "")
        result["latest_version"] = data.get("max_version", "")
        result["version_count"] = data.get("versions_count", 0) or len(data.get("versions", []))
        result["maintainer_count"] = 0
    return result


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
        eco = item.get("ecosystem")
        if not pkg:
            continue
        result = fetch_for_package(pkg, eco)
        results.append(result)

    print(json.dumps(results))


if __name__ == "__main__":
    main()
