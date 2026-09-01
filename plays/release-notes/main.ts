/**
 * @rote-frontmatter
 * ---
 * name: release-notes
 * version: 1.0.0
 * description: |
 *   Ship notes without the guilt. From a git range (two tags/SHAs), compose a categorized changelog draft: commits classified feat/fix/perf/chore/breaking, enriched with authors, rendered as markdown ready to paste — and optionally opened as a draft GitHub release, gated behind apply=true. Demonstrates the authority-boundary pattern: dry-run by default, mutation only on explicit opt-in.
 * provenance:
 *   author: playbookacademy
 *   workspace: release-notes
 * metadata:
 *   rote_version: 0.76.0
 *   version: 1.1.0
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
 * - name: from_ref
 *   type: string
 *   required: false
 *   default: HEAD~10
 *   description: 'Start of range (tag, SHA, or ref). Default: HEAD~10'
 * - name: to_ref
 *   type: string
 *   required: false
 *   default: HEAD
 *   description: 'End of range (tag, SHA, or ref). Default: HEAD'
 * - name: apply
 *   type: string
 *   required: false
 *   default: 'false'
 *   description: 'Set true to create the release (default: dry-run)'
 * - name: repo_path
 *   type: string
 *   required: false
 *   default: .
 *   description: 'Path to the git repository (default: current directory)'
 * steps:
 *   fetch_commits:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{fetch_commits.py}'
 *     - $from_ref
 *     - $to_ref
 *     - $repo_path
 *   classify_commits:
 *     type: process.exec
 *     depends_on:
 *     - fetch_commits
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{classify_commits.py}'
 *     - '@fetch_commits{$.stdout.text}'
 *   build_changelog:
 *     type: process.exec
 *     depends_on:
 *     - classify_commits
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{build_changelog.py}'
 *     - '@classify_commits{$.stdout.text}'
 *   apply_release:
 *     type: process.exec
 *     depends_on:
 *     - build_changelog
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{apply_release.py}'
 *     - $apply
 *     - $from_ref
 *     - $to_ref
 *     - $repo_path
 * presentation_fixtures:
 *   fetch_commits: resources/presentation-fixtures/fetch_commits/fixture.yaml
 *   classify_commits: resources/presentation-fixtures/classify_commits/fixture.yaml
 *   build_changelog: resources/presentation-fixtures/build_changelog/fixture.yaml
 *   apply_release: resources/presentation-fixtures/apply_release/fixture.yaml
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
const fetchCommits = ctx.step(stepName("fetch_commits"));
const classifyCommits = ctx.step(stepName("classify_commits"));
const buildChangelog = ctx.step(stepName("build_changelog"));
const applyRelease = ctx.step(stepName("apply_release"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "fetch_commits", step: fetchCommits },
  { name: "classify_commits", step: classifyCommits },
  { name: "build_changelog", step: buildChangelog },
  { name: "apply_release", step: applyRelease },
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

// Parse the changelog from build_changelog step
let changelogMd = "";
let total = 0;
let categories: string[] = [];
let fromRef = "";
let toRef = "";
let apply = "false";
let releaseResult: Record<string, unknown> | null = null;
let error: string | null = null;

try {
  const outcome = buildChangelog.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        changelogMd = String(parsed.markdown ?? "");
        total = Number(parsed.total ?? 0);
        categories = (parsed.categories as string[]) ?? [];
      }
    } else {
      error = "build_changelog produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "build_changelog failed");
  } else {
    error = `build_changelog status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse changelog: ${e.message}`;
}

// Parse apply result
try {
  const outcome = applyRelease.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      releaseResult = parsed;
      apply = String(parsed.applied != null && parsed.applied ? "true" : "false");
    }
  }
} catch {
  // apply_release is optional-degrade
}

fromRef = String(ctx.params?.from_ref ?? "HEAD~10");
toRef = String(ctx.params?.to_ref ?? "HEAD");

out.human(buildHuman(changelogMd, total, categories, fromRef, toRef, apply, releaseResult, error, ledger));
out.summary(`release-notes — ${fromRef}→${toRef} · ${total} commits · apply=${apply}`);
out.result({
  changelog_md: changelogMd,
  total,
  categories,
  from: fromRef,
  to: toRef,
  apply,
  release_result: releaseResult,
  ledger,
});

function buildHuman(
  md: string,
  total: number,
  categories: string[],
  fromRef: string,
  toRef: string,
  apply: string,
  releaseResult: Record<string, unknown> | null,
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `release-notes — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push(`## Changelog: ${fromRef} → ${toRef}`);
  lines.push("");
  lines.push(md);

  // Stage ledger
  lines.push("");
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
  lines.push("");

  // Gated-write status
  if (apply === "true") {
    lines.push("**apply=true** — release creation requested");
    if (releaseResult) {
      const note = releaseResult.get("note");
      if (note) lines.push(`  note: ${note}`);
    }
  } else {
    lines.push("**apply=false (dry run)** — no changes made. Set `apply=true` to create the release.");
  }

  return lines.join("\n");
}
