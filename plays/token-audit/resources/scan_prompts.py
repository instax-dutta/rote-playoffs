#!/usr/bin/env python3
"""
token-audit scan_prompts step.

Scans a directory for prompt files and AI-related text files.

Input (argv): dir, max_files
Output (stdout): JSON array of prompt files found
"""
import json
import os
import sys


def scan_prompts(directory: str, max_files: int = 100) -> list[dict]:
    """Scan for prompt files in a directory."""
    prompt_extensions = {'.txt', '.md', '.prompt', '.prompts'}
    prompt_names = {'prompt', 'system', 'instructions', 'context', 'template'}

    results = []
    for root, dirs, files in os.walk(directory):
        # Skip common non-project dirs
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', '.git', '__pycache__', 'venv', '.venv',
            'dist', 'build', '.next', 'target',
        }]

        for fname in files:
            if len(results) >= max_files:
                break

            fpath = os.path.join(root, fname)
            name_lower = fname.lower()
            ext = os.path.splitext(fname)[1].lower()

            # Check if it looks like a prompt file
            is_prompt = False
            if ext in prompt_extensions:
                is_prompt = True
            for pn in prompt_names:
                if pn in name_lower:
                    is_prompt = True
                    break

            if is_prompt:
                try:
                    size = os.path.getsize(fpath)
                    results.append({
                        "path": fpath,
                        "name": fname,
                        "size_bytes": size,
                    })
                except OSError:
                    pass

        if len(results) >= max_files:
            break

    return results


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    max_files = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    if not os.path.isdir(directory):
        print(json.dumps({"error": f"Directory not found: {directory}"}))
        sys.exit(2)

    prompts = scan_prompts(directory, max_files)
    print(json.dumps(prompts))


if __name__ == "__main__":
    main()
