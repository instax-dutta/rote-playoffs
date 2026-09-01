#!/usr/bin/env python3
"""
docker-scrub compute_plan step.

Computes a safe cleanup plan based on analysis.

Input (argv): JSON analysis from analyze_space
Output (stdout): JSON with cleanup plan
"""
import json
import sys


def main():
    analysis_json = sys.argv[1] if len(sys.argv) > 1 else "{}"
    try:
        analysis = json.loads(analysis_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid analysis JSON: {e}"}))
        sys.exit(2)

    if "error" in analysis:
        print(json.dumps(analysis))
        return

    plan = {
        "actions": [],
        "total_reclaimable_mb": analysis.get("total_reclaimable_mb", 0),
        "risk_level": "low",
    }

    reclaimable = analysis.get("reclaimable", {})

    # Dangling images - safe to remove
    dangling = reclaimable.get("dangling_images", {})
    if dangling.get("count", 0) > 0:
        plan["actions"].append({
            "type": "dangling_images",
            "command": "docker image prune -f",
            "description": f"Remove {dangling['count']} untagged images",
            "safe": True,
        })

    # Unused volumes - safe to remove
    volumes = reclaimable.get("unused_volumes", {})
    if volumes.get("count", 0) > 0:
        plan["actions"].append({
            "type": "unused_volumes",
            "command": "docker volume prune -f",
            "description": f"Remove {volumes['count']} unused volumes",
            "safe": True,
        })

    # Build cache - safe to remove
    cache = reclaimable.get("build_cache", {})
    if cache.get("count", 0) > 0:
        plan["actions"].append({
            "type": "build_cache",
            "command": "docker builder prune -f",
            "description": f"Clear {cache['count']} build cache entries ({cache.get('size_mb', 0)} MB)",
            "safe": True,
        })

    # Determine risk level
    if len(plan["actions"]) > 2:
        plan["risk_level"] = "medium"

    print(json.dumps(plan))


if __name__ == "__main__":
    main()
