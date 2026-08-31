/**
 * @rote-frontmatter
 * ---
 * name: git-hygiene
 * version: "0.1.0"
 * description: >
 *   The cleanup nobody wants by hand. Audits a git repo for stale branches,
 *   unpushed work, dirty worktrees, merged-but-not-pruned branches — one sweep
 *   with a safe --prune mode behind the same apply=true gate. Read-only by
 *   default; writes only on explicit opt-in.
 * provenance:
 *   author: playbookacademy
 *   workspace: git-hygiene
 * metadata:
 *   rote_version: 0.75.0
 *   version: 0.1.0
 *   status: released
 *   execution_model: steps_with_presentation
 *   flow_type: sequential
 *   requires_endpoints: []
 *   requires_sessions: false
 *   discoverability:
 *     tags:
 *     - domain-devtools
 *     - job-git-cleanup
 *     - audience-developers
 *     - effect-gated-write
 * parameters:
 *   - name: repo_path
 *     type: string
 *     required: false
 *     default: "."
 *     description: "Path to the git repository (default: current directory)"
 *   - name: apply
 *     type: string
 *     required: false
 *     default: "false"
 *     description: "Set true to prune merged branches (default: dry-run report)"
 * steps:
 *   audit:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - "@resource{hygiene.py}"
 *     - $repo_path
 *     - $apply
 * ---
 */

import {
  loadPresentationContext,
  stepName,
  FlowOutput,
} from "__ROTE_PRESENTATION_SDK__";

const out = new FlowOutput();
const ctx = await loadPresentationContext();
const audit = ctx.step(stepName("audit"));

let branchesTotal = 0;
let stale: unknown[] = [];
let merged: string[] = [];
let worktrees: unknown[] = [];
let unpushed: unknown[] = [];
let pruned: string[] = [];
let apply = "false";
let receipt = "";
let error: string | null = null;

try {
  const outcome = audit.outcome;
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
        pruned = (parsed.pruned as string[]) ?? [];
        apply = String(parsed.apply ?? "false");
        receipt = String(parsed.receipt ?? "");
      }
    } else {
      error = "Step produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "Step failed");
  } else {
    error = `Step status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse audit output: ${e.message}`;
}

out.human(buildHuman(branchesTotal, stale, merged, worktrees, unpushed, pruned, apply, receipt, error));
out.summary(receipt || `git-hygiene — ${branchesTotal} branches audited`);
out.result({ branches_total: branchesTotal, stale_branches: stale, merged_unpruned: merged, worktrees, unpushed, pruned, apply });

function buildHuman(
  total: number,
  stale: unknown[],
  merged: string[],
  worktrees: unknown[],
  unpushed: unknown[],
  pruned: string[],
  apply: string,
  receipt: string,
  error: string | null,
): string {
  if (error) {
    return `git-hygiene — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push(`GIT HYGIENE — ${total} branches audited`);
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
  }

  lines.push("---");
  if (apply === "true") {
    lines.push("**apply=true** — branches pruned");
  } else {
    lines.push("**apply=false (dry run)** — no changes made. Set `apply=true` to prune.");
  }

  return lines.join("\n");
}
