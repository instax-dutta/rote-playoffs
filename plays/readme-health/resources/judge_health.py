#!/usr/bin/env python3
"""
readme-health judge_health step.

Combines all findings into a deterministic verdict.

Input (argv): sections_json, links_json, code_json
Output (stdout): JSON with final verdict
"""
import json
import sys


def judge(sections_json: dict, links_json: dict, code_json: dict) -> dict:
    """Combine all findings into a verdict."""
    checks = []
    recommendations = []

    # Section coverage
    total_sections = 0
    found_sections = 0
    for fpath, info in sections_json.items():
        total_sections = info.get("total_sections", 0)
        found_sections = info.get("found_count", 0)
        sections = info.get("sections", {})

        if not sections.get("installation"):
            recommendations.append("Add an Installation section")
        if not sections.get("usage"):
            sections["usage"] = False
            recommendations.append("Add a Usage section")
        if not sections.get("license"):
            recommendations.append("Add a License section")

    coverage_pct = round(found_sections / max(total_sections, 1) * 100)

    checks.append({
        "id": "SEC-1",
        "area": "Section Coverage",
        "check": "Standard README sections present",
        "status": "PASS" if coverage_pct >= 70 else "WARN" if coverage_pct >= 40 else "FAIL",
        "detail": f"{found_sections}/{total_sections} sections ({coverage_pct}%)",
    })

    # Link quality
    total_links = 0
    empty_links = 0
    for fpath, info in links_json.items():
        total_links += info.get("total_links", 0)
        empty_links += info.get("empty_links", 0)

    checks.append({
        "id": "LNK-1",
        "area": "Link Quality",
        "check": "No empty or placeholder links",
        "status": "PASS" if empty_links == 0 else "FAIL",
        "detail": f"{empty_links} empty link(s)" if empty_links else "no empty links",
    })

    if empty_links > 0:
        recommendations.append(f"Fix {empty_links} empty/placeholder link(s)")

    # Code examples
    total_blocks = 0
    with_lang = 0
    for fpath, info in code_json.items():
        total_blocks += info.get("code_blocks", 0)
        with_lang += info.get("with_language", 0)

    checks.append({
        "id": "CODE-1",
        "area": "Code Examples",
        "check": "Code blocks present with language specified",
        "status": "PASS" if total_blocks > 0 and with_lang == total_blocks
                  else "WARN" if total_blocks > 0 else "FAIL",
        "detail": f"{total_blocks} block(s), {with_lang} with language" if total_blocks else "no code blocks",
    })

    if total_blocks == 0:
        recommendations.append("Add code examples with language-specified blocks")
    elif with_lang < total_blocks:
        recommendations.append("Specify language for all code blocks")

    # Verdict
    pass_count = sum(1 for c in checks if c["status"] == "PASS")
    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARN")

    if fail_count == 0 and warn_count == 0:
        verdict = "HEALTHY"
    elif fail_count == 0:
        verdict = "NEEDS_WORK"
    else:
        verdict = "INCOMPLETE"

    return {
        "verdict": verdict,
        "checks": checks,
        "recommendations": recommendations,
        "summary": {
            "coverage_pct": coverage_pct,
            "total_links": total_links,
            "empty_links": empty_links,
            "code_blocks": total_blocks,
            "total_checks": len(checks),
            "pass": pass_count,
            "fail": fail_count,
            "warn": warn_count,
        },
        "receipt": f"readme-health — {verdict} — {coverage_pct}% coverage, {pass_count}/{len(checks)} pass",
    }


def main():
    sections_json = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    links_json = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    code_json = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    results = judge(sections_json, links_json, code_json)
    print(json.dumps(results))


if __name__ == "__main__":
    main()
