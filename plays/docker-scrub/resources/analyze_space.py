#!/usr/bin/env python3
"""
docker-scrub analyze_space step.

Analyzes Docker disk usage data to identify reclaimable space.

Input (argv): JSON scan data from scan_docker
Output (stdout): JSON with analysis of reclaimable space
"""
import json
import sys


def parse_size(size_str: str) -> float:
    """Parse a human-readable size string to MB."""
    if not size_str:
        return 0
    size_str = size_str.strip()
    multipliers = {
        "B": 1 / (1024 * 1024),
        "kB": 1 / 1024,
        "MB": 1,
        "GB": 1024,
        "TB": 1024 * 1024,
        "MiB": 1,
        "GiB": 1024,
        "TiB": 1024 * 1024,
    }
    for suffix, mult in multipliers.items():
        if size_str.endswith(suffix):
            try:
                return float(size_str[:-len(suffix)]) * mult
            except ValueError:
                return 0
    # Try plain number
    try:
        return float(size_str) / (1024 * 1024)  # Assume bytes
    except ValueError:
        return 0


def main():
    scan_json = sys.argv[1] if len(sys.argv) > 1 else "{}"
    try:
        data = json.loads(scan_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid scan JSON: {e}"}))
        sys.exit(2)

    if "error" in data:
        print(json.dumps(data))
        return

    analysis = {
        "docker_version": data.get("docker_version", ""),
        "reclaimable": {},
        "total_reclaimable_mb": 0,
        "warnings": [],
    }

    # Analyze dangling images
    dangling = data.get("dangling_images", [])
    dangling_count = len(dangling)
    analysis["reclaimable"]["dangling_images"] = {
        "count": dangling_count,
        "description": f"{dangling_count} untagged images",
    }

    # Analyze unused volumes
    volumes = data.get("unused_volumes", [])
    volume_count = len(volumes)
    analysis["reclaimable"]["unused_volumes"] = {
        "count": volume_count,
        "description": f"{volume_count} unused volumes",
    }

    # Analyze build cache
    cache = data.get("build_cache", [])
    cache_size_mb = sum(parse_size(c.get("size", "0")) for c in cache)
    analysis["reclaimable"]["build_cache"] = {
        "count": len(cache),
        "size_mb": round(cache_size_mb, 1),
        "description": f"{len(cache)} build cache entries ({round(cache_size_mb, 1)} MB)",
    }

    # Analyze disk usage categories
    disk = data.get("disk_usage", {})
    for category, info in disk.items():
        size = parse_size(info.get("size", "0"))
        if size > 100:  # Only flag if > 100MB
            analysis["warnings"].append(f"{category}: {info.get('size', '?')} total")

    # Total reclaimable estimate
    total_mb = cache_size_mb + (dangling_count * 50) + (volume_count * 10)  # Rough estimates
    analysis["total_reclaimable_mb"] = round(total_mb, 1)

    print(json.dumps(analysis))


if __name__ == "__main__":
    main()
