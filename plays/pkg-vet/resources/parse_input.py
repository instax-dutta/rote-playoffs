#!/usr/bin/env python3
"""
pkg-vet parse_input step.

Parses the packages and ecosystems parameters into a normalized JSON array
of {package, ecosystem} objects for downstream steps.

Input (argv): packages (comma-separated), ecosystems (comma-separated or "auto")
Output (stdout): JSON array of [{"package": "zod", "ecosystem": "npm"}, ...]
"""
import json
import sys


def main():
    packages_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    ecosystems_arg = sys.argv[2] if len(sys.argv) > 2 else "auto"

    packages = [p.strip() for p in packages_arg.split(",") if p.strip()]
    if not packages:
        print(json.dumps({"error": "No packages specified"}))
        sys.exit(2)

    eco_parts = [e.strip().lower() for e in ecosystems_arg.split(",") if e.strip()] if ecosystems_arg.strip().lower() != "auto" else []

    items = []
    for i, pkg in enumerate(packages):
        eco = eco_parts[i] if i < len(eco_parts) else (eco_parts[0] if eco_parts else None)
        items.append({"package": pkg, "ecosystem": eco})

    print(json.dumps(items))


if __name__ == "__main__":
    main()
