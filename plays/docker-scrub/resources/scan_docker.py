#!/usr/bin/env python3
"""
docker-scrub scan_docker step.

Scans Docker disk usage and returns raw data.

Input: none
Output (stdout): JSON with Docker disk usage data
"""
import json
import subprocess
import sys


def run_cmd(args: list[str], timeout: int = 30) -> str | None:
    """Run a command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        return None


def scan_disk_usage() -> dict:
    """Scan Docker disk usage."""
    output = run_cmd(["docker", "system", "df", "--format", "{{.Type}}|{{.Total}}|{{.Active}}|{{.Size}}"])
    if not output:
        return {}

    categories = {}
    for line in output.split("\n"):
        parts = line.split("|")
        if len(parts) >= 4:
            categories[parts[0].strip()] = {
                "total": parts[1].strip(),
                "active": parts[2].strip(),
                "size": parts[3].strip(),
            }
    return categories


def scan_dangling_images() -> list[dict]:
    """Scan for dangling (untagged) images."""
    output = run_cmd(["docker", "images", "--filter", "dangling=true", "--format", "{{.ID}}|{{.Size}}|{{.CreatedSince}}"])
    if not output:
        return []

    images = []
    for line in output.split("\n"):
        parts = line.split("|")
        if len(parts) >= 3:
            images.append({
                "id": parts[0].strip(),
                "size": parts[1].strip(),
                "created": parts[2].strip(),
            })
    return images


def scan_unused_volumes() -> list[dict]:
    """Scan for unused volumes."""
    output = run_cmd(["docker", "volume", "ls", "--filter", "dangling=true", "--format", "{{.Name}}|{{.Driver}}|{{.Mountpoint}}"])
    if not output:
        return []

    volumes = []
    for line in output.split("\n"):
        parts = line.split("|")
        if len(parts) >= 3:
            volumes.append({
                "name": parts[0].strip(),
                "driver": parts[1].strip(),
                "mountpoint": parts[2].strip(),
            })
    return volumes


def scan_build_cache() -> list[dict]:
    """Scan build cache."""
    output = run_cmd(["docker", "builder", "du", "--format", "{{.ID}}|{{.Size}}|{{.Description}}"])
    if not output:
        return []

    cache = []
    for line in output.split("\n"):
        parts = line.split("|")
        if len(parts) >= 3:
            cache.append({
                "id": parts[0].strip(),
                "size": parts[1].strip(),
                "description": parts[2].strip(),
            })
    return cache


def main():
    # Check if Docker is available
    check = run_cmd(["docker", "version", "--format", "{{.Server.Version}}"])
    if not check:
        print(json.dumps({"error": "Docker is not running or not installed"}))
        sys.exit(1)

    result = {
        "docker_version": check,
        "disk_usage": scan_disk_usage(),
        "dangling_images": scan_dangling_images(),
        "unused_volumes": scan_unused_volumes(),
        "build_cache": scan_build_cache(),
    }

    print(json.dumps(result))


if __name__ == "__main__":
    main()
