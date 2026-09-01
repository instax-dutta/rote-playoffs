/**
 * @rote-frontmatter
 * ---
 * name: pkg-vet
 * version: 1.1.0
 * description: |
 *   Vet npm/PyPI/crates packages BEFORE installing. Checks OSV advisories, typosquat distance, package age, version count, maintainer signals, and license flags. Returns a deterministic verdict (SAFE / CAUTION / AVOID) with per-source evidence and a stage ledger. Read-only, no credentials. Complements (does not replace) installed-lockfile scanners such as modiqo/dependency-vulnerability-check.
 * provenance:
 *   author: playbookacademy
 *   workspace: pkg-vet
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
 *     - domain-security
 *     - job-dependency-vetting
 *     - audience-developers
 *     - effect-read-only
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: packages
 *   type: string
 *   required: true
 *   description: Comma-separated package names to vet
 *   example: zod,left-pad,react
 * - name: ecosystems
 *   type: string
 *   required: false
 *   default: auto
 *   description: Comma-separated ecosystems (npm,pypi,cargo), or auto-detect
 *   example: npm,pypi
 * steps:
 *   parse_input:
 *     type: process.exec
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{parse_input.py}'
 *     - $packages
 *     - $ecosystems
 *   fetch_registry:
 *     type: process.exec
 *     depends_on:
 *     - parse_input
 *     timeout_ms: 90000
 *     argv:
 *     - python3
 *     - '@resource{fetch_registry.py}'
 *     - '@parse_input{$.stdout.text}'
 *   check_osv:
 *     type: process.exec
 *     depends_on:
 *     - parse_input
 *     timeout_ms: 60000
 *     argv:
 *     - python3
 *     - '@resource{check_osv.py}'
 *     - '@parse_input{$.stdout.text}'
 *   check_typosquat:
 *     type: process.exec
 *     depends_on:
 *     - parse_input
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{check_typosquat.py}'
 *     - '@parse_input{$.stdout.text}'
 *   compute_verdict:
 *     type: process.exec
 *     depends_on:
 *     - fetch_registry
 *     - check_osv
 *     - check_typosquat
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{compute_verdict.py}'
 *     - '@fetch_registry{$.stdout.text}'
 *     - '@check_osv{$.stdout.text}'
 *     - '@check_typosquat{$.stdout.text}'
 * presentation_fixtures:
 *   parse_input: resources/presentation-fixtures/parse_input/fixture.yaml
 *   fetch_registry: resources/presentation-fixtures/fetch_registry/fixture.yaml
 *   check_osv: resources/presentation-fixtures/check_osv/fixture.yaml
 *   check_typosquat: resources/presentation-fixtures/check_typosquat/fixture.yaml
 *   compute_verdict: resources/presentation-fixtures/compute_verdict/fixture.yaml
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
const parseInput = ctx.step(stepName("parse_input"));
const fetchRegistry = ctx.step(stepName("fetch_registry"));
const checkOsv = ctx.step(stepName("check_osv"));
const checkTyposquat = ctx.step(stepName("check_typosquat"));
const computeVerdict = ctx.step(stepName("compute_verdict"));

// Stage ledger: track which steps completed vs degraded
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "parse_input", step: parseInput },
  { name: "fetch_registry", step: fetchRegistry },
  { name: "check_osv", step: checkOsv },
  { name: "check_typosquat", step: checkTyposquat },
  { name: "compute_verdict", step: computeVerdict },
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

// Parse the final verdict from compute_verdict step
let verdict: string = "UNKNOWN";
let packages: unknown[] = [];
let sourcesOk = 0;
let sourcesTotal = 0;
let receipt = "";
let error: string | null = null;

try {
  const outcome = computeVerdict.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        verdict = String(parsed.verdict ?? "UNKNOWN");
        packages = (parsed.packages as unknown[]) ?? [];
        sourcesOk = Number(parsed.sources_ok ?? 0);
        sourcesTotal = Number(parsed.sources_total ?? 0);
        receipt = String(parsed.receipt ?? "");
      }
    } else {
      error = "compute_verdict produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "compute_verdict failed");
  } else {
    error = `compute_verdict status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse verdict: ${e.message}`;
}

out.human(buildHuman(verdict, packages, sourcesOk, sourcesTotal, receipt, error, ledger));
out.summary(receipt || `pkg-vet — ${verdict}`);
out.result({
  verdict,
  packages,
  sources_ok: sourcesOk,
  sources_total: sourcesTotal,
  ledger,
});

function buildHuman(
  verdict: string,
  packages: unknown[],
  sourcesOk: number,
  sourcesTotal: number,
  receipt: string,
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `pkg-vet — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push(`PKG VET — Verdict: ${verdict}`);
  lines.push(`sources: ${sourcesOk}/${sourcesTotal} ok`);
  lines.push("");

  // Stage ledger
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
  lines.push("");

  for (const pkg of packages) {
    const p = pkg as Record<string, unknown>;
    const pkgVerdict = String(p.verdict ?? "?");
    const pkgName = String(p.package ?? "?");
    const eco = String(p.ecosystem ?? "?");

    const glyph = pkgVerdict === "SAFE" ? "[SAFE]" : pkgVerdict === "CAUTION" ? "[CAUT]" : "[AVOID]";
    lines.push(`  ${glyph} ${pkgName} (${eco})`);

    const signals = (p.signals as unknown[]) ?? [];
    for (const sig of signals) {
      const s = sig as Record<string, unknown>;
      const severity = String(s.severity ?? "?").toUpperCase();
      const detail = String(s.detail ?? "");
      lines.push(`      [${severity}] ${detail}`);
    }
  }

  return lines.join("\n");
}
