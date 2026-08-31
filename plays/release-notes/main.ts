/**
 * @rote-frontmatter
 * ---
 * name: release-notes
 * version: "0.1.0"
 * description: >
 *   Ship notes without the guilt. From a git range (two tags/SHAs), compose a
 *   categorized changelog draft: commits classified feat/fix/perf/chore/breaking,
 *   enriched with authors, rendered as markdown ready to paste — and optionally
 *   opened as a draft GitHub release, gated behind apply=true. Demonstrates the
 *   authority-boundary pattern: dry-run by default, mutation only on explicit opt-in.
 * provenance:
 *   author: playbookacademy
 *   workspace: release-notes
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
 *     - job-release-notes
 *     - audience-developers
 *     - effect-gated-write
 * parameters:
 *   - name: from_ref
 *     type: string
 *     required: false
 *     default: HEAD~10
 *     description: "Start of range (tag, SHA, or ref). Default: HEAD~10"
 *   - name: to_ref
 *     type: string
 *     required: false
 *     default: HEAD
 *     description: "End of range (tag, SHA, or ref). Default: HEAD"
 *   - name: apply
 *     type: string
 *     required: false
 *     default: "false"
 *     description: "Set true to create the release (default: dry-run)"
 *   - name: repo_path
 *     type: string
 *     required: false
 *     default: "."
 *     description: "Path to the git repository (default: current directory)"
 * steps:
 *   compose:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - "@resource{changelog.py}"
 *     - $from_ref
 *     - $to_ref
 *     - $apply
 *     - $repo_path
 * ---
 */

import {
  loadPresentationContext,
  stepName,
  FlowOutput,
} from "__ROTE_PRESENTATION_SDK__";

const out = new FlowOutput();
const ctx = await loadPresentationContext();
const compose = ctx.step(stepName("compose"));

let changelogMd = "";
let total = 0;
let categories: string[] = [];
let fromRef = "";
let toRef = "";
let apply = "false";
let receipt = "";
let error: string | null = null;

try {
  const outcome = compose.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        const cl = parsed.changelog as Record<string, unknown> | undefined;
        changelogMd = String(cl?.markdown ?? "");
        total = Number(cl?.total ?? 0);
        categories = (cl?.categories as string[]) ?? [];
        fromRef = String(parsed.from ?? "");
        toRef = String(parsed.to ?? "");
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
  error = `Failed to parse compose output: ${e.message}`;
}

out.human(buildHuman(changelogMd, total, categories, fromRef, toRef, apply, receipt, error));
out.summary(receipt || `release-notes — ${total} commits`);
out.result({ changelog_md: changelogMd, total, categories, from: fromRef, to: toRef, apply });

function buildHuman(
  md: string,
  total: number,
  categories: string[],
  fromRef: string,
  toRef: string,
  apply: string,
  receipt: string,
  error: string | null,
): string {
  if (error) {
    return `release-notes — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push(md);

  // Footer with gated-write status
  lines.push("");
  lines.push("---");
  if (apply === "true") {
    lines.push("**apply=true** — release creation requested");
  } else {
    lines.push("**apply=false (dry run)** — no changes made. Set `apply=true` to create the release.");
  }

  return lines.join("\n");
}
