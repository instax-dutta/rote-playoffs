#!/usr/bin/env python3
"""
docker-scrub execute_cleanup step.

Executes cleanup actions when apply=true. Dry-run by default.

Input (argv): apply ("true"/"false"), plan_json
Output (stdout): JSON with execution result
"""
import json
import subprocess
import sys


def main():
    apply = sys.argv[1] if len(sys.argv) > 1 else "false"
    plan_json = sys.argv[2] if len(sys.argv) > 2 else "{}"

    try:
        plan = json.loads(plan_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid plan JSON: {e}"}))
        sys.exit(2)

    if apply.lower() != "true":
        print(json.dumps({
            "applied": False,
            "executed": [],
            "note": "apply=false (dry run) — no cleanup performed. Set apply=true to execute.",
            "plan": plan,
        }))
        return

    executed = []
    errors = []

    for action in plan.get("actions", []):
        cmd = action.get("command", "")
        if not cmd:
            continue

        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                executed.append({
                    "type": action.get("type"),
                    "command": cmd,
                    "status": "success",
                })
            else:
                errors.append({
                    "type": action.get("type"),
                    "command": cmd,
                    "error": result.stderr.strip() or "Command failed",
                })
        except Exception as e:
            errors.append({
                "type": action.get("type"),
                "command": cmd,
                "error": str(e),
            })

    print(json.dumps({
        "applied": True,
        "executed": executed,
        "errors": errors,
        "note": f"Executed {len(executed)} actions, {len(errors)} errors",
    }))


if __name__ == "__main__":
    main()
