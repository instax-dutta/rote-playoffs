/**
 * @rote-frontmatter
 * ---
 * name: docker-scrub
 * version: 1.0.0
 * description: |
 *   Reclaim Docker disk space safely. Scans for dangling images, unused volumes, and build cache; computes a cleanup plan; optionally executes it behind the apply=true gate. Read-only by default; writes only on explicit opt-in. Zero credentials, no auth.
 * provenance:
 *   author: playbookacademy
 *   workspace: docker-scrub
 * metadata:
 *   rote_version: 0.76.0
 *   version: 1.2.0
 *   status: released
 *   execution_model: steps_with_presentation
 *   flow_type: sequential
 *   requires_endpoints: []
 *   requires_sessions: false
 *   discoverability:
 *     tags:
 *     - domain-devtools
 *     - job-docker-cleanup
 *     - audience-developers
 *     - effect-gated-write
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: apply
 *   type: string
 *   required: false
 *   default: 'false'
 *   description: 'Set true to execute cleanup (default: dry-run)'
 *   example: 'false'
 * steps:
 *   scan_docker:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_docker.py}'
 *   analyze_space:
 *     type: process.exec
 *     depends_on:
 *     - scan_docker
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{analyze_space.py}'
 *     - '@scan_docker{$.stdout.text}'
 *   compute_plan:
 *     type: process.exec
 *     depends_on:
 *     - analyze_space
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{compute_plan.py}'
 *     - '@analyze_space{$.stdout.text}'
 *   execute_cleanup:
 *     type: process.exec
 *     depends_on:
 *     - compute_plan
 *     timeout_ms: 60000
 *     argv:
 *     - python3
 *     - '@resource{execute_cleanup.py}'
 *     - $apply
 *     - '@compute_plan{$.stdout.text}'
 * presentation_fixtures:
 *   scan_docker: resources/presentation-fixtures/scan_docker/fixture.yaml
 *   analyze_space: resources/presentation-fixtures/analyze_space/fixture.yaml
 *   compute_plan: resources/presentation-fixtures/compute_plan/fixture.yaml
 *   execute_cleanup: resources/presentation-fixtures/execute_cleanup/fixture.yaml
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
const scanDocker = ctx.step(stepName("scan_docker"));
const analyzeSpace = ctx.step(stepName("analyze_space"));
const computePlan = ctx.step(stepName("compute_plan"));
const executeCleanup = ctx.step(stepName("execute_cleanup"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "scan_docker", step: scanDocker },
  { name: "analyze_space", step: analyzeSpace },
  { name: "compute_plan", step: computePlan },
  { name: "execute_cleanup", step: executeCleanup },
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

// Parse the plan from compute_plan step
let totalReclaimableMb = 0;
let actions: unknown[] = [];
let riskLevel = "low";
let apply = "false";
let executed: unknown[] = [];
let error: string | null = null;

try {
  const outcome = computePlan.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        totalReclaimableMb = Number(parsed.total_reclaimable_mb ?? 0);
        actions = (parsed.actions as unknown[]) ?? [];
        riskLevel = String(parsed.risk_level ?? "low");
      }
    } else {
      error = "compute_plan produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "compute_plan failed");
  } else {
    error = `compute_plan status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse plan: ${e.message}`;
}

// Parse execution result
try {
  const outcome = executeCleanup.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      executed = (parsed.executed as unknown[]) ?? [];
      apply = String(parsed.applied != null && parsed.applied ? "true" : "false");
    }
  }
} catch {
  // execute_cleanup is optional-degrade
}

out.human(buildHuman(totalReclaimableMb, actions, riskLevel, apply, executed, error, ledger));
out.summary(`docker-scrub — ${actions.length} actions · ${totalReclaimableMb} MB reclaimable · apply=${apply}`);
out.result({
  total_reclaimable_mb: totalReclaimableMb,
  actions,
  risk_level: riskLevel,
  applied: apply === "true",
  executed,
  ledger,
});

function buildHuman(
  reclaimableMb: number,
  actions: unknown[],
  riskLevel: string,
  apply: string,
  executed: unknown[],
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `docker-scrub — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push("DOCKER SCRUB");
  lines.push(`Reclaimable: ~${reclaimableMb} MB · Risk: ${riskLevel}`);
  lines.push("");

  // Stage ledger
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
  lines.push("");

  if (actions.length > 0) {
    lines.push("Cleanup Plan:");
    for (const a of actions) {
      const action = a as Record<string, unknown>;
      const safe = action.safe ? "[SAFE]" : "[CAUTION]";
      lines.push(`  ${safe} ${action.description}`);
      lines.push(`    command: ${action.command}`);
    }
    lines.push("");
  }

  // Gated-write status
  if (apply === "true") {
    lines.push(`**apply=true** — executed ${executed.length} actions`);
  } else {
    lines.push("**apply=false (dry run)** — no changes made. Set `apply=true` to clean up.");
  }

  return lines.join("\n");
}
