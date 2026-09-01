/**
 * @rote-frontmatter
 * ---
 * name: model-price-scout
 * version: 1.0.0
 * description: |
 *   Cheapest capable model, right now. Fetches live pricing from LiteLLM's public model catalog, classifies by capability tier, filters by your criteria, ranks cheapest-per-M-input-token, and prints a decision table. Read-only, no credentials, no auth. Complements (does not replace) modiqo/hello, which surfaces pricing as one of nine subsystems.
 * provenance:
 *   author: playbookacademy
 *   workspace: model-price-scout
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
 *     - domain-ai-ml
 *     - job-model-selection
 *     - audience-developers
 *     - effect-read-only
 * parameters:
 * - name: tier
 *   type: string
 *   required: false
 *   default: auto
 *   description: Capability tier filter — flagship, mid, fast, embedding, or auto (all)
 * - name: providers
 *   type: string
 *   required: false
 *   default: all
 *   description: Optional provider filter — comma-separated (openai,anthropic,google,bedrock), or all
 * - name: max_results
 *   type: integer
 *   required: false
 *   default: 10
 *   description: Maximum rows in the decision table
 * - name: budget_per_mtok
 *   type: number
 *   required: false
 *   default: 0
 *   description: Optional budget ceiling per M input tokens (0 = no ceiling)
 * steps:
 *   fetch_catalog:
 *     type: process.exec
 *     timeout_ms: 60000
 *     argv:
 *     - python3
 *     - '@resource{fetch_catalog.py}'
 *   classify_models:
 *     type: process.exec
 *     depends_on:
 *     - fetch_catalog
 *     timeout_ms: 30000
 *     argv:
 *     - python3
 *     - '@resource{classify_models.py}'
 *     - '@fetch_catalog{$.stdout.text | fromjson | .file}'
 *   filter_models:
 *     type: process.exec
 *     depends_on:
 *     - classify_models
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{filter_models.py}'
 *     - '@classify_models{$.stdout.text | fromjson | .file}'
 *     - $tier
 *     - $providers
 *     - $budget_per_mtok
 *   rank_and_format:
 *     type: process.exec
 *     depends_on:
 *     - filter_models
 *     timeout_ms: 15000
 *     argv:
 *     - python3
 *     - '@resource{rank_and_format.py}'
 *     - '@filter_models{$.stdout.text | fromjson | .file}'
 *     - $max_results
 * presentation_fixtures:
 *   fetch_catalog: resources/presentation-fixtures/fetch_catalog/fixture.yaml
 *   classify_models: resources/presentation-fixtures/classify_models/fixture.yaml
 *   filter_models: resources/presentation-fixtures/filter_models/fixture.yaml
 *   rank_and_format: resources/presentation-fixtures/rank_and_format/fixture.yaml
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
const fetchCatalog = ctx.step(stepName("fetch_catalog"));
const classifyModels = ctx.step(stepName("classify_models"));
const filterModels = ctx.step(stepName("filter_models"));
const rankAndFormat = ctx.step(stepName("rank_and_format"));

// Stage ledger
const ledger: Record<string, string> = {};
const stepStates = [
  { name: "fetch_catalog", step: fetchCatalog },
  { name: "classify_models", step: classifyModels },
  { name: "filter_models", step: filterModels },
  { name: "rank_and_format", step: rankAndFormat },
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

// Parse the final output from rank_and_format step
let table: unknown = null;
let meta: Record<string, unknown> = {};
let error: string | null = null;

try {
  const outcome = rankAndFormat.outcome;
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
      error = "rank_and_format produced no output";
    }
  } else if (outcome.status === "failed") {
    error = String(outcome.error ?? "rank_and_format failed");
  } else {
    error = `rank_and_format status: ${outcome.status}`;
  }
} catch (e: any) {
  error = `Failed to parse output: ${e.message}`;
}

const tier = String(ctx.params?.tier ?? "auto");
const providers = String(ctx.params?.providers ?? "all");
const maxResults = Number(ctx.params?.max_results ?? 10);
const budget = Number(ctx.params?.budget_per_mtok ?? 0);

out.human(buildHuman(table, meta, error, tier, providers, maxResults, budget, ledger));
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
  ledger,
});

function buildHuman(
  table: unknown,
  meta: Record<string, unknown>,
  error: string | null,
  tier: string,
  providers: string,
  maxResults: number,
  budget: number,
  ledger: Record<string, string>,
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

  // Stage ledger
  lines.push("Stage Ledger:");
  for (const [name, state] of Object.entries(ledger)) {
    const marker = state === "ok" ? "OK" : state === "degraded" ? "DEG" : state.toUpperCase();
    lines.push(`  ${name}: ${marker}`);
  }
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
