/**
 * @rote-frontmatter
 * ---
 * name: api-health
 * version: 1.0.0
 * description: |
 *   API endpoint health monitor. Parses endpoints from OpenAPI specs or route files, checks HTTP status codes, measures response times, and returns a deterministic verdict (HEALTHY / DEGRADED / UNHEALTHY) with prioritized recommendations. Read-only, no credentials.
 * provenance:
 *   author: playbookacademy
 *   workspace: api-health
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
 *     - job-api-monitoring
 *     - audience-developers
 *     - effect-read-only
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: src
 *   type: string
 *   required: true
 *   description: Path to OpenAPI spec file or routes directory
 *   example: ./routes
 * - name: base_url
 *   type: string
 *   required: false
 *   default: http://localhost:3000
 *   description: Base URL for endpoint health checks
 *   example: http://localhost:3000
 * steps:
 *   parse_endpoints:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{parse_endpoints.py}'
 *     - $src
 *   check_status:
 *     type: process.exec
 *     depends_on:
 *     - parse_endpoints
 *     timeout_ms: 60000
 *     argv:
 *     - python3
 *     - '@resource{check_status.py}'
 *     - '@parse_endpoints{$.stdout.text}'
 *     - $base_url
 *   check_latency:
 *     type: process.exec
 *     depends_on:
 *     - parse_endpoints
 *     timeout_ms: 60000
 *     argv:
 *     - python3
 *     - '@resource{check_latency.py}'
 *     - '@parse_endpoints{$.stdout.text}'
 *     - $base_url
 *   judge_api_health:
 *     type: process.exec
 *     depends_on:
 *     - check_status
 *     - check_latency
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{judge_api_health.py}'
 *     - '@check_status{$.stdout.text}'
 *     - '@check_latency{$.stdout.text}'
 * presentation_fixtures:
 *   parse_endpoints: resources/presentation-fixtures/parse_endpoints/fixture.yaml
 *   check_status: resources/presentation-fixtures/check_status/fixture.yaml
 *   check_latency: resources/presentation-fixtures/check_latency/fixture.yaml
 *   judge_api_health: resources/presentation-fixtures/judge_api_health/fixture.yaml
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
const parseEndpoints = ctx.step(stepName("parse_endpoints"));
const checkStatus = ctx.step(stepName("check_status"));
const checkLatency = ctx.step(stepName("check_latency"));
const judgeApiHealth = ctx.step(stepName("judge_api_health"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "parse_endpoints", step: parseEndpoints },
  { name: "check_status", step: checkStatus },
  { name: "check_latency", step: checkLatency },
  { name: "judge_api_health", step: judgeApiHealth },
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

// Parse the verdict from judge_api_health step
let verdict = "UNKNOWN";
let checks: unknown[] = [];
let recommendations: string[] = [];
let summary: Record<string, number> = {};
let receipt = "";
let error: string | null = null;

try {
  const outcome = judgeApiHealth.outcome;
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
      error = "judge_api_health produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "judge_api_health failed");
  } else {
    error = `judge_api_health status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse verdict: ${e.message}`;
}

const src = String(ctx.params?.src ?? ".");
const baseUrl = String(ctx.params?.base_url ?? "http://localhost:3000");

out.human(buildHuman(src, baseUrl, verdict, checks, recommendations, summary, error, ledger));
out.summary(receipt || `api-health — ${verdict}`);
out.result({
  verdict,
  checks,
  recommendations,
  summary,
  source: src,
  base_url: baseUrl,
  ledger,
});

function buildHuman(
  src: string,
  baseUrl: string,
  verdict: string,
  checks: unknown[],
  recommendations: string[],
  summary: Record<string, number>,
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `api-health — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push("API HEALTH");
  lines.push(`Source: ${src}`);
  lines.push(`Base URL: ${baseUrl}`);
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
  const healthy = summary.healthy ?? 0;
  const totalEndpoints = summary.total_endpoints ?? 0;
  const avgLatency = summary.avg_latency_ms ?? 0;
  lines.push(`  ${healthy}/${totalEndpoints} endpoints healthy`);
  lines.push(`  Avg latency: ${avgLatency}ms`);
  lines.push(`  ${passCount}/${total} checks pass, ${failCount} fail, ${warnCount} warn`);
  lines.push("");

  // Checks
  if (checks.length > 0) {
    lines.push("CHECKS");
    for (const c of checks) {
      const check = c as Record<string, unknown>;
      const id = String(check.id ?? "").padEnd(10);
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
