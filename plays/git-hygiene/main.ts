/**
 * @rote-frontmatter
 * ---
 * name: git-hygiene
 * version: 1.0.0
 * description: |
 *   The cleanup nobody wants by hand. Audits a git repo for stale branches, unpushed work, dirty worktrees, merged-but-not-pruned branches — one sweep with a safe prune mode behind the apply=true gate. Read-only by default; writes only on explicit opt-in.
 * provenance:
 *   author: playbookacademy
 *   workspace: git-hygiene
 * metadata:
 *   rote_version: 0.76.0
 *   version: 1.2.0
 *   status: released
 *   execution_model: steps_with_presentation
 *   flow_type: parallel
 *   requires_endpoints: []
 *   requires_sessions: false
 *   discoverability:
 *     tags:
 *     - domain-devtools
 *     - job-git-cleanup
 *     - audience-developers
 *     - effect-gated-write
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: repo_path
 *   type: string
 *   required: false
 *   default: .
 *   description: Path to the git repository
 *   example: .
 * - name: apply
 *   type: string
 *   required: false
 *   default: 'false'
 *   description: 'Set true to prune merged branches (default: dry-run)'
 *   example: 'false'
 * steps:
 *   scan_branches:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_branches.py}'
 *     - $repo_path
 *   scan_merged:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_merged.py}'
 *     - $repo_path
 *   scan_worktrees:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_worktrees.py}'
 *     - $repo_path
 *   analyze_hygiene:
 *     type: process.exec
 *     depends_on:
 *     - scan_branches
 *     - scan_merged
 *     - scan_worktrees
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{analyze_hygiene.py}'
 *     - '@scan_branches{$.stdout.text}'
 *     - '@scan_merged{$.stdout.text}'
 *     - '@scan_worktrees{$.stdout.text}'
 *   apply_prune:
 *     type: process.exec
 *     depends_on:
 *     - analyze_hygiene
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{apply_prune.py}'
 *     - $apply
 *     - $repo_path
 *     - '@analyze_hygiene{$.stdout.text | fromjson | .merged_unpruned}'
 * presentation_fixtures:
 *   scan_branches: resources/presentation-fixtures/scan_branches/fixture.yaml
 *   scan_merged: resources/presentation-fixtures/scan_merged/fixture.yaml
 *   scan_worktrees: resources/presentation-fixtures/scan_worktrees/fixture.yaml
 *   analyze_hygiene: resources/presentation-fixtures/analyze_hygiene/fixture.yaml
 *   apply_prune: resources/presentation-fixtures/apply_prune/fixture.yaml
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
const scanBranches = ctx.step(stepName("scan_branches"));
const scanMerged = ctx.step(stepName("scan_merged"));
const scanWorktrees = ctx.step(stepName("scan_worktrees"));
const analyzeHygiene = ctx.step(stepName("analyze_hygiene"));
const applyPrune = ctx.step(stepName("apply_prune"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "scan_branches", step: scanBranches },
  { name: "scan_merged", step: scanMerged },
  { name: "scan_worktrees", step: scanWorktrees },
  { name: "analyze_hygiene", step: analyzeHygiene },
  { name: "apply_prune", step: applyPrune },
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

// Parse the analysis from analyze_hygiene step
let branchesTotal = 0;
let stale: unknown[] = [];
let merged: string[] = [];
let worktrees: unknown[] = [];
let unpushed: unknown[] = [];
let pruned: string[] = [];
let apply = "false";
let error: string | null = null;

try {
  const outcome = analyzeHygiene.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        branchesTotal = Number(parsed.branches_total ?? 0);
        stale = (parsed.stale_branches as unknown[]) ?? [];
        merged = (parsed.merged_unpruned as string[]) ?? [];
        worktrees = (parsed.worktrees as unknown[]) ?? [];
        unpushed = (parsed.unpushed as unknown[]) ?? [];
      }
    } else {
      error = "analyze_hygiene produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "analyze_hygiene failed");
  } else {
    error = `analyze_hygiene status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse analysis: ${e.message}`;
}

// Parse prune result
try {
  const outcome = applyPrune.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      pruned = (parsed.pruned as string[]) ?? [];
      apply = String(parsed.applied != null && parsed.applied ? "true" : "false");
    }
  }
} catch {
  // apply_prune is optional-degrade
}

out.human(buildHuman(branchesTotal, stale, merged, worktrees, unpushed, pruned, apply, error, ledger));
out.summary(`git-hygiene — ${branchesTotal} branches · ${stale.length} stale · ${merged.length} merged-unpruned · apply=${apply}`);
out.result({
  branches_total: branchesTotal,
  stale_branches: stale,
  merged_unpruned: merged,
  worktrees,
  unpushed,
  pruned,
  apply,
  ledger,
});

function buildHuman(
  total: number,
  stale: unknown[],
  merged: string[],
  worktrees: unknown[],
  unpushed: unknown[],
  pruned: string[],
  apply: string,
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `git-hygiene — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push(`GIT HYGIENE — ${total} branches audited`);
  lines.push("");

  // Stage ledger
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
  lines.push("");

  if (stale.length > 0) {
    lines.push(`Stale branches (${stale.length}):`);
    for (const s of stale) {
      const b = s as Record<string, unknown>;
      lines.push(`  - ${b.name} (${b.last_commit}) — ${b.reason}`);
    }
    lines.push("");
  }

  if (merged.length > 0) {
    lines.push(`Merged but unpruned (${merged.length}):`);
    for (const name of merged) {
      lines.push(`  - ${name}`);
    }
    lines.push("");
  }

  if (unpushed.length > 0) {
    lines.push(`Unpushed work (${unpushed.length}):`);
    for (const u of unpushed) {
      const up = u as Record<string, unknown>;
      lines.push(`  - ${up.branch}: ${up.ahead} ahead`);
    }
    lines.push("");
  }

  if (worktrees.length > 1) {
    lines.push(`Worktrees (${worktrees.length}):`);
    for (const w of worktrees) {
      const wt = w as Record<string, unknown>;
      lines.push(`  - ${wt.path} (${wt.branch ?? wt.detached ?? "detached"})`);
    }
    lines.push("");
  }

  if (pruned.length > 0) {
    lines.push(`Pruned (${pruned.length}): ${pruned.join(", ")}`);
    lines.push("");
  }

  // Gated-write status
  if (apply === "true") {
    lines.push("**apply=true** — branches pruned");
  } else {
    lines.push("**apply=false (dry run)** — no changes made. Set `apply=true` to prune.");
  }

  return lines.join("\n");
}
