/**
 * @rote-frontmatter
 * ---
 * name: auth-scan
 * version: 1.0.0
 * description: |
 *   Auth security audit for Express/Node.js backends. Scans source for auth files, audits bcrypt hashing (salt rounds, compare usage, plaintext), JWT lifecycle (sign, verify, expiry, env secret, bearer extraction), middleware coverage, and refresh tokens. Returns a deterministic verdict (PASS / PASS_WITH_WARNINGS / FAIL) with a checklist, prioritized recommendations, and evidence. Read-only, no credentials.
 * provenance:
 *   author: playbookacademy
 *   workspace: auth-scan
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
 *     - domain-security
 *     - job-auth-audit
 *     - audience-developers
 *     - effect-read-only
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: src
 *   type: string
 *   required: true
 *   description: Path to the backend source directory to audit
 *   example: ./backend/src
 * steps:
 *   scan_routes:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_routes.py}'
 *     - $src
 *   audit_bcrypt:
 *     type: process.exec
 *     depends_on:
 *     - scan_routes
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{audit_bcrypt.py}'
 *     - '@scan_routes{$.stdout.text}'
 *   audit_jwt:
 *     type: process.exec
 *     depends_on:
 *     - scan_routes
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{audit_jwt.py}'
 *     - '@scan_routes{$.stdout.text}'
 *   audit_middleware:
 *     type: process.exec
 *     depends_on:
 *     - scan_routes
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{audit_middleware.py}'
 *     - '@scan_routes{$.stdout.text}'
 *   judge_security:
 *     type: process.exec
 *     depends_on:
 *     - audit_bcrypt
 *     - audit_jwt
 *     - audit_middleware
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{judge_security.py}'
 *     - '@audit_bcrypt{$.stdout.text}'
 *     - '@audit_jwt{$.stdout.text}'
 *     - '@audit_middleware{$.stdout.text}'
 * presentation_fixtures:
 *   scan_routes: resources/presentation-fixtures/scan_routes/fixture.yaml
 *   audit_bcrypt: resources/presentation-fixtures/audit_bcrypt/fixture.yaml
 *   audit_jwt: resources/presentation-fixtures/audit_jwt/fixture.yaml
 *   audit_middleware: resources/presentation-fixtures/audit_middleware/fixture.yaml
 *   judge_security: resources/presentation-fixtures/judge_security/fixture.yaml
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
const scanRoutes = ctx.step(stepName("scan_routes"));
const auditBcrypt = ctx.step(stepName("audit_bcrypt"));
const auditJwt = ctx.step(stepName("audit_jwt"));
const auditMiddleware = ctx.step(stepName("audit_middleware"));
const judgeSecurity = ctx.step(stepName("judge_security"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "scan_routes", step: scanRoutes },
  { name: "audit_bcrypt", step: auditBcrypt },
  { name: "audit_jwt", step: auditJwt },
  { name: "audit_middleware", step: auditMiddleware },
  { name: "judge_security", step: judgeSecurity },
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

// Parse the verdict from judge_security step
let verdict = "UNKNOWN";
let checks: unknown[] = [];
let recommendations: string[] = [];
let summary: Record<string, number> = {};
let receipt = "";
let error: string | null = null;

try {
  const outcome = judgeSecurity.outcome;
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
      error = "judge_security produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "judge_security failed");
  } else {
    error = `judge_security status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse verdict: ${e.message}`;
}

const src = String(ctx.params?.src ?? ".");

out.human(buildHuman(src, verdict, checks, recommendations, summary, error, ledger));
out.summary(receipt || `auth-scan — ${verdict}`);
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
    return `auth-scan — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push("AUTH SECURITY AUDIT");
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
  const total = summary.total ?? checks.length;
  lines.push(`  ${passCount}/${total} checks pass, ${failCount} fail, ${warnCount} warn, ${recommendations.length} recommendation(s)`);
  lines.push("");

  // Group checks by area
  const areas = ["Password Hashing", "Token Generation", "Token Verification", "Middleware Coverage", "Token Refresh"];
  for (const area of areas) {
    const areaChecks = checks.filter((c: any) => c.area === area);
    if (areaChecks.length === 0) continue;

    lines.push(area.toUpperCase());
    lines.push("  ID     Check                                                     Status  Detail");
    for (const c of areaChecks) {
      const check = c as Record<string, unknown>;
      const id = String(check.id ?? "").padEnd(6);
      const checkText = String(check.check ?? "").padEnd(55);
      const status = String(check.status ?? "").padEnd(6);
      const detail = String(check.detail ?? "");
      lines.push(`  ${id} ${checkText} ${status}  ${detail}`);
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
