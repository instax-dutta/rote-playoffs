/**
 * @rote-frontmatter
 * ---
 * name: pkg-vet
 * version: "0.1.0"
 * description: >
 *   Vet npm/PyPI/crates packages BEFORE installing: OSV advisories, typosquat
 *   distance, maintainer and repo signals, download trends, license flags.
 *   Read-only, no credentials. Complements (does not replace) installed-lockfile
 *   scanners such as modiqo/dependency-vulnerability-check.
 * provenance:
 *   author: playbookacademy
 *   workspace: pkg-vet
 * metadata:
 *   rote_version: 0.75.0
 *   version: 0.1.0
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
 * parameters:
 *   - name: packages
 *     type: string
 *     required: true
 *     description: "Comma-separated package names to vet, e.g. zod,left-pad,react"
 *   - name: ecosystems
 *     type: string
 *     required: false
 *     default: auto
 *     description: "Comma-separated ecosystems (npm,pypi,cargo), or auto-detect"
 * steps:
 *   vet_all:
 *     type: process.exec
 *     timeout_ms: 90000
 *     argv:
 *     - python3
 *     - "@resource{vet.py}"
 *     - $packages
 *     - $ecosystems
 * ---
 */

import {
  loadPresentationContext,
  stepName,
  FlowOutput,
} from "__ROTE_PRESENTATION_SDK__";

const out = new FlowOutput();
const ctx = await loadPresentationContext();
const vetStep = ctx.step(stepName("vet_all"));

let verdict: string = "UNKNOWN";
let packages: unknown[] = [];
let sourcesOk = 0;
let sourcesTotal = 0;
let receipt = "";
let error: string | null = null;

try {
  const outcome = vetStep.outcome;
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
      error = "Step produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "Step failed");
  } else {
    error = `Step status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse vet output: ${e.message}`;
}

out.human(buildHuman(verdict, packages, sourcesOk, sourcesTotal, receipt, error));
out.summary(receipt || `pkg-vet — ${verdict}`);
out.result({ verdict, packages, sources_ok: sourcesOk, sources_total: sourcesTotal });

function buildHuman(
  verdict: string,
  packages: unknown[],
  sourcesOk: number,
  sourcesTotal: number,
  receipt: string,
  error: string | null,
): string {
  if (error) {
    return `pkg-vet — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push(`PKG VET — Verdict: ${verdict}`);
  lines.push(`sources: ${sourcesOk}/${sourcesTotal} ok`);
  lines.push("");

  for (const pkg of packages) {
    const p = pkg as Record<string, unknown>;
    const pkgVerdict = String(p.verdict ?? "?");
    const pkgName = String(p.package ?? "?");
    const eco = String(p.ecosystem ?? "?");

    // Verdict glyph
    const glyph = pkgVerdict === "SAFE" ? "✓" : pkgVerdict === "CAUTION" ? "!" : "✗";
    lines.push(`  ${glyph} ${pkgName} (${eco}) — ${pkgVerdict}`);

    // Signals
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
