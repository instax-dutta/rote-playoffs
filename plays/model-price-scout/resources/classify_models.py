#!/usr/bin/env python3
"""
model-price-scout classify_models step.

Classifies each model in the catalog by capability tier.

Input (argv): file path from fetch_catalog
Output (stdout): JSON with temp file path of classified models
"""
import json
import sys
import os
import tempfile
from typing import Any


def safe_num(val: Any, default: float = 0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return default


def safe_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default
    return default


def extract_costs(model_data: dict) -> tuple:
    input_cost = safe_num(model_data.get("input_cost_per_token"))
    output_cost = safe_num(model_data.get("output_cost_per_token"))
    context_window = safe_int(model_data.get("max_input_tokens"))
    if context_window == 0:
        context_window = safe_int(model_data.get("max_tokens"))
    if input_cost == 0 and "cost_per_token" in model_data:
        c = safe_num(model_data["cost_per_token"])
        input_cost = c
        output_cost = c
    return input_cost, output_cost, context_window


def extract_provider(model_name: str, model_data: dict) -> str:
    litellm_provider = model_data.get("litellm_provider", "")
    if litellm_provider:
        return litellm_provider
    if "/" in model_name:
        return model_name.split("/")[0]
    return "other"


def classify_tier(model_name: str, input_cost: float, context_window: int) -> str:
    name_lower = model_name.lower()
    if "embed" in name_lower or "embedding" in name_lower:
        return "embedding"
    if input_cost > 5.0 or context_window >= 200000:
        return "flagship"
    if input_cost < 0.5 and context_window < 64000:
        return "fast"
    return "mid"


def main():
    info_json = sys.argv[1] if len(sys.argv) > 1 else "{}"
    try:
        info = json.loads(info_json)
        file_path = info.get("file", "")
    except json.JSONDecodeError:
        file_path = info_json

    if not file_path or not os.path.exists(file_path):
        print(json.dumps({"error": f"Catalog file not found: {file_path}"}))
        sys.exit(2)

    with open(file_path) as f:
        catalog = json.load(f)

    models = []
    for model_name, model_data in catalog.items():
        if not isinstance(model_data, dict):
            continue
        mode = model_data.get("mode", "chat")
        if mode and mode != "chat":
            continue

        input_cost, output_cost, context_window = extract_costs(model_data)
        if input_cost == 0 and output_cost == 0:
            continue

        provider = extract_provider(model_name, model_data)
        tier = classify_tier(model_name, input_cost, context_window)

        models.append({
            "model": model_name,
            "provider": provider,
            "tier": tier,
            "input_cost_per_token": input_cost,
            "output_cost_per_token": output_cost,
            "context_window": context_window,
        })

    # Write to temp file
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, prefix='mpc_classified_')
    json.dump(models, tmp)
    tmp.close()

    print(json.dumps({"file": tmp.name, "count": len(models)}))


if __name__ == "__main__":
    main()
