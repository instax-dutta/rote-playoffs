# model-price-scout

## Purpose

LiteLLM pricing scout — given a capability tier (flagship/mid/fast/embedding) and optional provider filter, fetch live pricing from LiteLLM's public model catalog, rank cheapest-per-M-token, flag context-window tradeoffs, print a decision table.

**Target prize:** iPhone 17 (3rd) — "Turns one expert run into useful work others can carry"

## Ownership

- Author: playbookacademy
- Canonical URI: https://play.modiqo.ai/playbookacademy/model-price-scout@0.1.0
- Registry: public, released

## Local Contracts

- Entrypoint: `main.ts` (rote frontmatter DAG + TypeScript presentation)
- Resource: `resources/classify_and_rank.py` (inline Python, self-contained)
- Dependencies: `deps.toml` declares python3 >= 3.10
- No adapters, no auth, no browser — pure process.exec + public HTTPS

## Work Guidance

- Frontmatter format: `/** @rote-frontmatter` then ` * ---` then YAML then ` * ---` then `*/` (BOTH fences required)
- metadata MUST include: rote_version, version, status, execution_model, flow_type, requires_endpoints, requires_sessions
- Resource files go under `resources/`, referenced as `@resource{filename}` in argv
- Step output accessed via: `step.outcome.output.body.stdout.text` (NOT step.stdout.text)
- Presentation body uses top-level await (NOT export default function)
- FlowOutput pattern: `const out = new FlowOutput()` then `out.human(str)`, `out.summary(str)`, `out.result(obj)` — do NOT return
- Step access: `ctx.step(stepName("step_name"))` then check `outcome.status`
- No f-strings in TypeScript presentation body (Deno runtime limitation)
- Lint gate: `rote play lint <name>` then `rote play release <name>` then `rote registry play push <path> playbookacademy`
- deps.toml format: `schema_version = 1` then `[[tools]]` with id/command/required/version_requirement, then `[[tools.install]]` with manager/package

## Verification

- `rote play lint model-price-scout` must pass before release
- `rote play run "https://play.modiqo.ai/playbookacademy/model-price-scout@0.1.0" tier=flagship max_results=5 --yes` must produce a decision table
- Cold-pull rehearsal: run from a pristine directory with zero flags
- Every version bump must be a semver bump (immutable versions)

## Child DOX Index

No child docs needed — flat structure (main.ts + resources/).
