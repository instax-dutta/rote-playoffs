/**
 * @rote-frontmatter
 * ---
 * name: token-audit
 * version: 1.0.0
 * description: |
 *   AI Prompt & Token Budget Auditor. Scans a directory for prompt files, estimates token counts, flags bloat (>4k tokens), and projects monthly API costs across models (GPT-4o, Claude 3.5 Sonnet, etc.). Read-only, no credentials, no auth.
 * provenance:
 *   author: playbookacademy
 *   workspace: token-audit
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
 *     - domain-ai-ml
 *     - job-token-audit
 *     - audience-developers
 *     - effect-read-only
 *     - multi-step-dag
 *     - value-edges
 * parameters:
 * - name: dir
 *   type: string
 *   required: false
 *   default: .
 *   description: Directory to scan for prompt files
 *   example: .
 * - name: max_files
 *   type: integer
 *   required: false
 *   default: 100
 *   description: Maximum files to scan
 *   example: '100'
 * - name: runs_per_day
 *   type: integer
 *   required: false
 *   default: 1000
 *   description: Estimated daily invocations for cost projection
 *   example: '1000'
 * steps:
 *   scan_prompts:
 *     type: process.exec
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{scan_prompts.py}'
 *     - $dir
 *     - $max_files
 *   count_tokens:
 *     type: process.exec
 *     depends_on:
 *     - scan_prompts
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{count_tokens.py}'
 *     - '@scan_prompts{$.stdout.text}'
 *   analyze_budget:
 *     type: process.exec
 *     depends_on:
 *     - count_tokens
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{analyze_budget.py}'
 *     - '@count_tokens{$.stdout.text}'
 *     - $runs_per_day
 *   generate_report:
 *     type: process.exec
 *     depends_on:
 *     - analyze_budget
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{generate_report.py}'
 *     - '@analyze_budget{$.stdout.text}'
 * presentation_fixtures:
 *   scan_prompts: resources/presentation-fixtures/scan_prompts/fixture.yaml
 *   count_tokens: resources/presentation-fixtures/count_tokens/fixture.yaml
 *   analyze_budget: resources/presentation-fixtures/analyze_budget/fixture.yaml
 *   generate_report: resources/presentation-fixtures/generate_report/fixture.yaml
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
const scanPrompts = ctx.step(stepName("scan_prompts"));
const countTokens = ctx.step(stepName("count_tokens"));
const analyzeBudget = ctx.step(stepName("analyze_budget"));
const generateReport = ctx.step(stepName("generate_report"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "scan_prompts", step: scanPrompts },
  { name: "count_tokens", step: countTokens },
  { name: "analyze_budget", step: analyzeBudget },
  { name: "generate_report", step: generateReport },
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

// Parse the report from generate_report step
let totalFiles = 0;
let totalTokens = 0;
let bloatCount = 0;
let dailyCostEstimate: Record<string, number> = {};
let largestFiles: unknown[] = [];
let warnings: string[] = [];
let receipt = "";
let error: string | null = null;

try {
  const outcome = generateReport.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object") {
        totalFiles = Number(parsed.total_files ?? 0);
        totalTokens = Number(parsed.total_tokens ?? 0);
        bloatCount = Number(parsed.bloat_count ?? 0);
        dailyCostEstimate = (parsed.daily_cost_estimate as Record<string, number>) ?? {};
        largestFiles = (parsed.largest_files as unknown[]) ?? [];
        warnings = (parsed.warnings as string[]) ?? [];
        receipt = String(parsed.receipt ?? "");
      }
    } else {
      error = "generate_report produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "generate_report failed");
  } else {
    error = `generate_report status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse report: ${e.message}`;
}

out.human(buildHuman(totalFiles, totalTokens, bloatCount, dailyCostEstimate, largestFiles, warnings, error, ledger));
out.summary(receipt || `token-audit — ${totalFiles} files · ${totalTokens} tokens`);
out.result({
  total_files: totalFiles,
  total_tokens: totalTokens,
  bloat_count: bloatCount,
  daily_cost_estimate: dailyCostEstimate,
  largest_files: largestFiles,
  warnings,
  ledger,
});

function buildHuman(
  totalFiles: number,
  totalTokens: number,
  bloatCount: number,
  dailyCost: Record<string, number>,
  largestFiles: unknown[],
  warnings: string[],
  error: string | null,
  ledger: Record<string, string>,
): string {
  if (error) {
    return `token-audit — ERROR: ${error}`;
  }

  const lines: string[] = [];
  lines.push("TOKEN AUDIT");
  lines.push(`${totalFiles} files · ${totalTokens} tokens · ${bloatCount} bloated`);
  lines.push("");

  // Stage ledger
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
  lines.push("");

  // Largest files
  if (largestFiles.length > 0) {
    lines.push("Largest Files:");
    for (const f of largestFiles) {
      const file = f as Record<string, unknown>;
      lines.push(`  ${file.path} (${file.tokens} tokens)`);
    }
    lines.push("");
  }

  // Cost estimates
  if (Object.keys(dailyCost).length > 0) {
    lines.push("Daily Cost Estimate (1000 runs):");
    for (const [model, cost] of Object.entries(dailyCost)) {
      lines.push(`  ${model}: $${cost}/day`);
    }
    lines.push("");
  }

  // Warnings
  if (warnings.length > 0) {
    lines.push("Warnings:");
    for (const w of warnings) {
      lines.push(`  ! ${w}`);
    }
  }

  return lines.join("\n");
}
