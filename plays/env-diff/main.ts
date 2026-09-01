/**
 * @rote-frontmatter
 * ---
 * name: env-diff
 * version: 1.0.0
 * description: |
 *   .env drift auditor. Scans for .env files and templates, compares keys, finds missing/extra keys, checks for potential secret leaks, and returns a deterministic verdict (CLEAN / DRIFT / LEAK). Read-only, no credentials.
 * provenance:
 *   author: playbookacademy
 *   workspace: env-diff
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
 *     - job-env-drift
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
 *   scan_env_files:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_env_files.py}'
 *     - $src
 *   parse_keys:
 *     type: process.exec
 *     depends_on:
 *     - scan_env_files
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{parse_keys.py}'
 *     - '@scan_env_files{$.stdout.text}'
 *   compare_drift:
 *     type: process.exec
 *     depends_on:
 *     - parse_keys
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{compare_drift.py}'
 *     - '@parse_keys{$.stdout.text}'
 *   check_secrets:
 *     type: process.exec
 *     depends_on:
 *     - scan_env_files
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{check_secrets.py}'
 *     - '@scan_env_files{$.stdout.text}'
 *   judge_drift:
 *     type: process.exec
 *     depends_on:
 *     - compare_drift
 *     - check_secrets
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{judge_drift.py}'
 *     - '@compare_drift{$.stdout.text}'
 *     - '@check_secrets{$.stdout.text}'
 * presentation_fixtures:
 *   scan_env_files: resources/presentation-fixtures/scan_env_files/fixture.yaml
 *   parse_keys: resources/presentation-fixtures/parse_keys/fixture.yaml
 *   compare_drift: resources/presentation-fixtures/compare_drift/fixture.yaml
 *   check_secrets: resources/presentation-fixtures/check_secrets/fixture.yaml
 *   judge_drift: resources/presentation-fixtures/judge_drift/fixture.yaml
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
const scanEnvFiles = ctx.step(stepName("scan_env_files"));
const parseKeys = ctx.step(stepName("parse_keys"));
const compareDrift = ctx.step(stepName("compare_drift"));
const checkSecrets = ctx.step(stepName("check_secrets"));
const judgeDrift = ctx.step(stepName("judge_drift"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "scan_env_files", step: scanEnvFiles },
  { name: "parse_keys", step: parseKeys },
  { name: "compare_drift", step: compareDrift },
  { name: "check_secrets", step: checkSecrets },
  { name: "judge_drift", step: judgeDrift },
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

// Parse the verdict from judge_drift step
let verdict = "UNKNOWN";
let checks: unknown[] = [];
let recommendations: string[] = [];
let summary: Record<string, number> = {};
let receipt = "";
let error: string | null = null;

try {
  const outcome = judgeDrift.outcome;
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
      error = "judge_drift produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "judge_drift failed");
  } else {
    error = `judge_drift status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse verdict: ${e.message}`;
}

const src = String(ctx.params?.src ?? ".");

out.human(buildHuman(src, verdict, checks, recommendations, summary, error, ledger));
out.summary(receipt || `env-diff — ${verdict}`);
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
    return `env-diff — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push("ENV DIFF");
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
  lines.push(`  ${passCount}/${total} checks pass, ${failCount} fail, ${warnCount} warn`);
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
