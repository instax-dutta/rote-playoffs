/**
 * @rote-frontmatter
 * ---
 * name: model-price-scout
 * version: "0.1.0"
 * description: >
 *   Cheapest capable model, right now. Fetches live pricing from LiteLLM's
 *   public model catalog, ranks cheapest-per-M-input-token by capability tier
 *   (flagship / mid / fast / embedding), flags context-window tradeoffs, and
 *   prints a decision table. Read-only, no credentials, no auth. Complements
 *   (does not replace) modiqo/hello, which surfaces pricing as one of nine
 *   subsystems — this is a dedicated, opinionated price scout.
 * provenance:
 *   author: playbookacademy
 *   workspace: model-price-scout
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
 *     - domain-ai-ml
 *     - job-model-selection
 *     - audience-developers
 *     - effect-read-only
 * parameters:
 *   - name: tier
 *     type: string
 *     required: false
 *     default: auto
 *     description: "Capability tier filter — flagship, mid, fast, embedding, or auto (all)"
 *   - name: providers
 *     type: string
 *     required: false
 *     default: all
 *     description: "Optional provider filter — comma-separated (openai,anthropic,google,bedrock), or all"
 *   - name: max_results
 *     type: integer
 *     required: false
 *     default: 10
 *     description: "Maximum rows in the decision table"
 *   - name: budget_per_mtok
 *     type: number
 *     required: false
 *     default: 0
 *     description: "Optional budget ceiling per M input tokens (0 = no ceiling)"
 * steps:
 *   fetch_and_classify:
 *     type: process.exec
 *     timeout_ms: 60000
 *     argv:
 *     - python3
 *     - "@resource{classify_and_rank.py}"
 *     - $tier
 *     - $providers
 *     - $max_results
 *     - $budget_per_mtok
 * ---
 */

import {
  loadPresentationContext,
  stepName,
  FlowOutput,
} from "__ROTE_PRESENTATION_SDK__";

const out = new FlowOutput();
const ctx = await loadPresentationContext();
const classify = ctx.step(stepName("fetch_and_classify"));

// The classify step emits JSON to stdout; parse it for the structured result.
let table: unknown = null;
let meta: Record<string, unknown> = {};
let error: string | null = null;

try {
  const outcome = classify.outcome;
  if (outcome.status === "completed" || outcome.status === "restored") {
    const body = outcome.output?.body as Record<string, unknown> | undefined;
    const stdout = (body?.stdout as Record<string, unknown> | undefined)?.text;
    if (typeof stdout === "string" && stdout.trim()) {
      const parsed = JSON.parse(stdout);
      if (parsed && typeof parsed === "object" && "error" in parsed) {
        error = String(parsed.error);
      } else if (parsed && typeof parsed === "object" && "table" in parsed) {
        table = parsed.table;
        meta = (parsed.meta as Record<string, unknown>) ?? {};
      } else {
        table = parsed;
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
  error = `Failed to parse classify output: ${e.message}`;
}

const tier = String(ctx.params?.tier ?? "auto");
const providers = String(ctx.params?.providers ?? "all");
const maxResults = Number(ctx.params?.max_results ?? 10);
const budget = Number(ctx.params?.budget_per_mtok ?? 0);

out.human(buildHuman(table, meta, error, tier, providers, maxResults, budget));
out.summary(
  typeof meta?.count === "number"
    ? `${meta.count} models ranked · tier=${tier} · providers=${providers}`
    : "Model price scout complete",
);
out.result({
  table,
  meta,
  error,
  params: { tier, providers, max_results: maxResults, budget_per_mtok: budget },
});

function buildHuman(
  table: unknown,
  meta: Record<string, unknown>,
  error: string | null,
  tier: string,
  providers: string,
  maxResults: number,
  budget: number,
): string {
  if (error) {
    return `model-price-scout — ERROR: ${error}`;
  }
  if (!table || !Array.isArray(table) || table.length === 0) {
    return `model-price-scout — no models matched (tier=${tier}, providers=${providers}, budget=${budget}/Mtok)`;
  }

  const lines: string[] = [];
  lines.push(`MODEL PRICE SCOUT — ${String(meta?.count ?? table.length)} models ranked`);
  lines.push(`tier: ${tier} · providers: ${providers} · budget: ${budget > 0 ? `$${budget}/Mtok` : "none"}`);
  lines.push("");

  // Header
  lines.push(
    `${"rank".padEnd(5)} ${"model".padEnd(42)} ${"provider".padEnd(12)} ${"in$/Mtok".padEnd(10)} ${"out$/Mtok".padEnd(10)} ${"ctx".padEnd(8)} ${"note"}`,
  );
  lines.push("─".repeat(110));

  for (let i = 0; i < table.length; i++) {
    const row = table[i] as Record<string, unknown>;
    const rank = String(i + 1).padEnd(5);
    const model = String(row.model ?? "?").slice(0, 42).padEnd(42);
    const provider = String(row.provider ?? "?").slice(0, 12).padEnd(12);
    const inp = `$${String(row.input_cost_per_token ?? "?")}`.padEnd(10);
    const out = `$${String(row.output_cost_per_token ?? "?")}`.padEnd(10);
    const ctx = String(row.context_window ?? "?").padEnd(8);
    const note = String(row.note ?? "");
    lines.push(`${rank} ${model} ${provider} ${inp} ${out} ${ctx} ${note}`);
  }

  return lines.join("\n");
}
