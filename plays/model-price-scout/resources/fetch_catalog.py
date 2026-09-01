#!/usr/bin/env python3
"""
model-price-scout fetch_catalog step.

Fetches the LiteLLM public model catalog and writes it to a temp file.

Input: none
Output (stdout): JSON with the temp file path
"""
import json
import sys
import urllib.request
import tempfile
import os


def fetch_catalog() -> dict:
    """Fetch the LiteLLM public model catalog."""
    url = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    req = urllib.request.Request(url, headers={"User-Agent": "model-price-scout/1.0.0"})
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read().decode())


def main():
    try:
        catalog = fetch_catalog()
    except Exception as e:
        print(json.dumps({"error": f"Failed to fetch catalog: {e}"}))
        sys.exit(1)

    # Write to temp file and output the path
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, prefix='mpc_catalog_')
    json.dump(catalog, tmp)
    tmp.close()

    print(json.dumps({"file": tmp.name, "count": len(catalog)}))


if __name__ == "__main__":
    main()
