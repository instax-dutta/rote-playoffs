#!/usr/bin/env python3
"""
pkg-vet check_typosquat step.

Computes typosquat distance for each package against popular names in its ecosystem.

Input (argv): JSON array of [{package, ecosystem}, ...] from parse_input
Output (stdout): JSON array of [{package, ecosystem, is_typosquat, matches: [...]}]
"""
import json
import sys


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


def get_popular_names(ecosystem: str) -> list[str]:
    """Get popular package names for typosquat checking."""
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


def check_typosquat(pkg: str, ecosystem: str) -> dict:
    """Check if a package name is a typosquat of popular packages."""
    popular = get_popular_names(ecosystem)
    matches = []
    for popular_name in popular:
        if popular_name == pkg:
            continue
        dist = levenshtein(pkg, popular_name)
        if dist <= 2 and dist > 0:
            matches.append({"name": popular_name, "distance": dist})
    return {"is_typosquat": len(matches) > 0, "matches": matches}


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
            results.append({"package": pkg, "ecosystem": eco, "is_typosquat": False, "matches": []})
            continue
        result = check_typosquat(pkg, eco)
        result["package"] = pkg
        result["ecosystem"] = eco
        results.append(result)

    print(json.dumps(results))


if __name__ == "__main__":
    main()
