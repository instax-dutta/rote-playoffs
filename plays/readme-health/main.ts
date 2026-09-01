/**
 * @rote-frontmatter
 * ---
 * name: readme-health
 * version: 1.0.0
 * description: |
 *   README completeness auditor. Scans for README files, checks standard section coverage (Installation, Usage, License, etc.), link quality, and code block formatting. Returns a deterministic verdict (HEALTHY / NEEDS_WORK / INCOMPLETE) with prioritized recommendations. Read-only, no credentials.
 * provenance:
 *   author: playbookacademy
 *   workspace: readme-health
 * metadata:
 *   rote_version: 0.76.0
 *   version: 1.1.0
 *   status: released
 *   execution_model: steps_with_presentation
 *   flow_type: parallel
 *   requires_endpoints: []
 *   requires_sessions: false
 *   discoverability:
 *     tags:
 *     - domain-devtools
 *     - job-readme-audit
 *     - audience-developers
 *     - effect-read-only
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: src
 *   type: string
 *   required: false
 *   default: .
 *   description: Path to the project root to scan
 *   example: .
 * steps:
 *   scan_readme:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_readme.py}'
 *     - $src
 *   check_sections:
 *     type: process.exec
 *     depends_on:
 *     - scan_readme
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{check_sections.py}'
 *     - '@scan_readme{$.stdout.text}'
 *   check_links:
 *     type: process.exec
 *     depends_on:
 *     - scan_readme
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{check_links.py}'
 *     - '@scan_readme{$.stdout.text}'
 *   check_code_blocks:
 *     type: process.exec
 *     depends_on:
 *     - scan_readme
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{check_code_blocks.py}'
 *     - '@scan_readme{$.stdout.text}'
 *   judge_health:
 *     type: process.exec
 *     depends_on:
 *     - check_sections
 *     - check_links
 *     - check_code_blocks
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{judge_health.py}'
 *     - '@check_sections{$.stdout.text}'
 *     - '@check_links{$.stdout.text}'
 *     - '@check_code_blocks{$.stdout.text}'
 * presentation_fixtures:
 *   scan_readme: resources/presentation-fixtures/scan_readme/fixture.yaml
 *   check_sections: resources/presentation-fixtures/check_sections/fixture.yaml
 *   check_links: resources/presentation-fixtures/check_links/fixture.yaml
 *   check_code_blocks: resources/presentation-fixtures/check_code_blocks/fixture.yaml
 *   judge_health: resources/presentation-fixtures/judge_health/fixture.yaml
 * ---
 */

import {
  loadPresentationContext,
  stepName,
  FlowOutput,
} from "__ROTE_PRESENTATION_SDK__";

const out = new FlowOutput();
const ctx = await loadPresentationContext();

// Read all step outcomes
const scanReadme = ctx.step(stepName("scan_readme"));
const checkSections = ctx.step(stepName("check_sections"));
const checkLinks = ctx.step(stepName("check_links"));
const checkCodeBlocks = ctx.step(stepName("check_code_blocks"));
const judgeHealth = ctx.step(stepName("judge_health"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "scan_readme", step: scanReadme },
  { name: "check_sections", step: checkSections },
  { name: "check_links", step: checkLinks },
  { name: "check_code_blocks", step: checkCodeBlocks },
  { name: "judge_health", step: judgeHealth },
];
for (const s of stepStates) {
  const status = s.step.outcome.status;
  if (status === "completed" || status === "restored") {
    ledger[s.name] = "ok";
  } else if (status === "degraded") {
    ledger[s.name] = "degraded";
  } else {
    ledger[s.name] = status;
  }
}

// Parse the verdict from judge_health step
let verdict = "UNKNOWN";
let checks: unknown[] = [];
let recommendations: string[] = [];
let summary: Record<string, number> = {};
let receipt = "";
let error: string | null = null;

try {
  const outcome = judgeHealth.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        verdict = String(parsed.verdict ?? "UNKNOWN");
        checks = (parsed.checks as unknown[]) ?? [];
        recommendations = (parsed.recommendations as string[]) ?? [];
        summary = (parsed.summary as Record<string, number>) ?? {};
        receipt = String(parsed.receipt ?? "");
      }
    } else {
      error = "judge_health produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "judge_health failed");
  } else {
    error = `judge_health status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse verdict: ${e.message}`;
}

const src = String(ctx.params?.src ?? ".");

out.human(buildHuman(src, verdict, checks, recommendations, summary, error, ledger));
out.summary(receipt || `readme-health — ${verdict}`);
out.result({
  verdict,
  checks,
  recommendations,
  summary,
  source: src,
  ledger,
});

function buildHuman(
  src: string,
  verdict: string,
  checks: unknown[],
  recommendations: string[],
  summary: Record<string, number>,
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `readme-health — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push("README HEALTH");
  lines.push(`Source: ${src}`);
  lines.push(`Verdict: ${verdict}`);
  lines.push("");

  // Stage ledger
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
  lines.push("");

  // Summary
  const passCount = summary.pass ?? 0;
  const failCount = summary.fail ?? 0;
  const warnCount = summary.warn ?? 0;
  const total = summary.total_checks ?? checks.length;
  const coverage = summary.coverage_pct ?? 0;
  lines.push(`  ${passCount}/${total} checks pass, ${failCount} fail, ${warnCount} warn`);
  lines.push(`  Section coverage: ${coverage}%`);
  lines.push("");

  // Checks
  if (checks.length > 0) {
    lines.push("CHECKS");
    for (const c of checks) {
      const check = c as Record<string, unknown>;
      const id = String(check.id ?? "").padEnd(8);
      const status = String(check.status ?? "").padEnd(6);
      const detail = String(check.detail ?? "");
      lines.push(`  ${id} [{status}] ${detail}`);
    }
    lines.push("");
  }

  // Recommendations
  if (recommendations.length > 0) {
    lines.push("RECOMMENDATIONS");
    recommendations.forEach((r, i) => lines.push(`  ${i + 1}. ${r}`));
    lines.push("");
  }

  return lines.join("\n");
}
